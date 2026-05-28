"""yusheng adapter：包装 comprehensive-experiments/yusheng/yusheng_interface.py。

与 siqi / xupeng adapter 同形。
- 数据组合 id 格式：YSxx；从 pytest 输出按 nodeid 后缀 `[YSxx]` 解析。
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Adapter, TestResult

YUSHENG_ROOT = Path(__file__).resolve().parents[3] / "yusheng"
if str(YUSHENG_ROOT) not in sys.path:
    sys.path.insert(0, str(YUSHENG_ROOT))

import yusheng_interface as _yusheng  # noqa: E402

_UI_ROOT = Path(__file__).resolve().parents[2]
_VENV_PY = _UI_ROOT / ".venv" / "Scripts" / "python.exe"
if _VENV_PY.exists():
    _yusheng.PYTHON = str(_VENV_PY)
else:
    import warnings
    warnings.warn(
        f"yusheng adapter: 未找到 UI/.venv/Scripts/python.exe (期望 {_VENV_PY})；"
        f"将沿用 sys.executable={_yusheng.PYTHON}，子进程可能缺少依赖。",
        RuntimeWarning,
    )


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


# yusheng 数据组合 id 是 YS01..YS25；pytest 行如 `... [YS01] PASSED [  4%]`
_DATA_CASE_PATTERN = re.compile(r"\[(YS\d{2})\]\s+(PASSED|FAILED|ERROR|SKIPPED)")


def _parse_data_combo_per_case(output: str) -> dict:
    out: dict[str, dict] = {}
    for m in _DATA_CASE_PATTERN.finditer(output or ""):
        out[m.group(1)] = {"status": m.group(2).lower()}
    return out


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


class YushengAdapter:
    owner = "yusheng"
    available = True

    def list_modules(self) -> list[str]:
        return ["cart_add", "cart_qty", "cart_remove"]

    def list_test_cases(self) -> dict:
        return _yusheng.list_test_cases()

    def get_default_params(self) -> dict:
        return _yusheng.get_default_params()

    def run_unit(self, module: str, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = {"module": module, **kwargs}
        r = _yusheng.run_unit(module=module, **kwargs)
        return _wrap(r, self.owner, started, params)

    def run_integration(self, depth: int, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = {"depth": depth, **kwargs}
        r = _yusheng.run_integration(depth=depth, **kwargs)
        return _wrap(r, self.owner, started, params)

    def run_data_combination(self, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = dict(kwargs)
        r = _yusheng.run_data_combination(**kwargs)
        wrapped = _wrap(r, self.owner, started, params)
        wrapped.extra["per_case"] = _parse_data_combo_per_case(r.raw_output)
        return wrapped

    def run_performance(self, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = dict(kwargs)
        r = _yusheng.run_performance(**kwargs)
        return _wrap(r, self.owner, started, params)

    def list_data_cases(self) -> list[dict]:
        return _yusheng.list_data_cases()
