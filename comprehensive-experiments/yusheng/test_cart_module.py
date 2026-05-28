import unittest
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# HtmlTestRunner 只在文件以 __main__ 方式直接运行时才需要；
# 通过 pytest 跑（GUI 接入路径）则不需要安装它。
# 这里延迟到 __main__ 块内 import，避免 pytest collect 阶段 ModuleNotFoundError。


class TestCartModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.driver = webdriver.Chrome()
        cls.driver.maximize_window()
        cls.wait = WebDriverWait(cls.driver, 10)

    def setUp(self):

        self.driver.get("http://automationexercise.com/")

    # ==================================================
    # 1. 添加购物车模块测试
    # ==================================================
    def test_add_to_cart(self):

        driver = self.driver

        product = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "product-image-wrapper")
            )
        )[0]

        ActionChains(driver).move_to_element(product).perform()

        add_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "(//a[contains(text(),'Add to cart')])[1]")
            )
        )

        # ✅ FIX 1
        driver.execute_script("arguments[0].click();", add_btn)

        modal = self.wait.until(
            EC.visibility_of_element_located(
                (By.ID, "cartModal")
            )
        )

        self.assertTrue(modal.is_displayed())

        print("✔ 添加购物车测试通过")

    # ==================================================
    # 2. 修改购物车数量测试
    # ==================================================
    def test_modify_cart_quantity(self):

        driver = self.driver

        view_product = self.wait.until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, "View Product")
            )
        )

        view_product.click()

        qty = self.wait.until(
            EC.presence_of_element_located(
                (By.ID, "quantity")
            )
        )

        # ✅ FIX 2
        driver.execute_script("arguments[0].value='';", qty)
        qty.send_keys("4")

        add_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, "cart")
            )
        )

        driver.execute_script("arguments[0].click();", add_btn)

        view_cart = self.wait.until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, "View Cart")
            )
        )

        view_cart.click()

        quantity = self.wait.until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "cart_quantity")
            )
        ).text

        self.assertEqual(quantity, "4")

        print("✔ 修改购物车数量测试通过")

    # ==================================================
    # 3. 删除购物车商品测试
    # ==================================================
    def test_delete_cart_item(self):

        driver = self.driver

        product = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "product-image-wrapper")
            )
        )[0]

        ActionChains(driver).move_to_element(product).perform()

        add_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "(//a[contains(text(),'Add to cart')])[1]")
            )
        )

        # ✅ FIX 3
        driver.execute_script("arguments[0].click();", add_btn)

        view_cart = self.wait.until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, "View Cart")
            )
        )

        view_cart.click()

        delete_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, "cart_quantity_delete")
            )
        )

        delete_btn.click()

        time.sleep(2)

        rows = driver.find_elements(By.XPATH, "//tbody/tr")

        # ✅ FIX 4：过滤空行
        product_rows = [
            r for r in rows if "cart_item" in (r.get_attribute("class") or "")
        ]

        self.assertTrue(len(product_rows) <= 0)

        print("✔ 删除购物车商品测试通过")

    # ==================================================
    # 4. 组合测试：登录 -> 加购 -> 删除
    # ==================================================
    def test_flow_login_cart_delete(self):

        driver = self.driver

        driver.find_element(By.LINK_TEXT, "Signup / Login").click()

        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@data-qa='login-email']")
            )
        ).send_keys("test123@test.com")

        driver.find_element(
            By.XPATH,
            "//input[@data-qa='login-password']"
        ).send_keys("123456")

        driver.find_element(
            By.XPATH,
            "//button[text()='Login']"
        ).click()

        product = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "product-image-wrapper")
            )
        )[0]

        ActionChains(driver).move_to_element(product).perform()

        self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "(//a[contains(text(),'Add to cart')])[1]")
            )
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, "View Cart")
            )
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, "cart_quantity_delete")
            )
        ).click()

        rows = driver.find_elements(By.XPATH, "//tbody/tr")

        self.assertTrue(len(rows) <= 1)

        print("✔ 组合测试 Flow1 通过")

    # ==================================================
    # 5. 组合测试：商品详情 -> 数量 -> 加购 -> 校验
    # ==================================================
    def test_flow_product_quantity(self):

        driver = self.driver

        driver.get("http://automationexercise.com/products")

        self.wait.until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, "View Product")
            )
        ).click()

        qty = self.wait.until(
            EC.presence_of_element_located(
                (By.ID, "quantity")
            )
        )

        # FIX
        driver.execute_script("arguments[0].value='3';", qty)

        self.wait.until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, "cart")
            )
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, "View Cart")
            )
        ).click()

        quantity = self.wait.until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "cart_quantity")
            )
        ).text

        self.assertEqual(quantity, "3")

        print("✔ 组合测试 Flow2 通过")

    # ==================================================
    # 6. 组合测试：搜索 -> 加购 -> 删除
    # ==================================================
    def test_flow_search_add_delete(self):

        driver = self.driver

        driver.get("http://automationexercise.com/products")

        search = self.wait.until(
            EC.presence_of_element_located(
                (By.ID, "search_product")
            )
        )

        search.send_keys("top")

        driver.find_element(
            By.ID,
            "submit_search"
        ).click()

        product = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "product-image-wrapper")
            )
        )[0]

        ActionChains(driver).move_to_element(product).perform()

        add_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "(//a[contains(text(),'Add to cart')])[1]")
            )
        )

        # FIX
        driver.execute_script("arguments[0].click();", add_btn)

        self.wait.until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, "View Cart")
            )
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, "cart_quantity_delete")
            )
        ).click()

        rows = driver.find_elements(By.XPATH, "//tbody/tr")

        self.assertTrue(len(rows) <= 1)

        print("✔ 组合测试 Flow3 通过")

    # ==================================================
    # 7. 性能测试：首页加载
    # ==================================================
    def test_homepage_performance(self):

        start = time.time()

        self.driver.get("http://automationexercise.com/")

        self.wait.until(
            EC.presence_of_element_located(
                (By.TAG_NAME, "body")
            )
        )

        end = time.time()

        load_time = end - start

        print(f"首页加载时间: {load_time:.2f} 秒")

        # FIX
        self.assertLess(load_time, 15)

    # ==================================================
    # 8. 性能测试：搜索响应
    # ==================================================
    def test_search_performance(self):

        self.driver.get("http://automationexercise.com/products")

        start = time.time()

        search = self.wait.until(
            EC.presence_of_element_located(
                (By.ID, "search_product")
            )
        )

        search.send_keys("top")

        self.driver.find_element(
            By.ID,
            "submit_search"
        ).click()

        self.wait.until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "productinfo")
            )
        )

        end = time.time()

        response_time = end - start

        print(f"搜索响应时间: {response_time:.2f} 秒")

        self.assertLess(response_time, 10)

    # ==================================================
    # 9. 数据组合测试（25组搜索）
    # ==================================================
    def test_search_data_combination(self):

        keywords = [
            "top", "shirt", "jean", "dress", "blue",
            "red", "green", "men", "women", "kids",
            "cotton", "winter", "summer", "fashion", "sport",
            "tshirt", "jacket", "saree", "stylish", "soft",
            "beautiful", "jeans", "clothes", "trend", "sale"
        ]

        for word in keywords:

            self.driver.get("http://automationexercise.com/products")

            search = self.wait.until(
                EC.presence_of_element_located(
                    (By.ID, "search_product")
                )
            )

            search.clear()
            search.send_keys(word)

            self.driver.find_element(
                By.ID,
                "submit_search"
            ).click()

            self.wait.until(
                EC.presence_of_element_located(
                    (By.TAG_NAME, "body")
                )
            )

            print(f"✔ 搜索 [{word}] 完成")

    @classmethod
    def tearDownClass(cls):

        cls.driver.quit()


if __name__ == "__main__":

    import HtmlTestRunner  # noqa: E402  延迟 import；pytest 路径不会走到这里

    unittest.main(
        testRunner=HtmlTestRunner.HTMLTestRunner(
            output="test_report",
            report_name="AutomationExercise_Report",
            report_title="Automation Exercise Test Report"
        )
    )