"""Adapter 抽象和 TestResult 数据结构。

TestResult 在 siqi_interface 原版基础上扩展两个字段（started_at, params），
方便历史记录索引使用。
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional, Protocol


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

    # GUI 层扩展字段
    started_at: str = ""              # ISO8601，开始执行时间
    params: dict = field(default_factory=dict)  # 调用时传入的参数（用于历史回溯）
    owner: str = ""                   # 所属成员

    def to_dict(self) -> dict:
        return asdict(self)


class Adapter(Protocol):
    """所有成员 adapter 必须实现的协议。"""

    owner: str
    available: bool   # False 时表示该成员尚未实现，UI 灰显

    def run_unit(self, module: str, **kwargs: Any) -> TestResult: ...
    def run_integration(self, depth: int, **kwargs: Any) -> TestResult: ...
    def run_data_combination(self, **kwargs: Any) -> TestResult: ...
    def run_performance(self, **kwargs: Any) -> TestResult: ...
    def list_modules(self) -> list[str]: ...
    def list_test_cases(self) -> dict: ...
    def get_default_params(self) -> dict: ...
    def list_data_cases(self) -> list[dict]: ...   # 数据组合测试的"待跑"列表
