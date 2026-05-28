# 测试参数自定义说明

本项目支持在命令行自定义部分测试参数，不需要改代码。

## UI 测试（pytest）

### 可用参数

| 参数 | 默认值 | 类型 | 含义 |
|---|---|---|---|
| `--keyword` | `dress` | 字符串 | 搜索关键词 |
| `--product-index` | `0` | 整数 | 列表 / 搜索结果中的商品序号（从 0 开始） |

### 各用例受哪个参数影响

| 用例 | `--keyword` | `--product-index` |
|---|---|---|
| TC-Search-01（单元 / 搜索） | ✅ | — |
| TC-ProductList-01（单元 / 列表） | — | ✅（抽样验证名称和价格的商品序号） |
| TC-ProductDetail-01（单元 / 详情） | — | — |
| TC-Integration-Depth3-01 | ✅ | ✅（搜索后点击的结果序号） |
| TC-Integration-Depth4-01 | — | ✅（商品 A 序号；商品 B 自动取 `index+1`） |
| TC-Integration-Depth5-01 | ✅ | ✅（商品 A 序号；商品 B 自动取 `index+1`） |
| TC-DataCombination | — | —（关键词由 CSV 提供） |

### 使用示例

```powershell
# 不传参数 = 沿用默认值（dress / 0）
pytest -m unit
pytest -m integration

# 换搜索关键词
pytest -m unit --keyword=jeans

# 换商品序号（列表 / 结果第 3 个）
pytest -m unit --product-index=2

# 同时换关键词和序号
pytest -m integration --keyword=shirt --product-index=1

# 单跑某条集成用例
pytest tests/test_integration_depth5.py --keyword=top --product-index=0

# 查看参数（找到 --keyword / --product-index 两行）
pytest --help
```

### 注意事项

- `--keyword`：要保证关键词在 SUT 上至少能返回 `product_index + 2` 个结果，否则 depth4/5 会断言失败。
- `--product-index`：要在结果数范围内，序号越界会断言失败。
- 自定义参数不影响数据组合测试（其关键词从 `testdata/combinations.csv` 读取，要改组合请改 `scripts/generate_combinations.py` 后重新生成 CSV）。

## 性能测试（Locust）

并发数等参数走 Locust 内置 CLI，没有自定义脚本参数。

### 常用参数

| 参数 | 默认 | 含义 |
|---|---|---|
| `--users` | 120（任务规格要求） | 并发用户数 |
| `--spawn-rate` | 10 | 每秒新增用户数 |
| `--run-time` | 60s | 持续时长 |
| `--host` | locustfile 内置 `http://automationexercise.com` | 被测地址 |
| `--headless` | — | 无 Web UI，命令行直跑 |
| `--html` | — | 输出 HTML 报告路径 |

### 使用示例

```powershell
# 默认 120 并发（符合任务规格）
locust -f tests/performance/locustfile.py --users 120 --spawn-rate 10 --run-time 60s --headless --html reports/locust/report.html

# 50 并发
locust -f tests/performance/locustfile.py --users 50 --spawn-rate 10 --run-time 60s --headless --html reports/locust/report.html

# 200 并发
locust -f tests/performance/locustfile.py --users 200 --spawn-rate 20 --run-time 60s --headless --html reports/locust/report.html

# 全部 Locust 参数
locust --help
```

### 注意事项

- SLA 阈值（2 秒）和任务权重（列表:详情:搜索 = 3:2:1）写在 `tests/performance/locustfile.py` 里，不属于 CLI 自定义参数。要改请直接改文件。
- 并发数过高时本机可能跑不动，看 Locust 输出里有没有 "CPU usage above 90%" 警告。

## 参数实现位置

- pytest 参数注册：`conftest.py` 的 `pytest_addoption` + 两个 fixture（`keyword`、`product_index`）。
- Locust 参数：Locust 框架原生支持，`locustfile.py` 不需要额外代码。
