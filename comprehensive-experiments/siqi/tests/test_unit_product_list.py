"""商品列表模块单测。"""
import pytest

from pages.product_list_page import ProductListPage


@pytest.mark.unit
def test_product_list_01_列表正常展示(page):
    """TC-ProductList-01：进入 /products 后列表可见，且至少 1 个商品有名称和价格。"""
    plist = ProductListPage(page)
    plist.open()

    assert plist.all_products_title.is_visible()
    assert plist.product_cards.count() > 0
    assert plist.card_name(0).strip() != ""
    assert plist.card_price(0).strip().startswith("Rs.")
