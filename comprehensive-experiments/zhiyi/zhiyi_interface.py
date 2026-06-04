"""zhiyi 实验统一接口适配文件。

zhiyi 的测试是 Java/TestNG/Maven 工程（automationexercise-selenium-testng/）。
本接口通过 subprocess 调本地 Maven（zhiyi/.maven/apache-maven-3.9.9/bin/mvn.cmd），
跑 surefire 后解析输出和 surefire-reports 目录里的 XML 报告。

公共 API（与 siqi/xupeng/yusheng 同形）:
    run_unit(module)               # register / login / logout / all
    run_integration(depth, *, path)# (depth, path) ∈ {(4,1),(5,1)} ——zhiyi 只有 2 条
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
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional, Union

# zhiyi 根目录（本文件位置）
ROOT = Path(__file__).resolve().parent

# Java 项目根（含 pom.xml）
JAVA_ROOT = ROOT / "automationexercise-selenium-testng"

# 本地 Maven 安装（用户安装时方案 A，下载 Apache Maven 二进制到 .maven/）
LOCAL_MVN = ROOT / ".maven" / "apache-maven-3.9.9" / "bin" / "mvn.cmd"

# 兜底：若用户系统装了 mvn，环境变量 MAVEN_HOME 优先
def _resolve_mvn() -> str:
    env_home = os.environ.get("MAVEN_HOME")
    if env_home:
        candidate = Path(env_home) / "bin" / "mvn.cmd"
        if candidate.exists():
            return str(candidate)
    if LOCAL_MVN.exists():
        return str(LOCAL_MVN)
    # 最后兜底 PATH 上的 mvn
    return "mvn"

MVN = _resolve_mvn()

# ============================================================
# 元数据
# ============================================================

# 测试类全限定 + 方法名映射
_SINGLE = "com.example.ae.tests.SingleModuleTest"
_INTEGRATION = "com.example.ae.tests.IntegrationModuleTest"
_DATA_COMBO = "com.example.ae.tests.LoginDataCombinationTest"
_PERF = "com.example.ae.tests.PerformanceHttpTest"

TEST_CATALOG = {
    "unit": {
        "register": {
            "id": "TC-Register-01",
            "name": "注册模块",
            "node": f"{_SINGLE}#registerModule_shouldCreateAccount",
            "supports": [],
        },
        "login": {
            "id": "TC-Login-01",
            "name": "登录模块（正确+错误两条）",
            # 同一类多个方法用 + 连接
            "node": (
                f"{_SINGLE}#loginModule_shouldLoginWithCorrectPassword"
                f"+loginModule_shouldShowErrorWithWrongPassword"
            ),
            "supports": [],
        },
        "logout": {
            "id": "TC-Logout-01",
            "name": "登出模块",
            "node": f"{_SINGLE}#logoutModule_shouldReturnToLoginPage",
            "supports": [],
        },
    },
    "integration": {
        (4, 1): {
            "id": "TC-Integration-Depth4-Z1",
            "name": "深度4：注册 → 登出 → 正确登录 → 登出",
            "node": f"{_INTEGRATION}#integration_depth4_registerLogoutLoginLogout",
            "supports": [],
        },
        (5, 1): {
            "id": "TC-Integration-Depth5-Z1",
            "name": "深度5：注册 → 登出 → 错误登录 → 正确登录 → 登出",
            "node": f"{_INTEGRATION}#integration_depth5_registerLogoutWrongLoginCorrectLoginLogout",
            "supports": [],
        },
    },
    "data_combination": {
        "id": "TC-DataCombination",
        "name": "数据组合测试（账号5×密码5=25 组）",
        "node": _DATA_COMBO,
        "supports": [],
    },
    "performance": {
        "id": "TC-Performance-01",
        "name": "性能测试（Java HttpClient，固定线程数模型）",
        "node": _PERF,
        # zhiyi 实际用 Java HttpClient 固定线程 × 固定每线程请求数模型，与 Locust 概念不同。
        # 不暴露 spawn_rate/run_time，改用 zhiyi 真实支持的两个参数。
        "supports": ["users", "requests_per_thread"],
    },
}

# 25 组登录组合（与 LoginDataCombinationTest.loginCombinations() 同顺序）
_EMAIL_CASES = ["E1_VALID", "E2_NOT_EXIST", "E3_EMPTY", "E4_INVALID_FORMAT", "E5_UPPERCASE_VALID"]
_PASSWORD_CASES = ["P1_VALID", "P2_WRONG", "P3_EMPTY", "P4_SHORT", "P5_SPACE"]


def _expected_for(email_case: str, password_case: str) -> str:
    """与 Java 侧 expectedResult() 规则保持一致。"""
    if email_case in ("E3_EMPTY", "E4_INVALID_FORMAT") or password_case == "P3_EMPTY":
        return "REQUIRED"
    if email_case == "E1_VALID" and password_case == "P1_VALID":
        return "SUCCESS"
    return "ERROR"


def _build_data_cases() -> list[dict]:
    rows: list[dict] = []
    for e in _EMAIL_CASES:
        for p in _PASSWORD_CASES:
            case_id = f"{e}+{p}"
            expected = _expected_for(e, p)
            rows.append({
                "id": case_id,
                "keyword": case_id,                              # 复用 keyword 字段做 GUI 列名
                "expected_hit": expected == "SUCCESS",           # 仅 E1+P1 为 SUCCESS
                "note": f"expected={expected}",
            })
    return rows


DATA_CASES: list[dict] = _build_data_cases()


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

def _run_mvn(args: list[str]) -> tuple[subprocess.CompletedProcess, float]:
    """跑 mvn 子进程，cwd 必须是 JAVA_ROOT（有 pom.xml 的目录）。"""
    env = os.environ.copy()
    env["MAVEN_OPTS"] = env.get("MAVEN_OPTS", "") + " -Dfile.encoding=UTF-8"
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [MVN, "-B", *args]
    start = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(JAVA_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return proc, time.time() - start


# 解析 mvn / surefire 输出中的汇总行：
#   [INFO] Tests run: 25, Failures: 1, Errors: 0, Skipped: 0
_TESTS_SUMMARY_RE = re.compile(
    r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)"
)


def _parse_summary(output: str) -> tuple[int, int, int]:
    """返回 (passed, failed, skipped)。

    Surefire 把 errors 跟 failures 分开报；我们把它合并到 failed。
    可能有多行 Tests run: ...（每个测试类一行 + 一个 total）。取最后一个（total）。
    """
    matches = list(_TESTS_SUMMARY_RE.finditer(output or ""))
    if not matches:
        return 0, 0, 0
    last = matches[-1]
    total, failures, errors, skipped = (int(x) for x in last.groups())
    passed = total - failures - errors - skipped
    failed = failures + errors
    return max(passed, 0), failed, skipped


def _parse_data_combo_per_case() -> dict:
    """从 target/surefire-reports/junitreports/TEST-*LoginDataCombinationTest.xml 解析每条用例结果。

    JUnit XML 的 <testcase> name 形如：
        loginCombination_shouldMatchExpectedResult[0]
        loginCombination_shouldMatchExpectedResult[1]
        ...
    序号 0..24 与 DataProvider 行顺序一致，对应 _EMAIL_CASES × _PASSWORD_CASES 笛卡尔积。
    """
    reports_dir = JAVA_ROOT / "target" / "surefire-reports"
    if not reports_dir.exists():
        return {}

    # 找 LoginDataCombinationTest 相关 XML（可能在 junitreports 子目录或直接在 surefire-reports/）
    candidates = list(reports_dir.glob("TEST-*LoginDataCombinationTest*.xml"))
    candidates += list(reports_dir.glob("junitreports/TEST-*LoginDataCombinationTest*.xml"))
    if not candidates:
        return {}

    per_case: dict[str, dict] = {}
    case_ids = [f"{e}+{p}" for e in _EMAIL_CASES for p in _PASSWORD_CASES]

    for xml_path in candidates:
        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            continue
        for tc in tree.iter("testcase"):
            name = tc.get("name", "")
            m = re.match(r"loginCombination_shouldMatchExpectedResult\[(\d+)\]", name)
            if not m:
                continue
            idx = int(m.group(1))
            if idx >= len(case_ids):
                continue
            case_id = case_ids[idx]
            # 子节点 <failure> / <error> / <skipped> 决定状态
            if tc.find("failure") is not None or tc.find("error") is not None:
                status = "failed"
            elif tc.find("skipped") is not None:
                status = "skipped"
            else:
                status = "passed"
            per_case[case_id] = {"status": status}
    return per_case


# ============================================================
# 单元测试
# ============================================================

def _headless_args(headless: bool) -> list[str]:
    """headless=True 时返回 ['-Dheadless=true']，否则空（保持 testng.xml 默认 false）。"""
    return ["-Dheadless=true"] if headless else []


def run_unit(module: str = "all", *, headless: bool = False, **_ignored) -> TestResult:
    """运行单元测试。

    module: register / login / logout / all
    """
    if module == "all":
        d_test = _SINGLE
        tag = "all"
    elif module in TEST_CATALOG["unit"]:
        d_test = TEST_CATALOG["unit"][module]["node"]
        tag = module
    else:
        raise ValueError(f"未知 module='{module}'，可选: register / login / logout / all")

    args = ["test", f"-Dtest={d_test}", *_headless_args(headless)]
    proc, dur = _run_mvn(args)
    p, f, s = _parse_summary(proc.stdout + proc.stderr)
    surefire = JAVA_ROOT / "target" / "surefire-reports"
    return TestResult(
        name=f"单元测试[{tag}]",
        success=(proc.returncode == 0 and f == 0),
        passed=p, failed=f, skipped=s,
        duration_sec=round(dur, 2),
        report_path=str(surefire) if surefire.exists() else None,
        raw_output=proc.stdout + proc.stderr,
        extra={"module": module},
    )


# ============================================================
# 集成测试
# ============================================================

def run_integration(depth: Union[int, str] = 4, *, path: int = 1,
                    headless: bool = False, **_ignored) -> TestResult:
    """运行集成测试。

    depth: 4 | 5（zhiyi 只有这两条）
    path:  1
    """
    if depth == "all":
        d_test = _INTEGRATION
        tag = "all"
    else:
        key = (int(depth), int(path))
        if key not in TEST_CATALOG["integration"]:
            raise ValueError(
                f"未知 (depth={depth}, path={path})，可选: "
                f"{list(TEST_CATALOG['integration'].keys())}"
            )
        d_test = TEST_CATALOG["integration"][key]["node"]
        tag = f"d{depth}p{path}"

    args = ["test", f"-Dtest={d_test}", *_headless_args(headless)]
    proc, dur = _run_mvn(args)
    p, f, s = _parse_summary(proc.stdout + proc.stderr)
    surefire = JAVA_ROOT / "target" / "surefire-reports"
    return TestResult(
        name=f"集成测试[{tag}]",
        success=(proc.returncode == 0 and f == 0),
        passed=p, failed=f, skipped=s,
        duration_sec=round(dur, 2),
        report_path=str(surefire) if surefire.exists() else None,
        raw_output=proc.stdout + proc.stderr,
        extra={"depth": depth, "path": path},
    )


# ============================================================
# 数据组合
# ============================================================

def run_data_combination(*, regenerate: bool = False, headless: bool = False,
                         limit: Optional[int] = None, **_ignored) -> TestResult:
    """limit 给定时只跑前 limit 组（DataProvider 读 -Ddata.limit 截断）；headless 供 demo 用。"""
    args = ["test", f"-Dtest={_DATA_COMBO}", *_headless_args(headless)]
    if limit:
        args.append(f"-Ddata.limit={int(limit)}")
    proc, dur = _run_mvn(args)
    p, f, s = _parse_summary(proc.stdout + proc.stderr)
    per_case = _parse_data_combo_per_case()
    surefire = JAVA_ROOT / "target" / "surefire-reports"
    return TestResult(
        name="数据组合测试[25 组]",
        success=(proc.returncode == 0 and f == 0),
        passed=p, failed=f, skipped=s,
        duration_sec=round(dur, 2),
        report_path=str(surefire) if surefire.exists() else None,
        raw_output=proc.stdout + proc.stderr,
        extra={"regenerated": regenerate, "per_case": per_case},
    )


# ============================================================
# 性能测试
# ============================================================

def run_performance(
    *,
    users: int = 120,
    requests_per_thread: int = 2,
    **_ignored,
) -> TestResult:
    """运行 Java HTTP 性能测试。

    GUI 字段映射：
      users               -> -Dperformance.threads           （必须 >100，否则 Java 侧断言失败）
      requests_per_thread -> -Dperformance.requestsPerThread （默认 2）

    总请求数 = users × requests_per_thread。
    与 Locust 的 spawn_rate/run_time 概念无关，UI 端会用单独的表单。
    """
    if users <= 0:
        raise ValueError("users 必须为正整数")
    if requests_per_thread <= 0:
        raise ValueError("requests_per_thread 必须为正整数")

    args = [
        "test",
        "-DsuiteXmlFile=src/test/resources/testng-performance.xml",
        f"-Dperformance.threads={users}",
        f"-Dperformance.requestsPerThread={requests_per_thread}",
    ]
    proc, dur = _run_mvn(args)
    p, f, s = _parse_summary(proc.stdout + proc.stderr)
    stats = _parse_perf_stats(proc.stdout + proc.stderr)
    surefire = JAVA_ROOT / "target" / "surefire-reports"
    return TestResult(
        name=f"性能测试[{users} 并发 × {requests_per_thread} 请求]",
        success=(proc.returncode == 0 and f == 0),
        passed=p, failed=f, skipped=s,
        duration_sec=round(dur, 2),
        report_path=str(surefire) if surefire.exists() else None,
        raw_output=proc.stdout + proc.stderr,
        extra={
            "users": users,
            "requests_per_thread": requests_per_thread,
            **stats,
        },
    )


def _parse_perf_stats(output: str) -> dict:
    """从 PerformanceHttpTest.println 的统计块抽数字。

    末尾把 zhiyi 的"成功"指标派生成与 Locust 一致的"失败"指标，
    这样前端 metric-grid 对所有成员能用同一套字段名渲染。
    """
    stats: dict = {}
    patterns = {
        "total_requests":   r"总请求数:\s*(\d+)",
        "success_requests": r"成功请求数:\s*(\d+)",
        "success_rate":     r"成功率:\s*([\d.]+)%",
        "total_time_ms":    r"总耗时:\s*(\d+)\s*ms",
        "avg_latency_ms":   r"平均响应时间:\s*([\d.]+)\s*ms",
        "p95_latency_ms":   r"P95响应时间:\s*(\d+)\s*ms",
        "max_latency_ms":   r"最大响应时间:\s*(\d+)\s*ms",
    }
    for key, pat in patterns.items():
        m = re.search(pat, output)
        if m:
            try:
                stats[key] = float(m.group(1)) if "." in m.group(1) else int(m.group(1))
            except ValueError:
                stats[key] = m.group(1)
    # 与 Locust extra 字段对齐
    if "total_requests" in stats and "success_requests" in stats:
        stats["total_failures"] = stats["total_requests"] - stats["success_requests"]
    if "success_rate" in stats:
        stats["failure_rate_percent"] = round(100.0 - float(stats["success_rate"]), 2)
    return stats


# ============================================================
# 元数据
# ============================================================

def list_test_cases() -> dict:
    return TEST_CATALOG


def get_default_params() -> dict:
    return {
        "unit": {"module": "all"},
        "integration": {"depth": 4, "path": 1},
        "data_combination": {"regenerate": False},
        "performance": {"users": 120, "requests_per_thread": 2},
    }


def list_data_cases() -> list[dict]:
    return list(DATA_CASES)


if __name__ == "__main__":
    print("[zhiyi_interface] ROOT =", ROOT)
    print("[zhiyi_interface] JAVA_ROOT =", JAVA_ROOT)
    print("[zhiyi_interface] MVN =", MVN)
    print("[zhiyi_interface] modules:", list(TEST_CATALOG["unit"].keys()))
    print("[zhiyi_interface] integrations:", list(TEST_CATALOG["integration"].keys()))
    print("[zhiyi_interface] data cases:", len(list_data_cases()), "first:", DATA_CASES[0], "last:", DATA_CASES[-1])
