"""automationexercise.com 商品列表页 Page Object。"""
from __future__ import annotations

from playwright.sync_api import Locator

from .base import BasePage


class ProductListPage(BasePage):
    url_path = "/products"

    @property
    def all_products_title(self) -> Locator:
        return self.page.locator("h2.title.text-center", has_text="All Products")

    @property
    def product_cards(self) -> Locator:
        return self.page.locator(".features_items .product-image-wrapper")

    def card(self, index: int) -> Locator:
        return self.product_cards.nth(index)

    def card_name(self, index: int) -> str:
        return self.card(index).locator(".productinfo p").inner_text()

    def card_price(self, index: int) -> str:
        return self.card(index).locator(".productinfo h2").inner_text()

    def view_product_link(self, index: int) -> Locator:
        return self.card(index).locator(".choose a[href*='/product_details/']")
