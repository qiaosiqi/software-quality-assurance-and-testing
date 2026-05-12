"""生成数据组合测试的 25 组数据 = pairwise (20) + 边界 (5)。

用法：python scripts/generate_combinations.py
输出：testdata/combinations.csv，被 tests/test_data_combination.py 消费。
"""
from __future__ import annotations

import csv
from pathlib import Path

from allpairspy import AllPairs

OUT = Path(__file__).resolve().parents[1] / "testdata" / "combinations.csv"

# pairwise 输入：4 个维度，5×4=20 → AllPairs 输出恰好 20 组
KEYWORDS = ["dress", "shirt", "top", "jeans", "noresult123"]
CASES = ["lower", "upper", "title", "mixed"]
WHITESPACES = ["clean", "leading", "trailing"]
LENGTHS = ["full", "partial"]

KNOWN_HITS = {"dress", "shirt", "top", "jeans"}

# 手工补的 5 组边界用例
EDGE_CASES = [
    ("", False, "空字符串"),
    ("12345", False, "纯数字"),
    ("!@#$%", False, "纯符号"),
    ("<script>x</script>", False, "HTML 标签注入"),
    ("a" * 200, False, "超长字符串"),
]


def derive_keyword(root: str, case: str, ws: str, length: str) -> str:
    w = root
    if length == "partial":
        w = w[: max(1, len(w) // 2)]
    if case == "upper":
        w = w.upper()
    elif case == "title":
        w = w.title()
    elif case == "mixed":
        w = "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(w))
    if ws == "leading":
        w = "  " + w
    elif ws == "trailing":
        w = w + "  "
    return w


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    idx = 1
    for root, case, ws, length in AllPairs([KEYWORDS, CASES, WHITESPACES, LENGTHS]):
        rows.append({
            "id": f"DC-{idx:02d}",
            "keyword": derive_keyword(root, case, ws, length),
            "expected_hit": root in KNOWN_HITS,
            "note": f"pairwise:{root}/{case}/{ws}/{length}",
        })
        idx += 1
    for kw, hit, note in EDGE_CASES:
        rows.append({
            "id": f"DC-{idx:02d}",
            "keyword": kw,
            "expected_hit": hit,
            "note": f"边界:{note}",
        })
        idx += 1

    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "keyword", "expected_hit", "note"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"已生成 {len(rows)} 组到 {OUT}")


if __name__ == "__main__":
    main()
