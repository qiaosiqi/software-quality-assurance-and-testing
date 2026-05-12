# siqi 综合实验 — 自动化测试

针对 `http://automationexercise.com/` 的自动化测试，覆盖**商品列表 / 商品详情 / 商品搜索**三个模块。详细任务规格见 `myTask.md`，分层与约定见 `CLAUDE.md`。

## 安装

```powershell
pip install -r requirements.txt
playwright install chromium
```

## 跑测试

```powershell
# 跑全部 UI 测试（pytest 默认不收 performance）
pytest

# 单个用例
pytest tests/test_unit_search.py::test_search_01_关键词命中商品

# 按 marker
pytest -m unit
pytest -m "integration and depth3"
pytest -m data_combo

# 性能测试（独立工具，不走 pytest）
locust -f tests/performance/locustfile.py
```

跑完产物：

- HTML 报告：`reports/html/report.html`
- 失败截图：`reports/screenshots/`

## 目录速览

```
config.py          全局常量（BASE_URL / 超时 / HEADLESS）
conftest.py        playwright fixture + 失败自动截图
pages/             Page Object（每页一个文件）
tests/             pytest 用例
testdata/          静态测试数据 + 25 组组合 CSV（committed）
docs/              交付物（流程图、人工截图、测试用例 md、最终报告）
reports/           运行产物（gitignore）
```

## 切换 headed / headless

平时开着 GUI 看浏览器自动操作，跑 CI 或多用例时改 `config.py` 的 `HEADLESS = True`、`SLOW_MO_MS = 0`。
