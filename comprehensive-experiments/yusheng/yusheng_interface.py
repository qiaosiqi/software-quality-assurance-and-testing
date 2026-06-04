"""yusheng 实验统一接口适配文件。

为上层 GUI 提供"运行测试 / 传参 / 收集结果"的可调用函数。

模块覆盖：添加购物车 / 修改购物车数量 / 删除购物车商品

yusheng 主测试文件 test_cart_module.py 用 unittest.TestCase + HtmlTestRunner，
pytest 可以直接跑 unittest.TestCase 子类，所以本接口统一走 pytest 子进程。
（HtmlTestRunner 只在 yusheng 自己 __main__ 入口走，pytest 模式无需安装。）

公共 API（与 siqi/xupeng 同形）:
    run_unit(module)               # cart_add / cart_qty / cart_remove / all
    run_integration(depth, *, path)# (depth, path) ∈ {(5,1),(5,2),(5,3)}
    run_data_combination(*, regenerate=False)
    run_performance(*, users, spawn_rate, run_time)
    list_test_cases()
    get_default_params()
    list_data_cases()
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
PYTHON = sys.executable

# ============================================================
# 元数据
# ============================================================

# 主文件里 6 个测试方法的 unittest nodeid（pytest 兼容写法）：
_MAIN = "test_cart_module.py::TestCartModule"

TEST_CATALOG = {
    "unit": {
        "cart_add": {
            "id": "TC-CartAdd-01",
            "name": "添加购物车模块",
            "node": f"{_MAIN}::test_add_to_cart",
            "supports": [],
        },
        "cart_qty": {
            "id": "TC-CartQty-01",
            "name": "修改购物车数量模块",
            "node": f"{_MAIN}::test_modify_cart_quantity",
            "supports": [],
        },
        "cart_remove": {
            "id": "TC-CartRemove-01",
            "name": "删除购物车商品模块",
            "node": f"{_MAIN}::test_delete_cart_item",
            "supports": [],
        },
    },
    "integration": {
        # (depth, path) -> 集成测试 nodeid
        (5, 1): {
            "id": "TC-Integration-Depth5-Y1",
            "name": "Flow1：登录 → 加购 → 购物车 → 删除",
            "node": f"{_MAIN}::test_flow_login_cart_delete",
            "supports": [],
        },
        (5, 2): {
            "id": "TC-Integration-Depth5-Y2",
            "name": "Flow2：商品详情 → 修改数量 → 加购 → 校验",
            "node": f"{_MAIN}::test_flow_product_quantity",
            "supports": [],
        },
        (5, 3): {
            "id": "TC-Integration-Depth5-Y3",
            "name": "Flow3：搜索 → 加购 → 购物车 → 删除",
            "node": f"{_MAIN}::test_flow_search_add_delete",
            "supports": [],
        },
    },
    "data_combination": {
        "id": "TC-DataCombination",
        "name": "数据组合测试（搜索关键词 25 组）",
        "node": "test_data_combination_yusheng.py",
        "supports": [],
    },
    "performance": {
        "id": "TC-Performance-01",
        "name": "性能测试（Locust，购物车相关端点）",
        "file": "load_test.py",
        "supports": ["users", "spawn_rate", "run_time"],
    },
}

# 数据组合 25 条元数据（与 test_data_combination_yusheng.DATA_CASES 一致）
DATA_CASES: list[dict] = [
    {"id": "YS01", "keyword": "top",       "expected_hit": True, "note": "服饰品类"},
    {"id": "YS02", "keyword": "shirt",     "expected_hit": True, "note": "服饰品类"},
    {"id": "YS03", "keyword": "jean",      "expected_hit": True, "note": "服饰品类（部分词）"},
    {"id": "YS04", "keyword": "dress",     "expected_hit": True, "note": "服饰品类"},
    {"id": "YS05", "keyword": "blue",      "expected_hit": True, "note": "颜色"},
    {"id": "YS06", "keyword": "red",       "expected_hit": True, "note": "颜色"},
    {"id": "YS07", "keyword": "green",     "expected_hit": True, "note": "颜色"},
    {"id": "YS08", "keyword": "men",       "expected_hit": True, "note": "人群"},
    {"id": "YS09", "keyword": "women",     "expected_hit": True, "note": "人群"},
    {"id": "YS10", "keyword": "kids",      "expected_hit": True, "note": "人群"},
    {"id": "YS11", "keyword": "cotton",    "expected_hit": True, "note": "材质"},
    {"id": "YS12", "keyword": "winter",    "expected_hit": True, "note": "季节"},
    {"id": "YS13", "keyword": "summer",    "expected_hit": True, "note": "季节"},
    {"id": "YS14", "keyword": "fashion",   "expected_hit": True, "note": "风格"},
    {"id": "YS15", "keyword": "sport",     "expected_hit": True, "note": "风格"},
    {"id": "YS16", "keyword": "tshirt",    "expected_hit": True, "note": "服饰品类"},
    {"id": "YS17", "keyword": "jacket",    "expected_hit": True, "note": "服饰品类"},
    {"id": "YS18", "keyword": "saree",     "expected_hit": True, "note": "服饰品类"},
    {"id": "YS19", "keyword": "stylish",   "expected_hit": True, "note": "风格"},
    {"id": "YS20", "keyword": "soft",      "expected_hit": True, "note": "材质"},
    {"id": "YS21", "keyword": "beautiful", "expected_hit": True, "note": "形容词"},
    {"id": "YS22", "keyword": "jeans",     "expected_hit": True, "note": "服饰品类"},
    {"id": "YS23", "keyword": "clothes",   "expected_hit": True, "note": "通用词"},
    {"id": "YS24", "keyword": "trend",     "expected_hit": True, "note": "风格"},
    {"id": "YS25", "keyword": "sale",      "expected_hit": True, "note": "促销词"},
]


# ============================================================
# 结果对象
# ============================================================

@dataclass
class TestResult:
    name: str
    success: bool
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_sec: float = 0.0
    report_path: Optional[str] = None
    raw_output: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# 内部辅助
# ============================================================

def _run_subprocess(cmd: list[str], env_extra: Optional[dict] = None) -> tuple[subprocess.CompletedProcess, float]:
    """env_extra：仅注入到该子进程的额外环境变量（如 SQA_HEADLESS=1），不污染当前进程。"""
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
    cmd = [PYTHON, "-m", "pytest", *args]
    if html_report is not None:
        html_report.parent.mkdir(parents=True, exist_ok=True)
        cmd += [f"--html={html_report}", "--self-contained-html"]
    return _run_subprocess(cmd, env_extra=env_extra)


def _headless_env(headless: bool) -> Optional[dict]:
    return {"SQA_HEADLESS": "1"} if headless else None


def _parse_pytest_summary(output: str) -> tuple[int, int, int]:
    passed = failed = skipped = 0
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
    """倒序找带 (X.XX%) 格式的 Aggregated 行（最终 stats），避开启动快照的全 0 行和 percentiles 表。"""
    stats: dict = {}
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        if not stripped.startswith("Aggregated"):
            continue
        fr = re.search(r"\(([\d.]+)%\)", stripped)
        if not fr:
            continue  # 跳过 percentiles 表的 Aggregated 行
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

def run_unit(module: str = "all", *, headless: bool = False, **_ignored) -> TestResult:
    """运行单元测试。

    module: cart_add / cart_qty / cart_remove / all
    """
    if module == "all":
        # 跑主文件里 3 个单元测试（用 -k 排除集成 flow 和性能 / 数据组合）
        args = [f"{_MAIN}", "-k", "add_to_cart or modify_cart_quantity or delete_cart_item"]
        tag = "all"
    elif module in TEST_CATALOG["unit"]:
        args = [TEST_CATALOG["unit"][module]["node"]]
        tag = module
    else:
        raise ValueError(f"未知 module='{module}'，可选: cart_add / cart_qty / cart_remove / all")

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
        extra={"module": module},
    )


# ============================================================
# 集成测试
# ============================================================

def run_integration(depth: Union[int, str] = 5, *, path: int = 1,
                    headless: bool = False, **_ignored) -> TestResult:
    """运行集成测试。

    depth: 5（yusheng 3 条 flow 都是 depth 5）
    path:  1 | 2 | 3
    """
    if depth == "all":
        args = [_MAIN, "-k", "flow_"]
        tag = "all"
    else:
        key = (int(depth), int(path))
        if key not in TEST_CATALOG["integration"]:
            raise ValueError(
                f"未知 (depth={depth}, path={path})，可选: "
                f"{list(TEST_CATALOG['integration'].keys())}"
            )
        args = [TEST_CATALOG["integration"][key]["node"]]
        tag = f"d{depth}p{path}"

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
        extra={"depth": depth, "path": path},
    )


# ============================================================
# 数据组合（独立文件 25 条 parametrize）
# ============================================================

def run_data_combination(*, regenerate: bool = False,
                         select_ids: Optional[list[str]] = None,
                         headless: bool = False, **_ignored) -> TestResult:
    """select_ids 给定时只跑这些 id 的子集（如 ["YS01","YS02"]）；headless 供 demo 用。"""
    report = ROOT / "reports" / "html" / "data_combination.html"
    args = ["test_data_combination_yusheng.py"]
    if select_ids:
        args += ["-k", " or ".join(select_ids)]
    proc, dur = _run_pytest(args, html_report=report, env_extra=_headless_env(headless))
    p, f, s = _parse_pytest_summary(proc.stdout + proc.stderr)
    return TestResult(
        name="数据组合测试[25 组]" if not select_ids else f"数据组合测试[{len(select_ids)} 组]",
        success=(proc.returncode == 0),
        passed=p, failed=f, skipped=s,
        duration_sec=round(dur, 2),
        report_path=str(report) if report.exists() else None,
        raw_output=proc.stdout + proc.stderr,
        extra={"regenerated": regenerate},
    )


# ============================================================
# 性能测试（Locust）
# ============================================================

def run_performance(
    *,
    users: int = 120,
    spawn_rate: int = 10,
    run_time: str = "60s",
    **_ignored,
) -> TestResult:
    if users <= 0:
        raise ValueError("users 必须为正整数")
    if spawn_rate <= 0:
        raise ValueError("spawn_rate 必须为正整数")

    html_report = ROOT / "reports" / "locust" / f"report_{users}users.html"
    html_report.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        PYTHON, "-m", "locust",
        "-f", str(ROOT / "load_test.py"),
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", run_time,
        "--headless",
        "--host", "https://automationexercise.com",
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
# 元数据
# ============================================================

def list_test_cases() -> dict:
    return TEST_CATALOG


def get_default_params() -> dict:
    return {
        "unit": {"module": "all"},
        "integration": {"depth": 5, "path": 1},
        "data_combination": {"regenerate": False},
        "performance": {"users": 120, "spawn_rate": 10, "run_time": "60s"},
    }


def list_data_cases() -> list[dict]:
    return list(DATA_CASES)


if __name__ == "__main__":
    print("[yusheng_interface] ROOT =", ROOT)
    print("[yusheng_interface] PYTHON =", PYTHON)
    print("[yusheng_interface] modules:", list(TEST_CATALOG["unit"].keys()))
    print("[yusheng_interface] integrations:", list(TEST_CATALOG["integration"].keys()))
    print("[yusheng_interface] data cases:", len(list_data_cases()))
