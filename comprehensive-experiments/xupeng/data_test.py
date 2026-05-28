
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time


class TestSearchProductsDataCombination:
    """搜索功能 数据组合测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        import os
        edge_options = Options()
        edge_options.add_argument("--disable-notifications")
        edge_options.add_argument("--disable-popup-blocking")
        edge_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        edge_driver_path = os.environ.get("EDGE_DRIVER_PATH")
        if edge_driver_path and os.path.exists(edge_driver_path):
            service = Service(executable_path=edge_driver_path)
            self.driver = webdriver.Edge(service=service, options=edge_options)
        else:
            self.driver = webdriver.Edge(options=edge_options)

        self.driver.maximize_window()
        self.driver.get("http://automationexercise.com/products")
        self.wait = WebDriverWait(self.driver, 8)
        time.sleep(0.8)
        yield
        self.driver.quit()

    def safe_click(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.2)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except:
            return False

    # ====================== 核心：搜索功能 ======================
    def search_product(self, keyword):
        """执行搜索操作"""
        try:
            search_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "search_product"))
            )
            search_btn = self.driver.find_element(By.ID, "submit_search")

            search_input.clear()
            search_input.send_keys(keyword)
            self.safe_click(search_btn)
            time.sleep(0.8)
            print(f"✓ 已搜索关键词: {keyword}")
            return True
        except Exception as e:
            print(f"搜索失败: {e}")
            return False

    def get_searched_product_count(self):
        """获取搜索后的商品数量"""
        try:
            products = self.driver.find_elements(By.CLASS_NAME, "product-image-wrapper")
            visible = [p for p in products if p.is_displayed()]
            return len(visible)
        except:
            return 0

    # 25组搜索测试数据（真实有效关键词 + 组合）
    @pytest.mark.parametrize("keyword, expected_min, test_id", [
        # 正常有效关键词 8组
        ("dress", 1, "TS001"),
        ("top", 1, "TS002"),
        ("jeans", 1, "TS003"),
        ("shirt", 1, "TS004"),
        ("saree", 1, "TS005"),
        ("tshirt", 1, "TS006"),
        ("cotton", 1, "TS007"),
        ("women", 1, "TS008"),

        # 大小写混合 4组
        ("Dress", 1, "TS009"),
        ("JEANS", 1, "TS010"),
        ("Top", 1, "TS011"),
        ("Shirt", 1, "TS012"),

        # 部分关键词 4组
        ("dre", 1, "TS013"),
        ("jean", 1, "TS014"),
        ("shi", 1, "TS015"),
        ("sar", 1, "TS016"),

        # 重复稳定性测试 5组
        ("dress", 1, "TS017"),
        ("jeans", 1, "TS018"),
        ("top", 1, "TS019"),
        ("tshirt", 1, "TS020"),
        ("saree", 1, "TS021"),

        # 边界/特殊组合 4组
        ("men", 1, "TS022"),
        ("girl", 1, "TS023"),
        ("soft", 1, "TS024"),
        ("white", 1, "TS025"),
    ])
    def test_search_product_combinations(self, keyword, expected_min, test_id):
        """搜索功能 25组数据组合测试"""
        start_time = time.time()
        print(f"\n{'=' * 50}")
        print(f"[{test_id}] 搜索关键词: {keyword}")

        # 执行搜索
        success = self.search_product(keyword)
        assert success, f"搜索失败: {keyword}"

        # 获取结果
        count = self.get_searched_product_count()
        elapsed = time.time() - start_time

        print(f"搜索结果商品数: {count} | 耗时: {elapsed:.2f}s")
        assert count >= expected_min, f"关键词 [{keyword}] 未搜索到商品"
        print(f"✓ [{test_id}] 测试通过")
        print(f"{'=' * 50}")



class TestSearchFast:
    @pytest.fixture(autouse=True)
    def setup(self):
        import os
        edge_options = Options()
        edge_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        edge_driver_path = os.environ.get("EDGE_DRIVER_PATH")
        if edge_driver_path and os.path.exists(edge_driver_path):
            service = Service(executable_path=edge_driver_path)
            self.driver = webdriver.Edge(service=service, options=edge_options)
        else:
            self.driver = webdriver.Edge(options=edge_options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 6)
        yield
        self.driver.quit()

    def search(self, word):
        try:
            self.driver.get("http://automationexercise.com/products")
            search = self.wait.until(EC.presence_of_element_located((By.ID, "search_product")))
            btn = self.driver.find_element(By.ID, "submit_search")
            search.clear()
            search.send_keys(word)
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.6)
            return True
        except:
            return False

    @pytest.mark.parametrize("keyword", [
        "dress", "jeans", "top", "tshirt", "saree",
        "shirt", "cotton", "women", "men", "girl"
    ])
    def test_fast_search(self, keyword):
        print(f"\n快速搜索: {keyword}")
        assert self.search(keyword)
        count = len(self.driver.find_elements(By.CLASS_NAME, "product-image-wrapper"))
        print(f"商品数: {count}")
        assert count >= 1


def print_summary():
    print("=" * 70)
    print("Search Products 数据组合测试")
    print("测试页面: http://automationexercise.com/products")
    print("测试组数: 25 组")
    print("覆盖类型: 正常词 / 大小写 / 部分词 / 稳定性 / 边界词")
    print("=" * 70)


if __name__ == "__main__":
    print_summary()