"""xupeng 实验统一接口适配文件。

为上层 GUI 提供"运行测试 / 传参 / 收集结果"的可调用函数，
内部通过 subprocess 调用 pytest 和 locust，避免污染当前进程。

模块覆盖：联系我们 / 分类筛选 / 订阅

公共 API（与 siqi_interface 同形）:
    run_unit(module)               # contact / category / subscribe / all
    run_integration(depth, *, path)# (depth, path) ∈ {(5,1),(6,2),(5,3)}
    run_data_combination(*, regenerate=False)
    run_performance(*, users, spawn_rate, run_time)
    list_test_cases()
    get_default_params()
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
PYTHON = sys.executable  # 默认沿用当前解释器；UI 侧 adapter 会强制改写为 UI/.venv

# ============================================================
# 元数据 —— 供 GUI 渲染列表 / 表单
# ============================================================

TEST_CATALOG = {
    "unit": {
        "contact": {
            "id": "TC-Contact-01",
            "name": "联系我们模块",
            "node": "test1.py::TestAutomationExercise::test_10_contact_us_form",
            "supports": [],
        },
        "category": {
            "id": "TC-Category-01",
            "name": "分类筛选模块（Women+Men）",
            # test_11_category_filter_women / test_11_category_filter_men
            "node": "test1.py -k category_filter",
            "supports": [],
        },
        "subscribe": {
            "id": "TC-Subscribe-01",
            "name": "订阅模块",
            "node": "test1.py::TestAutomationExercise::test_12_subscription_newsletter",
            "supports": [],
        },
    },
    "integration": {
        # 以 (depth, path) 为 key，path 用来区分相同深度的不同路径
        (5, 1): {
            "id": "TC-Integration-Depth5-01",
            "name": "Women/Dress + Men/Tshirt 多商品加购",
            "node": "test_module.py::TestIntegrationScenarios::test_integration_1_multi_items_cart",
            "supports": [],
        },
        (6, 2): {
            "id": "TC-Integration-Depth6-01",
            "name": "Products → 搜索 → 加购 → 订阅",
            "node": "test_module.py::TestIntegrationScenarios::test_integration_2_search_filter_subscribe",
            "supports": [],
        },
        (5, 3): {
            "id": "TC-Integration-Depth5-02",
            "name": "品牌筛选 → 加购 → 购物车 → 删除",
            "node": "test_module.py::TestIntegrationScenarios::test_integration_3_brand_filter_cart_delete",
            "supports": [],
        },
    },
    "data_combination": {
        "id": "TC-DataCombination",
        "name": "数据组合测试（搜索关键词 25 组）",
        "node": "data_test.py::TestSearchProductsDataCombination",
        "supports": [],
    },
    "performance": {
        "id": "TC-Performance-01",
        "name": "性能测试（Locust，3 模块端点）",
        "file": "load_test.py",
        "supports": ["users", "spawn_rate", "run_time"],
    },
}

# 数据组合 25 条的元数据（从 data_test.py 的 parametrize 镜像而来，供 GUI 列表显示）
# 字段对齐 siqi 的 list_data_cases() 返回结构：id / keyword / expected_hit / note
DATA_CASES: list[dict] = [
    {"id": "TS001", "keyword": "dress",  "expected_hit": True, "note": "正常有效关键词"},
    {"id": "TS002", "keyword": "top",    "expected_hit": True, "note": "正常有效关键词"},
    {"id": "TS003", "keyword": "jeans",  "expected_hit": True, "note": "正常有效关键词"},
    {"id": "TS004", "keyword": "shirt",  "expected_hit": True, "note": "正常有效关键词"},
    {"id": "TS005", "keyword": "saree",  "expected_hit": True, "note": "正常有效关键词"},
    {"id": "TS006", "keyword": "tshirt", "expected_hit": True, "note": "正常有效关键词"},
    {"id": "TS007", "keyword": "cotton", "expected_hit": True, "note": "正常有效关键词"},
    {"id": "TS008", "keyword": "women",  "expected_hit": True, "note": "正常有效关键词"},
    {"id": "TS009", "keyword": "Dress",  "expected_hit": True, "note": "大小写混合"},
    {"id": "TS010", "keyword": "JEANS",  "expected_hit": True, "note": "大小写混合"},
    {"id": "TS011", "keyword": "Top",    "expected_hit": True, "note": "大小写混合"},
    {"id": "TS012", "keyword": "Shirt",  "expected_hit": True, "note": "大小写混合"},
    {"id": "TS013", "keyword": "dre",    "expected_hit": True, "note": "部分关键词"},
    {"id": "TS014", "keyword": "jean",   "expected_hit": True, "note": "部分关键词"},
    {"id": "TS015", "keyword": "shi",    "expected_hit": True, "note": "部分关键词"},
    {"id": "TS016", "keyword": "sar",    "expected_hit": True, "note": "部分关键词"},
    {"id": "TS017", "keyword": "dress",  "expected_hit": True, "note": "稳定性重复"},
    {"id": "TS018", "keyword": "jeans",  "expected_hit": True, "note": "稳定性重复"},
    {"id": "TS019", "keyword": "top",    "expected_hit": True, "note": "稳定性重复"},
    {"id": "TS020", "keyword": "tshirt", "expected_hit": True, "note": "稳定性重复"},
    {"id": "TS021", "keyword": "saree",  "expected_hit": True, "note": "稳定性重复"},
    {"id": "TS022", "keyword": "men",    "expected_hit": True, "note": "边界/特殊"},
    {"id": "TS023", "keyword": "girl",   "expected_hit": True, "note": "边界/特殊"},
    {"id": "TS024", "keyword": "soft",   "expected_hit": True, "note": "边界/特殊"},
    {"id": "TS025", "keyword": "white",  "expected_hit": True, "note": "边界/特殊"},
]


# ============================================================
# 统一结果对象（字段与 siqi_interface.TestResult 对齐）
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
    """从 pytest 末尾汇总行解析 (passed, failed, skipped)。"""
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

    Parameters
    ----------
    module: "contact" | "category" | "subscribe" | "all"
    """
    if module == "all":
        args = ["test1.py"]
        tag = "all"
    elif module == "contact":
        args = ["test1.py::TestAutomationExercise::test_10_contact_us_form"]
        tag = "contact"
    elif module == "category":
        args = ["test1.py", "-k", "category_filter"]
        tag = "category"
    elif module == "subscribe":
        args = ["test1.py::TestAutomationExercise::test_12_subscription_newsletter"]
        tag = "subscribe"
    else:
        raise ValueError(f"未知 module='{module}'，可选: contact / category / subscribe / all")

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

    Parameters
    ----------
    depth: 5 | 6（xupeng 没有 depth 3/4）
    path:  1 | 2 | 3（区分相同深度的不同路径，组合见 TEST_CATALOG["integration"]）
    """
    if depth == "all":
        # all 模式：跑整个 test_module.py
        args = ["test_module.py"]
        tag = "all"
    else:
        key = (int(depth), int(path))
        if key not in TEST_CATALOG["integration"]:
            raise ValueError(
                f"未知 (depth={depth}, path={path})，可选组合: "
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
# 数据组合
# ============================================================

def run_data_combination(*, regenerate: bool = False,
                         select_ids: Optional[list[str]] = None,
                         headless: bool = False, **_ignored) -> TestResult:
    """运行数据组合测试（默认 25 组搜索关键词）。

    regenerate 参数为了对齐 siqi 接口保留，xupeng 没有动态生成步骤，传入会被忽略。
    select_ids 给定时只跑这些 id 子集（如 ["TS001","TS002"]）；headless 供 demo 用。
    """
    report = ROOT / "reports" / "html" / "data_combination.html"
    args = ["data_test.py::TestSearchProductsDataCombination"]
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
# 性能测试
# ============================================================

def run_performance(
    *,
    users: int = 120,
    spawn_rate: int = 10,
    run_time: str = "60s",
    **_ignored,
) -> TestResult:
    """运行 Locust 性能测试，覆盖 xupeng 的 3 模块端点。"""
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
    """返回 25 条数据组合的元数据（供 GUI 列表渲染）。"""
    return list(DATA_CASES)


if __name__ == "__main__":
    print("[xupeng_interface] ROOT =", ROOT)
    print("[xupeng_interface] PYTHON =", PYTHON)
    print("[xupeng_interface] 可用测试场景:")
    for k in TEST_CATALOG:
        print(f"  - {k}")
    print("[xupeng_interface] 默认参数:", get_default_params())
