# siqi 模块说明

> 本文档面向**后续协作者（人 + Claude）**，尤其是上层 GUI 的开发。
> GUI 侧不需要关心 siqi 内部如何实现，只需要会用 `siqi_interface.py` 暴露的接口。

## 角色 / 任务 / 状态

- **角色**：综合实验组成员
- **任务**：完成综合实验的成员任务，详见本目录 `myTask.md`
- **完成状态**：已完成全部自动化测试（单元 / 集成 / 数据组合 / 性能）和统一接口，待 GUI 集成

## 测试覆盖

被测站点：**http://automationexercise.com**（公开 demo 电商站，无需登录）

| 模块 | 测试方法 | 用例数 |
|---|---|---|
| 商品列表 / 商品详情 / 商品搜索 三个模块 | 单元（pytest + Playwright） | 3 |
| 集成路径深度 3 / 4 / 5 | 集成（pytest + Playwright） | 3 |
| 搜索关键词组合 | 数据组合（pairwise 20 + 边界 5） | 25 |
| 站点高并发能力 | 性能（Locust） | 1（120 并发 / 60s / 2s SLA） |

技术栈：Python + Playwright (sync) + pytest + pytest-html + Locust + allpairspy。详见 `requirements.txt`。

---

## 公共接口：`siqi_interface.py`

GUI **只需要 import 它**，不要直接调 pytest / locust / scripts。

```python
from siqi_interface import (
    # 运行测试
    run_unit, run_integration,
    generate_combinations, run_data_combination,
    run_performance,
    # 元数据 / 默认值
    list_test_cases, get_default_params,
    # 返回类型
    TestResult,
)
```

所有运行函数同步阻塞返回 `TestResult`；GUI **必须**在工作线程（如 QThread / threading.Thread）里调用，否则 UI 会冻。

### 1. `run_unit(module="all", *, keyword=None, product_index=None) -> TestResult`

| 参数 | 类型 | 默认 | 取值 |
|---|---|---|---|
| `module` | str | `"all"` | `"search"`, `"product_list"`, `"product_detail"`, `"all"` |
| `keyword` | str \| None | None（→ `dress`） | 任意字符串；只影响 search |
| `product_index` | int \| None | None（→ 0） | ≥ 0；只影响 product_list |

### 2. `run_integration(depth="all", *, keyword=None, product_index=None) -> TestResult`

| 参数 | 类型 | 默认 | 取值 |
|---|---|---|---|
| `depth` | int \| str | `"all"` | `3`, `4`, `5`, `"all"` |
| `keyword` | str \| None | None（→ `dress`） | depth3、depth5 用 |
| `product_index` | int \| None | None（→ 0） | depth3/4/5 都用；depth4/5 中第二个商品取 `index + 1` |

> **越界注意**：自定义 `product_index` 时要保证关键词命中的结果数 ≥ `product_index + 2`（深度 4、5 切两次详情），否则用例断言失败。

### 3. `generate_combinations() -> Path`

单独重新生成 `testdata/combinations.csv`（25 组）。返回 CSV 绝对路径。

### 4. `run_data_combination(*, regenerate=False) -> TestResult`

跑数据组合测试。`regenerate=True` 强制重新生成 CSV；CSV 不存在时也会自动生成。

### 5. `run_performance(*, users=120, spawn_rate=10, run_time="60s") -> TestResult`

| 参数 | 类型 | 默认 | 取值 |
|---|---|---|---|
| `users` | int | 120 | 并发用户数，正整数 |
| `spawn_rate` | int | 10 | 每秒新增用户数，正整数 |
| `run_time` | str | `"60s"` | Locust 时间语法：`"60s"` / `"3m"` / `"1h"` |

> 任务规格要求 120 并发 + 2s SLA。SLA 阈值与任务权重（列表:详情:搜索 = 3:2:1）写在 `tests/performance/locustfile.py`，不属于 CLI 自定义参数。

### 6. `list_test_cases() -> dict`

返回所有可用测试场景的元数据，供 GUI 渲染测试列表 / 表单。结构：

```python
{
    "unit": {
        "search":          {"id": "TC-Search-01",        "name": "商品搜索单元测试",    "node": "...", "supports": ["keyword"]},
        "product_list":    {"id": "TC-ProductList-01",   "name": "商品列表单元测试",    "node": "...", "supports": ["product_index"]},
        "product_detail":  {"id": "TC-ProductDetail-01", "name": "商品详情单元测试",    "node": "...", "supports": []},
    },
    "integration": {
        3: {"id": "TC-Integration-Depth3-01", "name": "集成深度3：列表→搜索→详情",            "supports": ["keyword", "product_index"]},
        4: {"id": "TC-Integration-Depth4-01", "name": "集成深度4：列表→详情A→回退→详情B",    "supports": ["product_index"]},
        5: {"id": "TC-Integration-Depth5-01", "name": "集成深度5：列表→搜索→详情A→回退→详情B","supports": ["keyword", "product_index"]},
    },
    "data_combination": {"id": "TC-DataCombination",  "name": "数据组合测试（25 组）", "supports": ["regenerate"]},
    "performance":      {"id": "TC-Performance-01",   "name": "性能测试（Locust）",   "supports": ["users", "spawn_rate", "run_time"]},
}
```

GUI 可按 `supports` 字段决定渲染哪些输入控件。

### 7. `get_default_params() -> dict`

```python
{
    "unit":             {"module": "all",  "keyword": "dress", "product_index": 0},
    "integration":      {"depth": "all",   "keyword": "dress", "product_index": 0},
    "data_combination": {"regenerate": False},
    "performance":      {"users": 120,     "spawn_rate": 10,   "run_time": "60s"},
}
```

