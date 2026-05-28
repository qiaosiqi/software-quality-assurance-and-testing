"""未实现成员的占位 adapter。所有 run_* 抛 NotImplementedError，元数据返回空。

UI 拿到 available=False 后会把对应模块卡片/tab 灰显。
"""
from __future__ import annotations

from typing import Any

from .base import Adapter, TestResult


class _PlaceholderAdapter:
    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.available = False

    def _not_impl(self) -> None:
        raise NotImplementedError(f"成员 {self.owner} 的 adapter 尚未实现")

    def list_modules(self) -> list[str]:
        return []

    def list_test_cases(self) -> dict:
        return {}

    def get_default_params(self) -> dict:
        return {}

    def run_unit(self, module: str, **kwargs: Any) -> TestResult:
        self._not_impl()

    def run_integration(self, depth: int, **kwargs: Any) -> TestResult:
        self._not_impl()

    def run_data_combination(self, **kwargs: Any) -> TestResult:
        self._not_impl()

    def run_performance(self, **kwargs: Any) -> TestResult:
        self._not_impl()

    def list_data_cases(self) -> list[dict]:
        return []


def make_placeholder(owner: str) -> Adapter:
    return _PlaceholderAdapter(owner)
