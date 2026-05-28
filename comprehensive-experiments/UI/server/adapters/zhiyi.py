"""zhiyi adapter：包装 comprehensive-experiments/zhiyi/zhiyi_interface.py。

zhiyi 是 Java/TestNG/Maven 工程；adapter 不像 siqi/xupeng/yusheng 那样有
"子进程 PYTHON 改写"的需求（zhiyi 跑的是 mvn.cmd 不是 Python）。
但需要确认 .maven 二进制存在。
"""
from __future__ import annotations

import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Adapter, TestResult

ZHIYI_ROOT = Path(__file__).resolve().parents[3] / "zhiyi"
if str(ZHIYI_ROOT) not in sys.path:
    sys.path.insert(0, str(ZHIYI_ROOT))

import zhiyi_interface as _zhiyi  # noqa: E402

# 校验本地 Maven 是否存在；不存在则 available=False（UI 会灰显并提示装 Maven）
_LOCAL_MVN = ZHIYI_ROOT / ".maven" / "apache-maven-3.9.9" / "bin" / "mvn.cmd"
_HAS_LOCAL_MVN = _LOCAL_MVN.exists()
if not _HAS_LOCAL_MVN:
    warnings.warn(
        f"zhiyi adapter: 未找到本地 Maven (期望 {_LOCAL_MVN})。"
        f"如未配置 MAVEN_HOME 或系统 PATH 上没有 mvn，zhiyi 测试将无法运行。",
        RuntimeWarning,
    )


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _wrap(result: Any, owner: str, started_at: str, params: dict) -> TestResult:
    return TestResult(
        name=result.name,
        success=result.success,
        passed=result.passed,
        failed=result.failed,
        skipped=result.skipped,
        duration_sec=result.duration_sec,
        report_path=result.report_path,
        raw_output=result.raw_output,
        extra=dict(result.extra),
        started_at=started_at,
        params=params,
        owner=owner,
    )


class ZhiyiAdapter:
    owner = "zhiyi"
    # 只要 zhiyi_interface 能 import，就认为可用；MVN 缺失也允许调用，让接口层抛错给前端
    available = True

    def list_modules(self) -> list[str]:
        return ["register", "login", "logout"]

    def list_test_cases(self) -> dict:
        return _zhiyi.list_test_cases()

    def get_default_params(self) -> dict:
        return _zhiyi.get_default_params()

    def run_unit(self, module: str, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = {"module": module, **kwargs}
        r = _zhiyi.run_unit(module=module, **kwargs)
        return _wrap(r, self.owner, started, params)

    def run_integration(self, depth: int, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = {"depth": depth, **kwargs}
        r = _zhiyi.run_integration(depth=depth, **kwargs)
        return _wrap(r, self.owner, started, params)

    def run_data_combination(self, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = dict(kwargs)
        r = _zhiyi.run_data_combination(**kwargs)
        return _wrap(r, self.owner, started, params)

    def run_performance(self, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = dict(kwargs)
        r = _zhiyi.run_performance(**kwargs)
        return _wrap(r, self.owner, started, params)

    def list_data_cases(self) -> list[dict]:
        return _zhiyi.list_data_cases()
