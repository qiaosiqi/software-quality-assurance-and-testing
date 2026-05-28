"""siqi adapter：包装 comprehensive-experiments/siqi/siqi_interface.py。

设计要点：
- 不把 siqi 包装成 pip 包，用 sys.path 注入方式让 import 找到。
- TestResult 字段映射：siqi_interface 返回的 TestResult 字段名一致，
  这里只补 started_at / params / owner 三个 GUI 扩展字段。
"""
from __future__ import annotations

import csv
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Adapter, TestResult

# 把 siqi 目录加进 sys.path，使 siqi_interface 可 import
SIQI_ROOT = Path(__file__).resolve().parents[3] / "siqi"
if str(SIQI_ROOT) not in sys.path:
    sys.path.insert(0, str(SIQI_ROOT))

import siqi_interface as _siqi  # noqa: E402  延迟到 sys.path 调整后再 import

# 强制 siqi 子进程用 UI/.venv 的 Python。
# 不然如果 uvicorn 被错误的 python (如 miniconda base) 启动，sys.executable 就是错的，
# siqi 子进程会拿不到 playwright / locust 这些只装在 UI venv 里的依赖。
_UI_ROOT = Path(__file__).resolve().parents[2]
_VENV_PY = _UI_ROOT / ".venv" / "Scripts" / "python.exe"
if _VENV_PY.exists():
    _siqi.PYTHON = str(_VENV_PY)
else:
    # 找不到 venv（极少见，比如改了目录结构）：让 siqi 继续用 sys.executable，并在 server 日志里告警
    import warnings
    warnings.warn(
        f"siqi adapter: 未找到 UI/.venv/Scripts/python.exe (期望路径 {_VENV_PY})；"
        f"将沿用 sys.executable={_siqi.PYTHON}，子进程可能缺少依赖。",
        RuntimeWarning,
    )


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


_DATA_CASE_PATTERN = re.compile(r"\[(DC-\d+)\]\s+(PASSED|FAILED|ERROR|SKIPPED)")


def _parse_data_combo_per_case(output: str) -> dict:
    """从 pytest 输出按 [DC-XX] 标签提取每个数据组合用例的 status（小写）。"""
    out: dict[str, dict] = {}
    for m in _DATA_CASE_PATTERN.finditer(output or ""):
        out[m.group(1)] = {"status": m.group(2).lower()}
    return out


def _wrap(result: Any, owner: str, started_at: str, params: dict) -> TestResult:
    """把 siqi_interface.TestResult 转成 GUI 用的 TestResult。"""
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


class SiqiAdapter:
    owner = "siqi"
    available = True

    # ---- 元数据 ----
    def list_modules(self) -> list[str]:
        return ["product_list", "product_detail", "search"]

    def list_test_cases(self) -> dict:
        return _siqi.list_test_cases()

    def get_default_params(self) -> dict:
        return _siqi.get_default_params()

    # ---- 运行 ----
    def run_unit(self, module: str, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = {"module": module, **kwargs}
        r = _siqi.run_unit(module=module, **kwargs)
        return _wrap(r, self.owner, started, params)

    def run_integration(self, depth: int, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = {"depth": depth, **kwargs}
        r = _siqi.run_integration(depth=depth, **kwargs)
        return _wrap(r, self.owner, started, params)

    def run_data_combination(self, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = dict(kwargs)
        r = _siqi.run_data_combination(**kwargs)
        wrapped = _wrap(r, self.owner, started, params)
        # 把 pytest 逐用例 PASS/FAIL 解析回 extra.per_case，前端用来填"实际/结果"列
        wrapped.extra["per_case"] = _parse_data_combo_per_case(r.raw_output)
        return wrapped

    def run_performance(self, **kwargs: Any) -> TestResult:
        started = _now_iso()
        params = dict(kwargs)
        r = _siqi.run_performance(**kwargs)
        return _wrap(r, self.owner, started, params)

    # ---- 数据组合"待跑"列表 ----
    def list_data_cases(self) -> list[dict]:
        """读 testdata/combinations.csv；不存在则先生成。

        返回列形如 [{id, keyword, expected_hit, note}, ...]
        """
        csv_path = SIQI_ROOT / "testdata" / "combinations.csv"
        if not csv_path.exists():
            _siqi.generate_combinations()
        rows: list[dict] = []
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                rows.append({
                    "id": r["id"],
                    "keyword": r["keyword"],
                    "expected_hit": r["expected_hit"] in ("True", "true", "1"),
                    "note": r["note"],
                })
        return rows
