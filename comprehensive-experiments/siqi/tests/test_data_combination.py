"""数据组合测试：搜索功能 25 组（pairwise 20 + 边界 5）。

数据来自 testdata/combinations.csv，由 scripts/generate_combinations.py 生成。
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from pages.product_list_page import ProductListPage
from pages.search_page import SearchPage

DATA_FILE = Path(__file__).resolve().parents[1] / "testdata" / "combinations.csv"


def _load_rows() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


_ROWS = _load_rows()


@pytest.mark.data_combo
@pytest.mark.parametrize(
    "row",
    _ROWS or [None],
    ids=[r["id"] for r in _ROWS] or ["MISSING_CSV"],
)
def test_data_combo_搜索关键词组合(page, row):
    """每组数据驱动一次搜索；actual_hit 与 expected_hit 一致则通过。"""
    if row is None:
        pytest.fail(
            f"找不到 {DATA_FILE}\n先跑: python scripts/generate_combinations.py"
        )

    expected_hit = row["expected_hit"].strip().lower() == "true"

    search = SearchPage(page)
    plist = ProductListPage(page)

    plist.open()
    search.search_input.fill(row["keyword"])
    search.search_button.click()

    # 有些边界输入（空串等）可能根本不触发搜索导航——容错处理
    try:
        search.searched_products_title.wait_for(timeout=5_000)
        actual_hit = search.result_count() > 0
    except Exception:
        actual_hit = False

    assert actual_hit == expected_hit, (
        f"{row['id']} keyword={row['keyword']!r} "
        f"expected={expected_hit} actual={actual_hit} ({row['note']})"
    )
