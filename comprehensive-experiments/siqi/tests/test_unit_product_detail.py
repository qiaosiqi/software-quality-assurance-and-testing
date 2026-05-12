"""商品详情模块单测。"""
import pytest

from pages.product_detail_page import ProductDetailPage


@pytest.mark.unit
def test_product_detail_01_详情字段齐全(page):
    """TC-ProductDetail-01：进入商品 1 的详情页，关键字段可见。"""
    detail = ProductDetailPage(page)
    detail.open_for_product(1)

    assert detail.name.is_visible()
    assert detail.category.is_visible()
    assert detail.price.is_visible()
    assert detail.availability.is_visible()
    assert detail.condition.is_visible()
    assert detail.brand.is_visible()
