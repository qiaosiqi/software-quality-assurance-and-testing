# 自选网站集成测试实验报告

| 项 | 内容 |
|---|---|
| 课程 | 软件质量保证与测试 |
| 实验名称 | 综合实验 — 自选网站集成测试 |
| 成员 | siqi |
| 被测网站 | <http://automationexercise.com> |
| 测试范围 | 商品列表、商品详情、商品搜索 三个模块 |
| 完成日期 | TODO |

---

## 一、实验环境

| 项 | 内容 |
|---|---|
| 操作系统 | Windows 11 |
| Python | TODO（`python --version`） |
| UI 自动化 | Playwright 1.40+（Chromium，sync API） |
| 测试运行器 | pytest 8.x + pytest-html |
| 性能测试 | Locust 2.x |
| 数据组合 | allpairspy（pairwise） |

完整依赖见 `requirements.txt`。

## 二、被测网站与模块

`automationexercise.com` 是一个面向自动化练习的公开 demo 电商站，无需登录即可访问浏览类功能。本次测试覆盖：

| 模块 | 入口 | 核心交互 |
|---|---|---|
| 商品列表 | `/products` | 浏览全部商品 |
| 商品详情 | `/product_details/<id>` | 查看单个商品详细信息 |
| 商品搜索 | `/products` + 搜索框 | 关键词搜索 |

## 三、测试设计与执行

### 3.1 单个模块测试（3 项）

| 用例 | 模块 | 文档 | 结果 |
|---|---|---|---|
| TC-Search-01 | 商品搜索 | [TC-Search.md](test_cases/TC-Search.md) | 通过 |
| TC-ProductList-01 | 商品列表 | [TC-ProductList.md](test_cases/TC-ProductList.md) | 通过 |
| TC-ProductDetail-01 | 商品详情 | [TC-ProductDetail.md](test_cases/TC-ProductDetail.md) | 通过 |

### 3.2 集成模块测试（3 项，路径深度 3 / 4 / 5）

| 用例 | 路径深度 | 节点 | 结果 |
|---|---|---|---|
| TC-Integration-Depth3-01 | 3 | 列表 → 搜索 → 详情 | 通过 |
| TC-Integration-Depth4-01 | 4 | 列表 → 详情 A → 回退 → 详情 B | 通过 |
| TC-Integration-Depth5-01 | 5 | 列表 → 搜索 → 详情 A → 回退 → 详情 B | 通过 |

详见 [TC-Integration.md](test_cases/TC-Integration.md)。

### 3.3 数据组合测试（1 项 / 25 组数据）

- 方法：**pairwise** 生成 20 组正交组合 + 5 组手工边界用例 = **25 组**
- 维度：关键词词根 / 大小写 / 空格位置 / 长度修剪
- 通过 **21** 组、未通过 **4** 组
- 未通过共性：**前导空格未被剥离**

详见 [TC-DataCombination.md](test_cases/TC-DataCombination.md)。

### 3.4 性能测试（1 项 / 120 并发 / 2s SLA）

| 指标 | 实测 | 期望 | 是否达成 |
|---|---|---|---|
| 总失败率 | 61.71% | 0% | 未达成 |
| 平均响应时间 | 2017 ms | < 2000 ms | 未达成 |
| p95 响应时间 | 2700 ms | < 2000 ms | 未达成 |
| 搜索端点失败率 | 100% | 0% | 未达成 |

详见 [TC-Performance.md](test_cases/TC-Performance.md)。

## 四、测试发现汇总

1. **搜索接口未对输入做 `lstrip`** —— 由数据组合测试发现，4/25 用例失败，全部为前导空格场景。
2. **120 并发下站点不可用** —— 总失败率 61.71%，搜索端点 100% 失败；存在明显请求排队（max 12 秒）。
3. **搜索是最弱端点** —— 单元 / 集成 / 数据组合 / 性能 四类测试中，搜索均暴露问题：组合输入处理粗糙、并发处理能力差。建议被测系统优先优化搜索逻辑（输入预处理 + 缓存）。
4. **基本功能稳定** —— 在单用户低负载下，三个模块的正常功能（列表、详情、有效关键词搜索）均通过。

## 五、运行方式

详见根目录 `README.md`，常用命令：

```powershell
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 生成 25 组数据组合
python scripts/generate_combinations.py

# 跑全部 UI 测试
pytest

# 跑性能测试
locust -f tests/performance/locustfile.py --users 120 --spawn-rate 10 --run-time 60s --headless --html reports/locust/report.html
```

## 六、附件清单

| 类型 | 位置 |
|---|---|
| 业务流程图 | `docs/test_cases/TC-*.md` 中 mermaid 嵌入 ; `docs/flowcharts/*.png`（如导出） |
| 测试用例文档 | `docs/test_cases/TC-*.md` |
| 自动化脚本 | `tests/`、`pages/`、`scripts/` |
| 人工复现截图 | `docs/manual_screenshots/` |
| pytest HTML 报告 | `reports/html/report.html`（重新跑一次产生） |
| Locust HTML 报告 | `reports/locust/report.html`（重新跑一次产生） |
| 数据组合 CSV | `testdata/combinations.csv` |
