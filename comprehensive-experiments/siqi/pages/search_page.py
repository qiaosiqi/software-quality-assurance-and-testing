"""automationexercise.com 的商品搜索页 Page Object。"""
from __future__ import annotations

from playwright.sync_api import Locator

from .base import BasePage


class SearchPage(BasePage):
    url_path = "/products"

    @property
    def search_input(self) -> Locator:
        return self.page.locator("#search_product")

    @property
    def search_button(self) -> Locator:
        return self.page.locator("#submit_search")

    @property
    def result_items(self) -> Locator:
        return self.page.locator(".features_items .product-image-wrapper")

    @property
    def searched_products_title(self) -> Locator:
        return self.page.locator("h2.title.text-center", has_text="Searched Products")

    def search(self, keyword: str) -> None:
        self.open()
        self.search_input.fill(keyword)
        self.search_button.click()

    def result_count(self) -> int:
        return self.result_items.count()
