"""商品搜索模块单测。"""
import pytest

from pages.search_page import SearchPage


@pytest.mark.unit
def test_search_01_关键词命中商品(page):
    """TC-Search-01：输入存在的关键词 'dress'，应返回至少 1 个商品。"""
    search = SearchPage(page)
    search.search("dress")

    assert search.searched_products_title.is_visible()
    assert search.result_count() > 0
