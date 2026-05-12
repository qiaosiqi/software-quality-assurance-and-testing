# 性能测试 — Locust

针对 `automationexercise.com` 的并发性能测试。**不走 pytest**，独立运行，与 UI 测试隔离。

## 测试配置

| 项 | 值 |
|---|---|
| 并发用户 | **120** |
| 单请求 SLA | **2 秒**（超出标记为 failure） |
| 任务比例 | 商品列表 : 商品详情 : 商品搜索 = 3 : 2 : 1 |
| 用户思考间隔 | 0.5 ~ 2 秒（随机） |

## 运行方式

### Headless：60 秒、直接出报告

```powershell
locust -f tests/performance/locustfile.py `
       --users 120 --spawn-rate 10 --run-time 60s `
       --headless --html reports/locust/report.html
```

跑完看 `reports/locust/report.html`。

### 交互模式：可视化看流量上升

```powershell
locust -f tests/performance/locustfile.py
```

浏览器打开 <http://localhost:8089> → 填 `Number of users = 120`、`Spawn rate = 10` → Start。
观察后手动 Stop，Web UI 里能下载 CSV 报告。

## 报告关键指标

- **# Failures** — 包含 HTTP 错误码 + 超过 2 秒 SLA 的请求
- **Median / 95% / 99% Response Time** — 看长尾延迟
- **Requests/s** — 实际吞吐量
- **Failure rate** — 综合健康度

## 三类任务说明

- `GET /products` — 商品列表渲染
- `GET /product_details/[id]` — 商品详情页（随机挑 ID 1/2/3/5/10/20）
- `POST /products (search)` — 提交搜索表单，关键词在 dress/shirt/top/jeans 里随机
