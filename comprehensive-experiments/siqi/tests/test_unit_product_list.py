"""商品列表模块单测。"""
import pytest

from pages.product_list_page import ProductListPage


@pytest.mark.unit
def test_product_list_01_列表正常展示(page, product_index):
    """TC-ProductList-01：进入 /products 后列表可见，且抽样商品（默认序号 0，可通过 --product-index 自定义）有名称和价格。"""
    plist = ProductListPage(page)
    plist.open()

    assert plist.all_products_title.is_visible()
    assert plist.product_cards.count() > product_index
    assert plist.card_name(product_index).strip() != ""
    assert plist.card_price(product_index).strip().startswith("Rs.")
