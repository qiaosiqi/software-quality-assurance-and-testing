"""把 INTEGRATION_CATALOG 全量组合 dump 到 UI/docs/integration_paths.md。

为什么用脚本生成而不直接维护 markdown：
- INTEGRATION_CATALOG 是后端真实白名单，markdown 只是给人看的备查清单
- 每次往 catalog 加新组合后跑一遍 `python scripts/dump_integration_paths.py`，保证同步

用法（UI 目录下）:
    .venv/Scripts/python.exe scripts/dump_integration_paths.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# 让 import 找到 server 包
UI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(UI_ROOT))

from server.adapters import MODULE_META, OWNER_DISPLAY  # noqa: E402
from server.adapters.integration_catalog import INTEGRATION_CATALOG  # noqa: E402


def _module_zh(mod_id: str) -> str:
    for m in MODULE_META:
        if m["id"] == mod_id:
            return m["name"]
    return mod_id


def render() -> str:
    lines: list[str] = [
        "# 集成测试已实现组合一览",
        "",
        "> 本文件由 `UI/scripts/dump_integration_paths.py` 自动生成。",
        "> 每次往 `UI/server/adapters/integration_catalog.py` 加新组合后重跑一遍。",
        "",
        f"共 **{len(INTEGRATION_CATALOG)}** 条组合，按成员分组：",
        "",
    ]

    # 按 owner 分组
    by_owner: dict[str, list[tuple[tuple[str, ...], dict]]] = {}
    for key, val in INTEGRATION_CATALOG.items():
        by_owner.setdefault(val["owner"], []).append((key, val))

    for owner in ("siqi", "xupeng", "yusheng", "zhiyi"):
        if owner not in by_owner:
            continue
        owner_zh = OWNER_DISPLAY.get(owner, owner)
        rows = by_owner[owner]
        lines.append(f"## {owner_zh}（{owner}）")
        lines.append("")
        for key, val in sorted(rows, key=lambda r: (r[1]["depth"], r[1]["label"])):
            mod_names = " → ".join(_module_zh(m) for m in key)
            lines.append(f"- **深度 {val['depth']}**（{mod_names}）：{val['label']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 下拉框模块 id ↔ 中文名对照")
    lines.append("")
    for m in MODULE_META:
        lines.append(f"- `{m['id']}` → {m['name']}（{m['group']}）")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    out_path = UI_ROOT / "docs" / "integration_paths.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = render()
    out_path.write_text(content, encoding="utf-8")
    print(f"[dump] wrote {len(INTEGRATION_CATALOG)} combos to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
