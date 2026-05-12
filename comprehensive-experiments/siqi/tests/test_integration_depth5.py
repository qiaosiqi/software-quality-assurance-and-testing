"""集成测试：路径深度 5 — 列表 → 搜索 → 详情 A → 回结果 → 详情 B。"""
import pytest

from pages.product_detail_page import ProductDetailPage
from pages.product_list_page import ProductListPage
from pages.search_page import SearchPage


@pytest.mark.integration
@pytest.mark.depth5
def test_integration_depth5_搜索结果中切换两次详情(page):
    """TC-Integration-Depth5-01：列表→搜索→详情A→回到搜索结果→详情B。"""
    plist = ProductListPage(page)
    search = SearchPage(page)
    detail = ProductDetailPage(page)

    # 节点1：商品列表模块
    plist.open()
    assert plist.all_products_title.is_visible()

    # 节点2：商品搜索模块 —— 搜索关键词
    search.search_input.fill("top")
    search.search_button.click()
    assert search.searched_products_title.is_visible()
    assert search.result_count() >= 2, "至少要 2 个结果才能切两次详情"

    # 节点3：商品详情模块 —— 第一个结果
    plist.view_product_link(0).click()
    assert detail.name.is_visible()
    name_a = detail.name.inner_text().strip()

    # 节点4：回到搜索结果（仍是商品列表模块的搜索态）
    page.go_back(wait_until="domcontentloaded")
    assert search.searched_products_title.is_visible()

    # 节点5：商品详情模块 —— 第二个结果
    plist.view_product_link(1).click()
    assert detail.name.is_visible()
    name_b = detail.name.inner_text().strip()

    assert name_a != name_b, f"两次进入的应是不同商品，但都是 {name_a!r}"
