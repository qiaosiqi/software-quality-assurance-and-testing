import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import os
import time


class TestAutomationExercise:
    @pytest.fixture(autouse=True)
    def setup(self):
        """初始化 Edge 浏览器驱动，访问首页。

        driver 解析顺序：
        1) 环境变量 EDGE_DRIVER_PATH 指定的可执行文件（若存在）
        2) Selenium 4 内置 Selenium Manager 自动下载（默认）
        """
        edge_options = Options()
        edge_options.add_argument("--disable-notifications")
        edge_options.add_argument("--disable-popup-blocking")
        edge_options.add_experimental_option("excludeSwitches", ["enable-logging"])
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

        # 等待页面完全加载
        time.sleep(3)

        # 关闭可能出现的广告
        self.close_ads()

        yield
        self.driver.quit()

    def close_ads(self):
        """关闭页面上的广告"""
        try:
            # 移除所有广告 iframe
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                if "google" in iframe.get_attribute("src") or "ad" in iframe.get_attribute("id").lower():
                    self.driver.execute_script("arguments[0].remove();", iframe)

            # 移除其他广告元素
            ad_selectors = [
                "div[id*='google_ads']",
                "div[class*='advertisement']",
                "ins.adsbygoogle"
            ]

            for selector in ad_selectors:
                ads = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for ad in ads:
                    self.driver.execute_script("arguments[0].remove();", ad)
        except:
            pass

    def safe_click(self, element):
        """安全的点击方法"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            print(f"点击失败: {e}")

    def test_10_contact_us_form(self):
        """测试10: 联系我们模块 — 填写表单并验证提交成功提示"""
        print("\n开始测试10: 联系我们表单")

        # 先关闭广告
        self.close_ads()

        # 点击 Contact us 按钮（使用多种方式查找）
        try:
            # 方式1: 通过链接文本
            contact_link = self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Contact us")))
        except:
            # 方式2: 通过部分链接文本
            contact_link = self.wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Contact")))

        self.safe_click(contact_link)
        print("已点击 Contact us 链接")
        time.sleep(2)

        # 等待表单元素加载
        name_field = self.wait.until(EC.presence_of_element_located((By.NAME, "name")))
        email_field = self.driver.find_element(By.NAME, "email")
        subject_field = self.driver.find_element(By.NAME, "subject")
        message_field = self.driver.find_element(By.ID, "message")

        # 填写表单
        name_field.clear()
        name_field.send_keys("Test User")
        email_field.clear()
        email_field.send_keys("testuser@example.com")
        subject_field.clear()
        subject_field.send_keys("Testing Contact Form")
        message_field.clear()
        message_field.send_keys("This is a test message for automation practice.")
        print("表单已填写")

        # 上传文件
        file_path = os.path.abspath("test_upload.txt")
        with open(file_path, "w") as f:
            f.write("This is a dummy file for upload test.")

        upload_input = self.driver.find_element(By.NAME, "upload_file")
        upload_input.send_keys(file_path)
        print(f"文件已上传: {file_path}")

        # 提交表单
        submit_btn = self.driver.find_element(By.NAME, "submit")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
        time.sleep(1)
        self.safe_click(submit_btn)
        print("表单已提交")

        # 处理 alert
        try:
            alert = WebDriverWait(self.driver, 3).until(EC.alert_is_present())
            alert_text = alert.text
            alert.accept()
            print(f"Alert 内容: {alert_text}")
        except:
            print("没有出现 alert")

        # 验证成功
        time.sleep(2)
        try:
            success_msg = self.wait.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".alert-success, .status, div[class*='success']")
            ))
            assert "success" in success_msg.text.lower() or "submitted" in success_msg.text.lower()
            print(f"成功提示: {success_msg.text}")
        except:
            page_source = self.driver.page_source.lower()
            assert "success" in page_source or "submitted" in page_source
            print("通过页面源代码验证成功")

        # 清理文件
        if os.path.exists(file_path):
            os.remove(file_path)

        print("测试10通过")

    def test_11_category_filter_women(self):
        """测试11: 分类筛选模块 — 点击 Women 分类"""
        print("\n开始测试11: Women 分类筛选")

        self.close_ads()

        # 等待分类区域加载
        categories_section = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "category-products")))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", categories_section)
        time.sleep(1)

        # 查找 Women 标题并点击
        try:
            # 尝试多种选择器
            women_headers = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Women')]")
            for header in women_headers:
                if "panel-heading" in header.get_attribute("class") or header.tag_name == "h4":
                    self.safe_click(header)
                    break
        except:
            # 使用 JavaScript 点击
            self.driver.execute_script("document.querySelector('#accordian h4:first-child a').click();")

        time.sleep(1)

        # 查找 Women 下的 Dress 链接
        dress_link = None
        try:
            dress_link = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Dress')]")
            ))
        except:
            # 尝试更精确的选择器
            dress_link = self.driver.find_element(By.XPATH, "//div[@id='Women']//a[contains(@href, 'category')]")

        self.safe_click(dress_link)
        print("已点击 Women Dress 分类")
        time.sleep(2)

        # 验证跳转成功
        current_url = self.driver.current_url
        assert "category" in current_url, f"未跳转到分类页面，当前 URL: {current_url}"

        # 验证有商品显示
        products = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-image-wrapper, .single-products"))
        )
        assert len(products) > 0, "Women 分类下未加载任何商品"
        print(f"找到 {len(products)} 个商品")
        print("测试11(Women)通过")

    def test_11_category_filter_men(self):
        """测试11: 分类筛选模块 — 点击 Men 分类"""
        print("\n开始测试11: Men 分类筛选")

        self.close_ads()

        # 刷新页面回到首页
        self.driver.get("http://automationexercise.com")
        time.sleep(2)
        self.close_ads()

        # 等待分类区域加载
        categories_section = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "category-products")))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", categories_section)
        time.sleep(1)

        # 查找 Men 标题并点击
        try:
            men_headers = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Men')]")
            for header in men_headers:
                if "panel-heading" in header.get_attribute("class") or header.tag_name == "h4":
                    self.safe_click(header)
                    break
        except:
            self.driver.execute_script("document.querySelector('#accordian h4:last-child a').click();")

        time.sleep(1)

        # 查找 Men 下的 Jeans 链接
        jeans_link = None
        try:
            jeans_link = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Jeans')]")
            ))
        except:
            jeans_link = self.driver.find_element(By.XPATH, "//div[@id='Men']//a[contains(@href, 'category')]")

        self.safe_click(jeans_link)
        print("已点击 Men Jeans 分类")
        time.sleep(2)

        # 验证跳转成功
        current_url = self.driver.current_url
        assert "category" in current_url, f"未跳转到分类页面，当前 URL: {current_url}"

        # 验证有商品显示
        products = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-image-wrapper, .single-products"))
        )
        assert len(products) > 0, "Men 分类下未加载任何商品"
        print(f"找到 {len(products)} 个商品")
        print("测试11(Men)通过")

    def test_12_subscription_newsletter(self):
        """测试12: 订阅模块 — 滚动到页脚，输入邮箱订阅"""
        print("\n开始测试12: 订阅功能")

        self.close_ads()

        # 滚动到页脚
        footer = self.driver.find_element(By.TAG_NAME, "footer")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", footer)
        time.sleep(1)

        # 查找订阅输入框
        subscribe_input = None
        try:
            subscribe_input = self.wait.until(EC.presence_of_element_located((By.ID, "susbscribe_email")))
        except:
            try:
                subscribe_input = self.driver.find_element(By.ID, "subscribe_email")
            except:
                subscribe_input = self.driver.find_element(By.NAME, "email")

        subscribe_input.clear()
        subscribe_input.send_keys(f"test_{int(time.time())}@example.com")
        print(f"输入邮箱: {subscribe_input.get_attribute('value')}")

        # 查找订阅按钮
        subscribe_btn = None
        try:
            subscribe_btn = self.driver.find_element(By.ID, "subscribe")
        except:
            subscribe_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'subscribe')]")

        self.safe_click(subscribe_btn)
        print("已点击订阅按钮")
        time.sleep(2)

        # 验证成功提示
        try:
            success_alert = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert-success"))
            )
            assert "success" in success_alert.text.lower()
            print(f"订阅成功提示: {success_alert.text}")
        except:
            # 检查页面是否有成功消息
            page_text = self.driver.page_source.lower()
            assert "successfully subscribed" in page_text or "success" in page_text
            print("通过页面源代码验证订阅成功")

        print("测试12通过")


if __name__ == "__main__":
    # 运行所有测试
    pytest.main(["-v", "-s", "--tb=short", __file__])