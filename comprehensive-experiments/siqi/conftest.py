"""根 conftest：playwright 浏览器/页面 fixture + 失败自动截图。"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

import config

SCREENSHOT_DIR = Path(__file__).parent / "reports" / "screenshots"


def pytest_addoption(parser):
    # 注意：option name 不能用 "keyword"，否则 dest 与 pytest 内置 -k 冲突，
    # 导致 --keyword=xxx 被当成 -k 过滤表达式，所有用例被 deselect。
    parser.addoption(
        "--keyword", default="dress", dest="siqi_keyword",
        help="搜索关键词（单元搜索 / 集成深度3、5 使用）",
    )
    parser.addoption(
        "--product-index", type=int, default=0, dest="siqi_product_index",
        help="列表 / 搜索结果中的商品序号（从 0 开始）",
    )


@pytest.fixture
def keyword(request) -> str:
    return request.config.getoption("siqi_keyword")


@pytest.fixture
def product_index(request) -> int:
    return request.config.getoption("siqi_product_index")


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=config.HEADLESS,
            slow_mo=config.SLOW_MO_MS,
        )
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser) -> Page:
    context = browser.new_context(base_url=config.BASE_URL)
    page = context.new_page()
    page.set_default_timeout(config.DEFAULT_TIMEOUT_MS)
    page.set_default_navigation_timeout(config.NAV_TIMEOUT_MS)
    yield page
    context.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call" or not rep.failed:
        return
    page = item.funcargs.get("page")
    if page is None:
        return
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    target = SCREENSHOT_DIR / f"{ts}_{item.name}_FAIL.png"
    try:
        page.screenshot(path=str(target), full_page=True)
    except Exception:
        pass
