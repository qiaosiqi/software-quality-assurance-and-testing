"""集成测试组合白名单。

UI 5 个下拉框（深度 1~5，深度 4/5 可空）拼出一个模块 id tuple；
后端按 tuple 精确匹配本表，命中就调对应 runner。

目标 4 成员 × 3 路径 = 12 条；当前只有 siqi 3 条，其他 9 条等组员补 adapter。
"""
from __future__ import annotations

from typing import Optional

# key 是模块 id tuple（不带末尾的空值），value 是 runner 描述
# runner 格式：(owner, method_name, kwargs_dict)
IntegrationKey = tuple[str, ...]
IntegrationRunner = tuple[str, str, dict]

INTEGRATION_CATALOG: dict[IntegrationKey, dict] = {
    # ---- siqi（已实现）----
    ("product_list", "search", "product_detail"): {
        "owner": "siqi",
        "depth": 3,
        "label": "列表 → 搜索 → 详情",
        "runner": ("siqi", "run_integration", {"depth": 3}),
    },
    ("product_list", "product_detail", "product_list", "product_detail"): {
        "owner": "siqi",
        "depth": 4,
        "label": "列表 → 详情A → 列表 → 详情B",
        "runner": ("siqi", "run_integration", {"depth": 4}),
    },
    ("product_list", "search", "product_detail", "product_list", "product_detail"): {
        "owner": "siqi",
        "depth": 5,
        "label": "列表 → 搜索 → 详情A → 列表 → 详情B",
        "runner": ("siqi", "run_integration", {"depth": 5}),
    },

    # ---- xupeng（已实现）----
    # 路径1（深度5）：Women/Dress 加购 → Men/Tshirt 加购 → 验证购物车
    ("category", "cart_add", "category", "cart_add", "cart_qty"): {
        "owner": "xupeng",
        "depth": 5,
        "label": "Women/Dress 加购 → Men/Tshirt 加购 → 验证购物车",
        "runner": ("xupeng", "run_integration", {"depth": 5, "path": 1}),
    },
    # 路径2（深度6）：Products → 搜索 Summer → 加购 → 订阅 → 验证
    # tuple 用 4 个核心模块（前端 5 槽够用），depth 写真实深度 6
    ("product_list", "search", "cart_add", "subscribe"): {
        "owner": "xupeng",
        "depth": 6,
        "label": "Products → 搜索 → 加购 → 订阅（含验证 6 层）",
        "runner": ("xupeng", "run_integration", {"depth": 6, "path": 2}),
    },
    # 路径3（深度5）：品牌筛选 → 加购 → 进入购物车 → 删除 → 验证清空
    ("category", "cart_add", "cart_qty", "cart_remove"): {
        "owner": "xupeng",
        "depth": 5,
        "label": "品牌筛选 → 加购 → 购物车 → 删除",
        "runner": ("xupeng", "run_integration", {"depth": 5, "path": 3}),
    },

    # ---- yusheng（已实现）----
    # Flow1（深度5）：登录 → 加购 → 进入购物车 → 删除 → 验证
    ("login", "cart_add", "cart_qty", "cart_remove"): {
        "owner": "yusheng",
        "depth": 5,
        "label": "登录 → 加购 → 购物车 → 删除",
        "runner": ("yusheng", "run_integration", {"depth": 5, "path": 1}),
    },
    # Flow2（深度5）：商品列表 → 详情 → 修改数量 → 加购 → 验证
    ("product_list", "product_detail", "cart_qty", "cart_add"): {
        "owner": "yusheng",
        "depth": 5,
        "label": "商品详情 → 修改数量 → 加购 → 校验",
        "runner": ("yusheng", "run_integration", {"depth": 5, "path": 2}),
    },
    # Flow3（深度5）：商品列表 → 搜索 → 加购 → 购物车 → 删除
    ("product_list", "search", "cart_add", "cart_remove"): {
        "owner": "yusheng",
        "depth": 5,
        "label": "搜索 → 加购 → 购物车 → 删除",
        "runner": ("yusheng", "run_integration", {"depth": 5, "path": 3}),
    },

    # ---- zhiyi（已实现，2 条路径）----
    # 路径A（深度4）：注册 → 登出 → 正确登录 → 登出
    ("register", "logout", "login", "logout"): {
        "owner": "zhiyi",
        "depth": 4,
        "label": "注册 → 登出 → 正确登录 → 登出",
        "runner": ("zhiyi", "run_integration", {"depth": 4, "path": 1}),
    },
    # 路径B（深度5）：注册 → 登出 → 错误登录 → 正确登录 → 登出
    ("register", "logout", "login", "login", "logout"): {
        "owner": "zhiyi",
        "depth": 5,
        "label": "注册 → 登出 → 错误登录 → 正确登录 → 登出",
        "runner": ("zhiyi", "run_integration", {"depth": 5, "path": 1}),
    },
}


def normalize_slots(slots: list[Optional[str]]) -> IntegrationKey:
    """去掉末尾的空值/None，返回前缀 tuple；中间不允许出现空值。"""
    # 去尾部 None / ""
    while slots and not slots[-1]:
        slots = slots[:-1]
    # 中间不允许空
    for i, s in enumerate(slots):
        if not s:
            raise ValueError(f"深度 {i+1} 不能留空（只允许末尾留空）")
    return tuple(slots)


def lookup(slots: list[Optional[str]]) -> Optional[dict]:
    """slots 是 5 长度（可能含 None）。返回 catalog 条目或 None。"""
    try:
        key = normalize_slots(list(slots))
    except ValueError:
        return None
    return INTEGRATION_CATALOG.get(key)


def list_available() -> list[dict]:
    """列出全部已实现组合（给前端折叠区用）。"""
    return [
        {
            "modules": list(key),
            "depth": v["depth"],
            "owner": v["owner"],
            "label": v["label"],
        }
        for key, v in INTEGRATION_CATALOG.items()
    ]
