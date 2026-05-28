"""xupeng adapter：包装 comprehensive-experiments/xupeng/xupeng_interface.py。

与 siqi adapter 同形：
- 用 sys.path 注入定位 xupeng_interface
- 防御性把子进程 PYTHON 改写为 UI/.venv
- 数据组合用 [TSxxx] 标签解析逐用例结果到 extra.per_case
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Adapter, TestResult

XUPENG_ROOT = Path(__file__).resolve().parents[3] / "xupeng"
if str(XUPENG_ROOT) not in sys.path:
    sys.path.insert(0, str(XUPENG_ROOT))

import xupeng_interface as _xupeng  # noqa: E402

# 与 siqi adapter 同款的 venv 强制改写
_UI_ROOT = Path(__file__).resolve().parents[2]
_VENV_PY = _UI_ROOT / ".venv" / "Scripts" / "python.exe"
if _VENV_PY.exists():
    _xupeng.PYTHON = str(_VENV_PY)
else:
    import warnings
    warnings.warn(
        f"xupeng adapter: 未找到 UI/.venv/Scripts/python.exe (期望 {_VENV_PY})；"
        f"将沿用 sys.executable={_xupeng.PYTHON}，子进程可能缺少依赖。",
        RuntimeWarning,
    )


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


# xupeng 的数据组合用例 id 是 TSxxx；pytest 报告每行末尾会出现 [...-TSxxx] PASSED/FAILED
_DATA_CASE_PATTERN = re.compile(r"\b(TS\d+)\][^\[\]]*?(PASSED|FAILED|ERROR|SKIPPED)")


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


class XupengAdapter:
    owner = "xupeng"
    available = True

    # ---- 元数据 ----
    def list_modules(self) -> list[str]:
        return ["contact", "category", "subscribe"]

    def list_test_cases(self) -> dict:
        return _xupeng.list_test_cases()

    def get_default_params(self) -> dict:
        return _xupeng.get_default_params()

    # ---- 运行 ----
    def run_unit(self, module: str, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = {"module": module, **kwargs}
        r = _xupeng.run_unit(module=module, **kwargs)
        return _wrap(r, self.owner, started, params)

    def run_integration(self, depth: int, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = {"depth": depth, **kwargs}
        r = _xupeng.run_integration(depth=depth, **kwargs)
        return _wrap(r, self.owner, started, params)

    def run_data_combination(self, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = dict(kwargs)
        r = _xupeng.run_data_combination(**kwargs)
        wrapped = _wrap(r, self.owner, started, params)
        wrapped.extra["per_case"] = _parse_data_combo_per_case(r.raw_output)
        return wrapped

    def run_performance(self, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = dict(kwargs)
        r = _xupeng.run_performance(**kwargs)
        return _wrap(r, self.owner, started, params)

    # ---- 数据组合"待跑"列表 ----
    def list_data_cases(self) -> list[dict]:
        return _xupeng.list_data_cases()
