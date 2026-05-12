"""automationexercise.com 商品详情页 Page Object。"""
from __future__ import annotations

from playwright.sync_api import Locator

from .base import BasePage


class ProductDetailPage(BasePage):
    """url 由 product_id 决定，open() 走 open_for_product()。"""

    def open_for_product(self, product_id: int) -> None:
        self.page.goto(f"/product_details/{product_id}", wait_until="domcontentloaded")

    @property
    def info(self) -> Locator:
        return self.page.locator(".product-information")

    @property
    def name(self) -> Locator:
        return self.info.locator("h2").first

    @property
    def category(self) -> Locator:
        return self.info.locator("p", has_text="Category:")

    @property
    def price(self) -> Locator:
        return self.info.locator("span > span").first

    @property
    def availability(self) -> Locator:
        return self.info.locator("p", has_text="Availability:")

    @property
    def condition(self) -> Locator:
        return self.info.locator("p", has_text="Condition:")

    @property
    def brand(self) -> Locator:
        return self.info.locator("p", has_text="Brand:")
