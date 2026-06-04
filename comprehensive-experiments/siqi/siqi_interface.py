"""siqi 实验统一接口适配文件。

为上层 GUI 提供"运行测试 / 传参 / 收集结果"的可调用函数，
内部通过 subprocess 调用 pytest 和 locust，避免污染当前进程。

公共 API:
    run_unit(module, *, keyword, product_index)
    run_integration(depth, *, keyword, product_index)
    generate_combinations()
    run_data_combination(*, regenerate)
    run_performance(*, users, spawn_rate, run_time)
    list_test_cases()
    get_default_params()

所有函数同步阻塞返回 TestResult，GUI 应在工作线程中调用。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional, Union

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable  # 使用当前解释器，保证 venv 一致


# ============================================================
# 测试元数据 —— 供 GUI 渲染列表 / 表单
# ============================================================

TEST_CATALOG = {
    "unit": {
        "search": {
            "id": "TC-Search-01",
            "name": "商品搜索单元测试",
            "node": "tests/test_unit_search.py",
            "supports": ["keyword"],
        },
        "product_list": {
            "id": "TC-ProductList-01",
            "name": "商品列表单元测试",
            "node": "tests/test_unit_product_list.py",
            "supports": ["product_index"],
        },
        "product_detail": {
            "id": "TC-ProductDetail-01",
            "name": "商品详情单元测试",
            "node": "tests/test_unit_product_detail.py",
            "supports": [],
        },
    },
    "integration": {
        3: {
            "id": "TC-Integration-Depth3-01",
            "name": "集成深度3：列表→搜索→详情",
            "node": "tests/test_integration_depth3.py",
            "supports": ["keyword", "product_index"],
        },
        4: {
            "id": "TC-Integration-Depth4-01",
            "name": "集成深度4：列表→详情A→回退→详情B",
            "node": "tests/test_integration_depth4.py",
            "supports": ["product_index"],
        },
        5: {
            "id": "TC-Integration-Depth5-01",
            "name": "集成深度5：列表→搜索→详情A→回退→详情B",
            "node": "tests/test_integration_depth5.py",
            "supports": ["keyword", "product_index"],
        },
    },
    "data_combination": {
        "id": "TC-DataCombination",
        "name": "数据组合测试（25 组）",
        "node": "tests/test_data_combination.py",
        "supports": ["regenerate"],
    },
    "performance": {
        "id": "TC-Performance-01",
        "name": "性能测试（Locust）",
        "file": "tests/performance/locustfile.py",
        "supports": ["users", "spawn_rate", "run_time"],
    },
}


# ============================================================
# 统一结果对象
# ============================================================

@dataclass
class TestResult:
    name: str
    success: bool                       # 子进程退出码 == 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_sec: float = 0.0
    report_path: Optional[str] = None   # HTML 报告绝对路径（不存在则为 None）
    raw_output: str = ""                # 完整 stdout+stderr，便于 GUI 展示日志
    extra: dict = field(default_factory=dict)  # 模块特定字段（例如性能指标）

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# 内部辅助
# ============================================================

def _run_subprocess(cmd: list[str], env_extra: Optional[dict] = None) -> tuple[subprocess.CompletedProcess, float]:
    """跑子进程，统一 UTF-8 编码 + 工作目录。

    env_extra：仅注入到这个子进程的额外环境变量（如 SQA_HEADLESS=1），
    不污染当前进程环境。
    """
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if env_extra:
        env.update({k: str(v) for k, v in env_extra.items()})
    start = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return proc, time.time() - start


def _run_pytest(args: list[str], html_report: Optional[Path] = None,
                env_extra: Optional[dict] = None) -> tuple[subprocess.CompletedProcess, float]:
    """组装 pytest 命令并执行。html_report 给定时覆盖 pytest.ini 里的默认报告路径。"""
    cmd = [PYTHON, "-m", "pytest", *args]
    if html_report is not None:
        html_report.parent.mkdir(parents=True, exist_ok=True)
        cmd += [f"--html={html_report}", "--self-contained-html"]
    return _run_subprocess(cmd, env_extra=env_extra)


def _headless_env(headless: bool) -> Optional[dict]:
    """headless=True 时返回给子进程注入的环境变量；否则 None（保持原行为）。"""
    return {"SQA_HEADLESS": "1"} if headless else None


def _parse_pytest_summary(output: str) -> tuple[int, int, int]:
    """从 pytest 末尾汇总行解析 (passed, failed, skipped)。

    例：'======== 4 failed, 21 passed, 6 deselected in 170.94s ========'
    """
    passed = failed = skipped = 0
    # 取最后一行包含 passed/failed/error 的
    for line in reversed(output.splitlines()):
        if any(k in line for k in ("passed", "failed", "error", "no tests ran")):
            for name, pat in [
                ("passed", r"(\d+)\s+passed"),
                ("failed", r"(\d+)\s+failed"),
                ("skipped", r"(\d+)\s+skipped"),
                ("error", r"(\d+)\s+error"),
            ]:
                m = re.search(pat, line)
                if not m:
                    continue
                n = int(m.group(1))
                if name == "passed":
                    passed = n
                elif name == "failed":
                    failed = n
                elif name == "skipped":
                    skipped = n
                elif name == "error":
                    failed += n
            break
    return passed, failed, skipped


def _parse_locust_aggregated(output: str) -> dict:
    """从 Locust 输出中提取 Aggregated 行的关键指标。

    Locust headless 模式会输出 N 个 Aggregated 行：
      - 启动快照：     Aggregated  0  0(0.00%)  ...      ← 全 0，不能用
      - 周期性中间快照：Aggregated  328  23(7.01%)  ...  ← 不完整
      - 最终统计：     Aggregated  1528  67(4.38%)  ...  ← 我们要的
      - 百分位表的：   Aggregated  1900  2000  2100 ...  ← 没有 (X%) 格式，跳过

    解析策略：倒序找到第一个**带 (X.XX%) 失败率格式**的 Aggregated 行，即最终统计行。
    """
    stats: dict = {}
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        if not stripped.startswith("Aggregated"):
            continue
        fr = re.search(r"\(([\d.]+)%\)", stripped)
        if not fr:
            continue  # 跳过 percentiles 表的 Aggregated 行（没有 % 格式）
        stats["aggregated_raw"] = stripped
        nums = re.findall(r"\d+(?:\.\d+)?", stripped)
        if len(nums) >= 2:
            stats["total_requests"] = int(float(nums[0]))
            stats["total_failures"] = int(float(nums[1]))
        stats["failure_rate_percent"] = float(fr.group(1))
        break
    return stats


# ============================================================
# 单元测试
# ============================================================

def run_unit(
    module: str = "all",
    *,
    keyword: Optional[str] = None,
    product_index: Optional[int] = None,
    headless: bool = False,
    **_ignored,
) -> TestResult:
    """运行单元测试。

    Parameters
    ----------
    module: "search" | "product_list" | "product_detail" | "all"
    keyword: 透传给 pytest 的 --keyword；None 用 conftest 默认 ("dress")
    product_index: 透传给 pytest 的 --product-index；None 用 conftest 默认 (0)
    """
    if module == "all":
        args = ["-m", "unit"]
        tag = "all"
    elif module in TEST_CATALOG["unit"]:
        args = [TEST_CATALOG["unit"][module]["node"]]
        tag = module
    else:
        raise ValueError(f"未知的 module='{module}'，可选: search / product_list / product_detail / all")

    if keyword is not None:
        args.append(f"--keyword={keyword}")
    if product_index is not None:
        args.append(f"--product-index={product_index}")

    report = ROOT / "reports" / "html" / f"unit_{tag}.html"
    proc, dur = _run_pytest(args, html_report=report, env_extra=_headless_env(headless))
    p, f, s = _parse_pytest_summary(proc.stdout + proc.stderr)
    return TestResult(
        name=f"单元测试[{tag}]",
        success=(proc.returncode == 0),
        passed=p, failed=f, skipped=s,
        duration_sec=round(dur, 2),
        report_path=str(report) if report.exists() else None,
        raw_output=proc.stdout + proc.stderr,
        extra={"module": module, "keyword": keyword, "product_index": product_index},
    )


# ============================================================
# 集成测试
# ============================================================

def run_integration(
    depth: Union[int, str] = "all",
    *,
    keyword: Optional[str] = None,
    product_index: Optional[int] = None,
    headless: bool = False,
    **_ignored,
) -> TestResult:
    """运行集成测试。

    Parameters
    ----------
    depth: 3 | 4 | 5 | "all"
    """
    if depth == "all":
        args = ["-m", "integration"]
        tag = "all"
    elif depth in (3, 4, 5):
        args = [TEST_CATALOG["integration"][depth]["node"]]
        tag = f"depth{depth}"
    else:
        raise ValueError(f"depth 必须是 3 / 4 / 5 / 'all'，收到 {depth!r}")

    if keyword is not None:
        args.append(f"--keyword={keyword}")
    if product_index is not None:
        args.append(f"--product-index={product_index}")

    report = ROOT / "reports" / "html" / f"integration_{tag}.html"
    proc, dur = _run_pytest(args, html_report=report, env_extra=_headless_env(headless))
    p, f, s = _parse_pytest_summary(proc.stdout + proc.stderr)
    return TestResult(
        name=f"集成测试[{tag}]",
        success=(proc.returncode == 0),
        passed=p, failed=f, skipped=s,
        duration_sec=round(dur, 2),
        report_path=str(report) if report.exists() else None,
        raw_output=proc.stdout + proc.stderr,
        extra={"depth": depth, "keyword": keyword, "product_index": product_index},
    )


# ============================================================
# 数据组合
# ============================================================

def generate_combinations() -> Path:
    """重新生成 testdata/combinations.csv。返回 CSV 绝对路径。"""
    script = ROOT / "scripts" / "generate_combinations.py"
    proc, _ = _run_subprocess([PYTHON, str(script)])
    csv_path = ROOT / "testdata" / "combinations.csv"
    if proc.returncode != 0 or not csv_path.exists():
        raise RuntimeError(
            f"生成组合 CSV 失败 (exit={proc.returncode})\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
    return csv_path


def run_data_combination(*, regenerate: bool = False,
                         select_ids: Optional[list[str]] = None,
                         headless: bool = False, **_ignored) -> TestResult:
    """运行数据组合测试（默认 25 组）。

    Parameters
    ----------
    regenerate: True 时先重新生成 CSV，再跑测试；CSV 不存在时也会自动生成。
    select_ids: 仅跑指定 id 的子集（如 ["DC-01", "DC-02"]）；None 跑全部。
    headless: True 时子进程以 headless 模式跑（demo 用）。
    """
    csv_path = ROOT / "testdata" / "combinations.csv"
    if regenerate or not csv_path.exists():
        generate_combinations()

    args = ["-m", "data_combo"]
    if select_ids:
        args += ["-k", " or ".join(select_ids)]
    report = ROOT / "reports" / "html" / "data_combination.html"
    proc, dur = _run_pytest(args, html_report=report, env_extra=_headless_env(headless))
    p, f, s = _parse_pytest_summary(proc.stdout + proc.stderr)
    return TestResult(
        name="数据组合测试[25 组]" if not select_ids else f"数据组合测试[{len(select_ids)} 组]",
        success=(proc.returncode == 0),
        passed=p, failed=f, skipped=s,
        duration_sec=round(dur, 2),
        report_path=str(report) if report.exists() else None,
        raw_output=proc.stdout + proc.stderr,
        extra={"csv_path": str(csv_path), "regenerated": regenerate},
    )


# ============================================================
# 性能测试
# ============================================================

def run_performance(
    *,
    users: int = 120,
    spawn_rate: int = 10,
    run_time: str = "60s",
) -> TestResult:
    """运行 Locust 性能测试。

    Parameters
    ----------
    users: 并发用户数
    spawn_rate: 每秒新增用户数
    run_time: 持续时长（Locust 语法），例如 "60s" / "3m" / "1h"
    """
    if users <= 0:
        raise ValueError("users 必须为正整数")
    if spawn_rate <= 0:
        raise ValueError("spawn_rate 必须为正整数")

    html_report = ROOT / "reports" / "locust" / f"report_{users}users.html"
    html_report.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        PYTHON, "-m", "locust",
        "-f", str(ROOT / "tests" / "performance" / "locustfile.py"),
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", run_time,
        "--headless",
        "--html", str(html_report),
    ]
    proc, dur = _run_subprocess(cmd)
    stats = _parse_locust_aggregated(proc.stdout + proc.stderr)

    return TestResult(
        name=f"性能测试[{users} 并发 / {run_time}]",
        success=(proc.returncode == 0),
        passed=0, failed=0, skipped=0,
        duration_sec=round(dur, 2),
        report_path=str(html_report) if html_report.exists() else None,
        raw_output=proc.stdout + proc.stderr,
        extra={"users": users, "spawn_rate": spawn_rate, "run_time": run_time, **stats},
    )


# ============================================================
# 元数据 / 默认参数
# ============================================================

def list_test_cases() -> dict:
    """返回所有可用测试的元数据（深拷贝意义不大，直接返回引用即可——GUI 不应该改）。"""
    return TEST_CATALOG


def get_default_params() -> dict:
    """各测试的默认参数；GUI 表单初始化用。"""
    return {
        "unit": {"module": "all", "keyword": "dress", "product_index": 0},
        "integration": {"depth": "all", "keyword": "dress", "product_index": 0},
        "data_combination": {"regenerate": False},
        "performance": {"users": 120, "spawn_rate": 10, "run_time": "60s"},
    }


# ============================================================
# 命令行自检
# ============================================================

if __name__ == "__main__":
    print("[siqi_interface] ROOT =", ROOT)
    print("[siqi_interface] PYTHON =", PYTHON)
    print("[siqi_interface] 可用测试场景:")
    for k in TEST_CATALOG:
        print(f"  - {k}")
    print("[siqi_interface] 默认参数:", get_default_params())
