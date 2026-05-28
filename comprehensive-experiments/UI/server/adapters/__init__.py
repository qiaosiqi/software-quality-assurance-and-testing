"""成员 adapter 注册表。

每个成员在自己目录下提供 `<name>_interface.py`，本包通过 adapter 模块包装统一接口。
未实现的成员用 placeholder adapter 占位（所有 run_* 抛 NotImplementedError）。
"""
from __future__ import annotations

from .base import Adapter, TestResult
from .siqi import SiqiAdapter
from .xupeng import XupengAdapter
from .yusheng import YushengAdapter
from .zhiyi import ZhiyiAdapter
from .placeholder import make_placeholder  # noqa: F401  保留以便将来按需占位

# 12 模块 → 负责成员的映射（与 ui_design.md §3.1 一致）
MODULE_OWNER: dict[str, str] = {
    "register": "zhiyi", "login": "zhiyi", "logout": "zhiyi",
    "product_list": "siqi", "product_detail": "siqi", "search": "siqi",
    "cart_add": "yusheng", "cart_qty": "yusheng", "cart_remove": "yusheng",
    "contact": "xupeng", "category": "xupeng", "subscribe": "xupeng",
}

# 12 模块元数据（业务分组、中文名）
MODULE_META: list[dict] = [
    {"id": "register",       "name": "注册模块",        "group": "账户"},
    {"id": "login",          "name": "登录模块",        "group": "账户"},
    {"id": "logout",         "name": "登出模块",        "group": "账户"},
    {"id": "product_list",   "name": "商品列表模块",     "group": "商品浏览"},
    {"id": "product_detail", "name": "商品详情模块",     "group": "商品浏览"},
    {"id": "search",         "name": "商品搜索模块",     "group": "商品浏览"},
    {"id": "cart_add",       "name": "添加购物车模块",   "group": "购物车"},
    {"id": "cart_qty",       "name": "购物车数量修改",   "group": "购物车"},
    {"id": "cart_remove",    "name": "删除购物车商品",   "group": "购物车"},
    {"id": "contact",        "name": "联系我们模块",     "group": "辅助"},
    {"id": "category",       "name": "分类筛选模块",     "group": "辅助"},
    {"id": "subscribe",      "name": "订阅模块",        "group": "辅助"},
]

# 成员中文名映射（用于 UI 展示）
OWNER_DISPLAY: dict[str, str] = {
    "siqi":    "乔思齐",
    "zhiyi":   "唐知怡",
    "yusheng": "曹宇声",
    "xupeng":  "沈徐鹏",
}

# Adapter 实例注册
ADAPTERS: dict[str, Adapter] = {
    "siqi":    SiqiAdapter(),
    "xupeng":  XupengAdapter(),
    "yusheng": YushengAdapter(),
    "zhiyi":   ZhiyiAdapter(),
}


def get_adapter(owner: str) -> Adapter:
    if owner not in ADAPTERS:
        raise KeyError(f"未知成员: {owner}")
    return ADAPTERS[owner]


__all__ = [
    "Adapter", "TestResult",
    "ADAPTERS", "MODULE_OWNER", "MODULE_META", "OWNER_DISPLAY",
    "get_adapter",
]
