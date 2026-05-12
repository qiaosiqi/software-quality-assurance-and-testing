"""所有 Page Object 的基类。"""
from __future__ import annotations

from playwright.sync_api import Page


class BasePage:
    url_path: str = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self) -> None:
        self.page.goto(self.url_path, wait_until="domcontentloaded")
