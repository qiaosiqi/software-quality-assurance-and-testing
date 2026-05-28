"""集成测试：路径深度 3 — 列表 → 搜索 → 详情。"""
import pytest

from pages.product_detail_page import ProductDetailPage
from pages.product_list_page import ProductListPage
from pages.search_page import SearchPage


@pytest.mark.integration
@pytest.mark.depth3
def test_integration_depth3_搜索后进入商品详情(page, keyword, product_index):
    """TC-Integration-Depth3-01：列表页→搜索关键词→点击结果进入详情。
    关键词与商品序号可通过 --keyword / --product-index 自定义。"""
    plist = ProductListPage(page)
    search = SearchPage(page)
    detail = ProductDetailPage(page)

    # 节点1：商品列表模块 —— 打开 /products
    plist.open()
    assert plist.all_products_title.is_visible()
    assert plist.product_cards.count() > 0

    # 节点2：商品搜索模块 —— 输入关键词并提交
    search.search_input.fill(keyword)
    search.search_button.click()
    assert search.searched_products_title.is_visible()
    assert search.result_count() > product_index

    # 节点3：商品详情模块 —— 点击指定序号的搜索结果进入详情
    plist.view_product_link(product_index).click()
    assert detail.name.is_visible()
    assert detail.price.is_visible()
