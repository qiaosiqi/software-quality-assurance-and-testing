"""数据组合测试（yusheng）。

把 test_cart_module.TestCartModule.test_search_data_combination 中 for 循环跑的
25 个 keyword 拆成 pytest parametrize，方便 GUI 逐条展示 PASS/FAIL。

不直接 import 主测试模块——主模块的 HtmlTestRunner / unittest 入口跟 pytest 模式有冲突。
"""
from __future__ import annotations

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 25 条数据组合（id 与 keyword 来自原 test_search_data_combination 中的 keywords 顺序）
DATA_CASES: list[tuple[str, str, str]] = [
    ("YS01", "top",       "服饰品类"),
    ("YS02", "shirt",     "服饰品类"),
    ("YS03", "jean",      "服饰品类（部分词）"),
    ("YS04", "dress",     "服饰品类"),
    ("YS05", "blue",      "颜色"),
    ("YS06", "red",       "颜色"),
    ("YS07", "green",     "颜色"),
    ("YS08", "men",       "人群"),
    ("YS09", "women",     "人群"),
    ("YS10", "kids",      "人群"),
    ("YS11", "cotton",    "材质"),
    ("YS12", "winter",    "季节"),
    ("YS13", "summer",    "季节"),
    ("YS14", "fashion",   "风格"),
    ("YS15", "sport",     "风格"),
    ("YS16", "tshirt",    "服饰品类"),
    ("YS17", "jacket",    "服饰品类"),
    ("YS18", "saree",     "服饰品类"),
    ("YS19", "stylish",   "风格"),
    ("YS20", "soft",      "材质"),
    ("YS21", "beautiful", "形容词"),
    ("YS22", "jeans",     "服饰品类"),
    ("YS23", "clothes",   "通用词"),
    ("YS24", "trend",     "风格"),
    ("YS25", "sale",      "促销词"),
]


@pytest.fixture(scope="module")
def driver():
    drv = webdriver.Chrome()
    drv.maximize_window()
    yield drv
    drv.quit()


@pytest.mark.parametrize(
    "case_id,keyword,note",
    DATA_CASES,
    ids=[case[0] for case in DATA_CASES],
)
def test_search_data_combo(driver, case_id, keyword, note):
    """对每个 keyword 跑一次 /products 搜索，断言搜索结果页正常返回（含 body 标签）。

    对齐 yusheng 主测试的最低断言（不强制结果数量）。
    """
    wait = WebDriverWait(driver, 10)
    driver.get("http://automationexercise.com/products")
    search = wait.until(EC.presence_of_element_located((By.ID, "search_product")))
    search.clear()
    search.send_keys(keyword)
    driver.find_element(By.ID, "submit_search").click()
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print(f"[{case_id}] keyword={keyword!r} ({note}) - search submitted")
