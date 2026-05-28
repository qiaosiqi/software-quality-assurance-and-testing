"""xupeng 性能测试（Locust）。

覆盖 xupeng 负责的 3 个模块的 HTTP 端点：
  - 联系我们：GET /contact_us
  - 分类筛选：GET /category_products/1 (Women→Dress)、/category_products/6 (Men→Jeans)
  - 订阅：    GET /  （订阅表单在首页页脚，POST /subscribe_email 表单提交）

启动（命令行单独跑）：
    locust -f load_test.py --host=https://automationexercise.com

通过 GUI 调用时，xupeng_interface.run_performance() 会附加 --headless 等参数。
"""
from locust import HttpUser, between, task


class XupengWebsiteUser(HttpUser):
    host = "https://automationexercise.com"
    wait_time = between(1, 3)

    @task(3)
    def contact_us_page(self):
        """联系我们页面加载（含上传表单 HTML）。"""
        self.client.get("/contact_us", name="contact_us")

    @task(2)
    def category_women_dress(self):
        """Women→Dress 分类商品页。"""
        self.client.get("/category_products/1", name="category_women_dress")

    @task(2)
    def category_men_jeans(self):
        """Men→Jeans 分类商品页。"""
        self.client.get("/category_products/6", name="category_men_jeans")

    @task(2)
    def subscribe_via_homepage(self):
        """订阅模块入口（页脚），先取首页拿到表单 token，再 POST 订阅邮箱。

        如果站点不接受跨源 POST，则只统计 GET / 的负载即可，PUT/POST 失败计入 failure_rate。
        """
        self.client.get("/", name="homepage")
        # 站点的订阅端点是 POST /subscribe_email
        self.client.post(
            "/subscribe_email",
            data={"email": "loadtest@example.com"},
            name="subscribe_email",
            catch_response=True,
        )
