import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time


class TestIntegrationScenarios:
    @pytest.fixture(autouse=True)
    def setup(self):
        """初始化浏览器驱动；driver 由 Selenium Manager 自动管理，或 EDGE_DRIVER_PATH 指定。"""
        import os
        edge_options = Options()
        edge_options.add_argument("--disable-notifications")
        edge_options.add_argument("--disable-popup-blocking")
        # 仅当 SQA_HEADLESS=1（快速 demo 注入）时后台跑；默认可见，与原行为一致。
        _demo_headless = os.environ.get("SQA_HEADLESS") == "1"
        if _demo_headless:
            edge_options.add_argument("--headless=new")
            edge_options.add_argument("--window-size=1440,1000")
            edge_options.add_argument("--disable-gpu")
            # eager：DOM 可交互即返回，不死等广告/统计脚本等子资源——
            # 否则 headless 下 driver.get 在本站会长时间挂起（每次导航 30-60s+）。
            edge_options.page_load_strategy = "eager"

        edge_driver_path = os.environ.get("EDGE_DRIVER_PATH")
        if edge_driver_path and os.path.exists(edge_driver_path):
            service = Service(edge_driver_path)
            self.driver = webdriver.Edge(service=service, options=edge_options)
        else:
            self.driver = webdriver.Edge(options=edge_options)
        if _demo_headless:
            self.driver.set_page_load_timeout(40)   # 兜底：即便 eager 也不让单次导航无限挂起
        else:
            self.driver.maximize_window()
        self.driver.get("http://automationexercise.com")
        self.wait = WebDriverWait(self.driver, 15)
        time.sleep(3)
        yield
        self.driver.quit()

    def safe_click(self, element):
        """安全点击（使用JavaScript）"""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        self.driver.execute_script("arguments[0].click();", element)

    # ==================== 集成测试1：多商品购物车（深度5） ====================
    def test_integration_1_multi_items_cart(self):
        """
        路径深度：5层
        层1: 首页 → 层2: Women分类 → 层3: Dress子分类 → 层4: 添加商品1 → 层5: 验证购物车
        然后继续 → 层2: Men分类 → 层3: Tshirt子分类 → 层4: 添加商品2 → 层5: 验证购物车有2件
        """
        print("\n集成测试1：多商品购物车（深度5）")

        # 添加第1个商品（Women Dress）
        women_header = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Women')]")
        self.safe_click(women_header)
        time.sleep(1)

        dress_link = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Dress')]")
        self.safe_click(dress_link)
        time.sleep(2)

        first_product = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-image-wrapper")))
        first_product_name = first_product.find_element(By.CSS_SELECTOR, ".productinfo p").text
        print(f"  商品1: {first_product_name}")

        add_btn = first_product.find_element(By.CSS_SELECTOR, "a.btn.btn-default.add-to-cart")
        self.safe_click(add_btn)
        time.sleep(1)

        # 添加第2个商品（Men Tshirt）
        self.driver.get("http://automationexercise.com")
        time.sleep(2)

        men_header = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Men')]")
        self.safe_click(men_header)
        time.sleep(1)

        tshirt_link = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Tshirts')]")
        self.safe_click(tshirt_link)
        time.sleep(2)

        second_product = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-image-wrapper")))
        second_product_name = second_product.find_element(By.CSS_SELECTOR, ".productinfo p").text
        print(f"  商品2: {second_product_name}")

        add_btn2 = second_product.find_element(By.CSS_SELECTOR, "a.btn.btn-default.add-to-cart")
        self.safe_click(add_btn2)
        time.sleep(1)

        # 查看购物车并验证
        cart_link = self.driver.find_element(By.XPATH, "//a[contains(@href, 'view_cart')]")
        self.safe_click(cart_link)
        time.sleep(2)

        cart_items = self.driver.find_elements(By.CSS_SELECTOR, "#cart_info_table tbody tr")
        assert len(cart_items) >= 2, f"购物车商品数量不足: {len(cart_items)}"

        cart_text = self.driver.page_source
        assert first_product_name in cart_text, f"未找到: {first_product_name}"
        assert second_product_name in cart_text, f"未找到: {second_product_name}"

        print(f"  ✓ 购物车中有 {len(cart_items)} 件商品")
        print("✓ 集成测试1通过")

    # ==================== 集成测试2：搜索订阅（深度6） ====================
    def test_integration_2_search_filter_subscribe(self):
        """
        路径深度：6层
        层1: 首页 → 层2: Products页面 → 层3: 搜索Summer → 层4: 添加商品 → 层5: 订阅 → 层6: 验证成功
        """
        print("\n集成测试2：搜索订阅（深度6）")

        # 进入Products页面
        products_link = self.driver.find_element(By.XPATH, "//a[contains(@href, '/products')]")
        self.safe_click(products_link)
        time.sleep(2)

        # 搜索商品
        search_input = self.wait.until(EC.presence_of_element_located((By.ID, "search_product")))
        search_input.clear()
        search_input.send_keys("Summer")

        search_btn = self.driver.find_element(By.ID, "submit_search")
        self.safe_click(search_btn)
        time.sleep(2)

        # 验证搜索结果
        result_title = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Searched Products')]")
        assert result_title.is_displayed(), "搜索结果页面未加载"

        search_results = self.driver.find_elements(By.CSS_SELECTOR, ".product-image-wrapper")
        assert len(search_results) > 0, "搜索无结果"
        print(f"  ✓ 搜索到 {len(search_results)} 个商品")

        # 添加到购物车
        first_product = search_results[0]
        product_name = first_product.find_element(By.CSS_SELECTOR, ".productinfo p").text
        print(f"  商品: {product_name}")

        add_btn = first_product.find_element(By.CSS_SELECTOR, "a.btn.btn-default.add-to-cart")
        self.safe_click(add_btn)
        time.sleep(1)

        # 关闭可能出现的弹窗
        try:
            close_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'close-modal')]")
            self.safe_click(close_btn)
        except:
            pass

        # 订阅
        footer = self.driver.find_element(By.TAG_NAME, "footer")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", footer)
        time.sleep(1)

        # 先关闭页脚附近的广告
        try:
            ad_iframes = self.driver.find_elements(By.XPATH, "//div[@class='google-auto-placed']//iframe")
            for ad in ad_iframes:
                self.driver.execute_script("arguments[0].remove();", ad)
        except:
            pass

        subscribe_input = self.driver.find_element(By.ID, "susbscribe_email")
        subscribe_input.clear()
        test_email = f"test_{int(time.time())}@example.com"
        subscribe_input.send_keys(test_email)
        print(f"  ✓ 输入邮箱: {test_email}")

        subscribe_btn = self.driver.find_element(By.ID, "subscribe")
        self.safe_click(subscribe_btn)
        print("  ✓ 已点击订阅")
        time.sleep(2)

        # 验证订阅成功 - 使用多种方式查找成功提示
        success_found = False

        # 方式1：通过ID查找
        try:
            success_msg = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.ID, "success-subscribe"))
            )
            if "successfully subscribed" in success_msg.text.lower():
                success_found = True
                print(f"  ✓ 订阅成功: {success_msg.text}")
        except:
            pass

        # 方式2：通过class查找
        if not success_found:
            try:
                success_msg = self.driver.find_element(By.CSS_SELECTOR, ".alert-success")
                if "successfully subscribed" in success_msg.text.lower():
                    success_found = True
                    print(f"  ✓ 订阅成功: {success_msg.text}")
            except:
                pass

        # 方式3：检查页面源代码
        if not success_found:
            time.sleep(1)
            page_source = self.driver.page_source.lower()
            if "successfully subscribed" in page_source or "you have been successfully subscribed" in page_source:
                success_found = True
                print("  ✓ 订阅成功（通过页面源码验证）")

        assert success_found, "订阅未成功，未找到成功提示"

        print("✓ 集成测试2通过")
    # ==================== 集成测试3：品牌筛选加购删除（深度5） ====================
    def test_integration_3_brand_filter_cart_delete(self):
        """
        路径深度：5层
        层1: 首页 → 层2: 品牌筛选 → 层3: 添加商品 → 层4: 进入购物车 → 层5: 删除商品验证
        """
        print("\n集成测试3：品牌筛选加购删除（深度5）")

        # 品牌筛选
        brands_section = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "brands-name")))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", brands_section)
        time.sleep(1)

        brand_links = self.driver.find_elements(By.CSS_SELECTOR, ".brands-name a")
        assert len(brand_links) > 0, "未找到品牌"
        selected_brand = brand_links[0].text
        self.safe_click(brand_links[0])
        time.sleep(2)
        print(f"  ✓ 选择品牌: {selected_brand}")

        # 添加商品
        brand_products = self.wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".product-image-wrapper")
        ))
        assert len(brand_products) > 0, "品牌下无商品"

        first_product = brand_products[0]
        product_name = first_product.find_element(By.CSS_SELECTOR, ".productinfo p").text
        print(f"  商品: {product_name}")

        add_btn = first_product.find_element(By.CSS_SELECTOR, "a.btn.btn-default.add-to-cart")
        self.safe_click(add_btn)
        time.sleep(1)

        # 进入购物车
        cart_link = self.driver.find_element(By.XPATH, "//a[contains(@href, 'view_cart')]")
        self.safe_click(cart_link)
        time.sleep(2)

        # 删除商品
        delete_btn = self.driver.find_element(By.CSS_SELECTOR, ".cart_quantity_delete")
        self.safe_click(delete_btn)
        time.sleep(2)

        # 验证购物车为空
        cart_items = self.driver.find_elements(By.CSS_SELECTOR, "#cart_info_table tbody tr")
        page_text = self.driver.page_source.lower()

        assert len(cart_items) == 0 or "cart is empty" in page_text, "购物车未清空"
        print("  ✓ 购物车已清空")
        print("✓ 集成测试3通过")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])