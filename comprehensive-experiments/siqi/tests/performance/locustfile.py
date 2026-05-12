"""automationexercise.com 性能测试。

并发：120 用户
SLA：单请求 < 2 秒（超过即标记为 failure）
任务比例：列表 : 详情 : 搜索 = 3 : 2 : 1

运行方式见同目录 README.md。
"""
import random

from locust import HttpUser, between, task

SLA_SECONDS = 2.0

KEYWORDS = ["dress", "shirt", "top", "jeans"]
PRODUCT_IDS = [1, 2, 3, 5, 10, 20]


class BrowseUser(HttpUser):
    host = "http://automationexercise.com"
    wait_time = between(0.5, 2.0)

    @task(3)
    def view_product_list(self):
        with self.client.get(
            "/products",
            catch_response=True,
            name="GET /products",
        ) as r:
            self._check_sla(r)

    @task(2)
    def view_product_detail(self):
        pid = random.choice(PRODUCT_IDS)
        with self.client.get(
            f"/product_details/{pid}",
            catch_response=True,
            name="GET /product_details/[id]",
        ) as r:
            self._check_sla(r)

    @task(1)
    def search_product(self):
        keyword = random.choice(KEYWORDS)
        with self.client.post(
            "/products",
            data={"search_product": keyword},
            catch_response=True,
            name="POST /products (search)",
        ) as r:
            self._check_sla(r)

    @staticmethod
    def _check_sla(response) -> None:
        if response.status_code >= 400:
            response.failure(f"HTTP {response.status_code}")
            return
        elapsed = response.elapsed.total_seconds()
        if elapsed > SLA_SECONDS:
            response.failure(f"超过 SLA {SLA_SECONDS}s: {elapsed:.2f}s")
