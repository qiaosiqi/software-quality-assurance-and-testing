"""yusheng 性能测试（Locust）。

覆盖 yusheng 负责的 3 个模块相关端点：
  - 加购：       浏览商品列表 + 详情页（加购按钮所在页面）
  - 修改数量：   商品详情页（含 quantity 输入）
  - 删除：       view_cart 购物车页

启动（手动单跑）:
    locust -f load_test.py --host=https://automationexercise.com

通过 GUI 调用时，yusheng_interface.run_performance() 会附加 --headless 等。
"""
from locust import HttpUser, between, task


class YushengWebsiteUser(HttpUser):
    host = "https://automationexercise.com"
    wait_time = between(1, 3)

    @task(3)
    def products_listing(self):
        """商品列表（加购入口）。"""
        self.client.get("/products", name="products")

    @task(2)
    def product_detail(self):
        """商品详情（数量修改入口，product_id=1 是站点默认存在的样品）。"""
        self.client.get("/product_details/1", name="product_details")

    @task(2)
    def view_cart(self):
        """购物车页（删除入口）。"""
        self.client.get("/view_cart", name="view_cart")

    @task(1)
    def homepage(self):
        """首页（加购按钮的另一个入口）。"""
        self.client.get("/", name="homepage")
