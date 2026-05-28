"""集成测试：路径深度 4 — 列表 → 详情 A → 回列表 → 详情 B。"""
import pytest

from pages.product_detail_page import ProductDetailPage
from pages.product_list_page import ProductListPage


@pytest.mark.integration
@pytest.mark.depth4
def test_integration_depth4_列表与详情来回切换(page, product_index):
    """TC-Integration-Depth4-01：列表→详情A→回到列表→详情B，且 A、B 商品不同。
    商品 A 序号通过 --product-index 自定义（默认 0），商品 B 取下一个序号。"""
    plist = ProductListPage(page)
    detail = ProductDetailPage(page)

    idx_a = product_index
    idx_b = product_index + 1

    # 节点1：商品列表模块 —— 打开列表
    plist.open()
    assert plist.product_cards.count() > idx_b

    # 节点2：商品详情模块 —— 点序号为 idx_a 的商品
    plist.view_product_link(idx_a).click()
    assert detail.name.is_visible()
    name_a = detail.name.inner_text().strip()

    # 节点3：商品列表模块 —— 浏览器后退回列表
    page.go_back(wait_until="domcontentloaded")
    assert plist.all_products_title.is_visible()

    # 节点4：商品详情模块 —— 点序号为 idx_b 的商品
    plist.view_product_link(idx_b).click()
    assert detail.name.is_visible()
    name_b = detail.name.inner_text().strip()

    assert name_a != name_b, f"两次进入的应是不同商品，但都是 {name_a!r}"