GUI 表单初始化用。

### 8. `TestResult` 数据结构

```python
@dataclass
class TestResult:
    name: str               # 中文名，例如 "单元测试[search]"
    success: bool           # 子进程 exit code == 0
    passed: int             # pytest: 通过用例数（性能测试恒为 0）
    failed: int             # pytest: 失败用例数（性能测试恒为 0）
    skipped: int
    duration_sec: float
    report_path: str | None # HTML 报告绝对路径；不存在为 None
    raw_output: str         # 完整 stdout+stderr，供日志窗口展示
    extra: dict             # 模块特定字段，见下表

    def to_dict(self) -> dict: ...
```

`extra` 字段表：

| 测试 | extra 包含 |
|---|---|
| 单元 / 集成 | `module` / `depth`、`keyword`、`product_index` |
| 数据组合 | `csv_path`、`regenerated` |
| 性能 | `users`、`spawn_rate`、`run_time`、`total_requests`、`total_failures`、`failure_rate_percent`、`aggregated_raw` |

> 性能测试若 Locust 输出格式异常，`extra` 里只会少几个字段，但 `success` / `raw_output` 仍可用。

---

## GUI 集成模式

### 在工作线程里跑（必须）

```python
import threading
from siqi_interface import run_unit

def on_run_clicked():
    def worker():
        result = run_unit(module="search", keyword="jeans")
        # 回到主线程更新 UI（PyQt 用 signal；tkinter 用 after()）
        update_ui(result)
    threading.Thread(target=worker, daemon=True).start()
```

### 打开 HTML 报告

```python
import os
if result.report_path:
    os.startfile(result.report_path)   # Windows
    # 跨平台：webbrowser.open(f"file:///{result.report_path}")
```

### 通用结果展示

```python
def update_ui(r: TestResult):
    status_label.text = "✅ 通过" if r.success else "❌ 失败"
    summary_label.text = f"通过 {r.passed} / 失败 {r.failed} / 跳过 {r.skipped}  · {r.duration_sec}s"
    log_textbox.text = r.raw_output
    if r.report_path:
        open_report_btn.enabled = True
    # 性能测试额外展示
    if "total_requests" in r.extra:
        perf_card.text = (
            f"总请求 {r.extra['total_requests']} · "
            f"失败 {r.extra['total_failures']} "
            f"({r.extra.get('failure_rate_percent', 0):.2f}%)"
        )
```

### 异常处理

| 调用 | 可能抛出 | 含义 |
|---|---|---|
| `run_unit(module=...)` | `ValueError` | module 取值不在合法集合 |
| `run_integration(depth=...)` | `ValueError` | depth 取值不在合法集合 |
| `run_performance(users=...)` | `ValueError` | users / spawn_rate 非正整数 |
| `generate_combinations()` | `RuntimeError` | 生成脚本执行失败（CSV 未产出） |

子进程内部失败（pytest 用例失败、Locust 超时等）**不会抛异常**——通过 `result.success == False` 和 `result.failed > 0` 判断。

### 报告路径约定

| 测试 | 报告路径 |
|---|---|
| `run_unit(module="search")` | `reports/html/unit_search.html` |
| `run_unit(module="all")` | `reports/html/unit_all.html` |
| `run_integration(depth=3)` | `reports/html/integration_depth3.html` |
| `run_integration(depth="all")` | `reports/html/integration_all.html` |
| `run_data_combination()` | `reports/html/data_combination.html` |
| `run_performance(users=120)` | `reports/locust/report_120users.html` |

不同参数的运行**不会互相覆盖**报告。

---

## 已知约束 / 当前未覆盖

| 项 | 现状 | 影响 |
|---|---|---|
| `HEADLESS` | 硬编码在 `config.py = False`，跑测试会弹浏览器窗口 | GUI 暂时无法控制是否无头；要支持需另开任务改 `config.py` 和接口签名 |
| 进度回调 | 无 | 子进程执行期间没有中间进度，GUI 只能显示"运行中"loading |
| 取消运行 | 无 | 一旦调用就跑完，不能中途打断；GUI 想做"取消"按钮需改成 `subprocess.Popen` + 杀进程 |
| 超时控制 | 无 | 浏览器卡死时函数会挂起；GUI 可自行用 `concurrent.futures` 包一层超时 |

如需要扩展上述能力，请先和用户确认范围，再修改 `siqi_interface.py`（不要让 GUI 直接调 pytest / locust 绕过统一接口）。

---

## 目录与文件参考

```
siqi/
├── siqi_interface.py       ← GUI 入口（本文档主角）
├── config.py               ← 全局常量（BASE_URL / HEADLESS / 超时 …）
├── conftest.py             ← pytest fixture + --keyword / --product-index 选项
├── pytest.ini              ← pytest 配置 + markers
├── pages/                  ← Page Object（GUI 不要直接 import）
├── tests/                  ← pytest 用例（GUI 不要直接调）
│   └── performance/locustfile.py
├── scripts/generate_combinations.py
├── testdata/combinations.csv
├── reports/                ← 运行产物（gitignored）
│   ├── html/*.html
│   ├── locust/*.html
│   └── screenshots/        ← 失败自动截图
└── docs/
    ├── final_report.md
    ├── custom_parameters.md   ← 用户手动 CLI 跑测试时的参数说明
    ├── test_cases/TC-*.md
    ├── flowcharts/
    └── manual_screenshots/
```

GUI 开发只会用到本文档列出的 `siqi_interface.py` API，其他目录都是 siqi 内部实现细节。
