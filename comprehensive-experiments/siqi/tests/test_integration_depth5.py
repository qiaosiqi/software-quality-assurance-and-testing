"""集成测试：路径深度 5 — 列表 → 搜索 → 详情 A → 回结果 → 详情 B。"""
import pytest

from pages.product_detail_page import ProductDetailPage
from pages.product_list_page import ProductListPage
from pages.search_page import SearchPage


@pytest.mark.integration
@pytest.mark.depth5
def test_integration_depth5_搜索结果中切换两次详情(page, keyword, product_index):
    """TC-Integration-Depth5-01：列表→搜索→详情A→回到搜索结果→详情B。
    关键词与商品 A 序号可通过 --keyword / --product-index 自定义，商品 B 取下一个序号。"""
    plist = ProductListPage(page)
    search = SearchPage(page)
    detail = ProductDetailPage(page)

    idx_a = product_index
    idx_b = product_index + 1

    # 节点1：商品列表模块
    plist.open()
    assert plist.all_products_title.is_visible()

    # 节点2：商品搜索模块 —— 搜索关键词
    search.search_input.fill(keyword)
    search.search_button.click()
    assert search.searched_products_title.is_visible()
    assert search.result_count() > idx_b, "结果数需大于 idx_b 才能切两次详情"

    # 节点3：商品详情模块 —— 序号为 idx_a 的结果
    plist.view_product_link(idx_a).click()
    assert detail.name.is_visible()
    name_a = detail.name.inner_text().strip()

    # 节点4：回到搜索结果（仍是商品列表模块的搜索态）
    page.go_back(wait_until="domcontentloaded")
    assert search.searched_products_title.is_visible()

    # 节点5：商品详情模块 —— 序号为 idx_b 的结果
    plist.view_product_link(idx_b).click()
    assert detail.name.is_visible()
    name_b = detail.name.inner_text().strip()

    assert name_a != name_b, f"两次进入的应是不同商品，但都是 {name_a!r}"
