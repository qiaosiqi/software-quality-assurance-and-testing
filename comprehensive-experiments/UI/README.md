# QualityHub 综合测试平台

软件质量保证与测试综合实验的统一编排与展示平台。系统已接入四位成员的测试实现，通过统一 adapter 协议封装 pytest、Playwright、Selenium、Locust、TestNG 与 Maven 等异构测试栈，并提供实时测试、历史记录、业务流程、运行监控和快速演示等完整功能。

设计细节见同目录 `ui_design.md`。

---

## 首次部署

### 1. 装依赖

```bat
cd UI
setup.bat
```

`setup.bat` 会：
- 创建 `UI/.venv` 独立虚拟环境
- 装 `requirements.txt` 全部 Python 依赖（FastAPI + Uvicorn + siqi 全套 Playwright/pytest/Locust）
- 装 Playwright Chromium 浏览器（首次约 100MB，几十秒到几分钟）

### 2. 启动

```bat
start.bat
```

会激活 venv、起 uvicorn 监听 `localhost:8000`，3 秒后自动开浏览器。

如果浏览器没开起来，手动访问 <http://localhost:8000/>。

---

## 页面导航

| 路径 | 说明 |
|---|---|
| `#/` | 入口页：小组信息 + 三大功能卡片 |
| `#/history` | 历史记录：时间倒序，可按时间/类别/成员筛选 |
| `#/live/unit` | 单元测试：12 模块卡片，点击选中后跑 |
| `#/live/integration` | 集成测试：5 个深度下拉，命中白名单才跑 |
| `#/live/data` | 数据组合：成员 tab + 25 行表 |
| `#/live/performance` | 性能测试：成员 tab + 动态参数表单 |
| `#/flowchart` | 业务流程图：SVG 全局业务流程 |
| `#/demo` | 快速演示：四位成员并行执行并生成汇总报告 |

---

## 视觉素材

前端引用以下静态资源（用户可直接替换同名文件，无需改代码）：

| 用途 | 文件路径 | 当前形式 |
|---|---|---|
| 团队 logo（入口页 banner 右上角） | `web/static/team_logo.svg` | 蓝紫圆形 + "SQAT 综合实验" |
| 历史记录卡片图标 | `web/static/icon_history.svg` | 钟表 + 倒流箭头 |
| 实时测试卡片图标 | `web/static/icon_live.svg` | 播放三角 + 红点 |
| 业务流程图卡片图标 | `web/static/icon_flowchart.svg` | 树状框图 |
| 业务流程图主图 | `web/static/flowchart.svg` | 完整业务流程总览 |

> 推荐尺寸：
> - 卡片图标 64×64（SVG/PNG 均可）
> - 团队 logo 90×90
> - 业务流程图主图 宽度 1024+ 像素

---

## 统一 adapter 接口

四位成员均已通过独立 adapter 接入。每个 adapter 将成员原有测试框架的调用方式转换为统一接口：

1. 在 `comprehensive-experiments/<member>/` 下提供 `<member>_interface.py`，对外暴露下列函数：

```python
run_unit(module: str, **kwargs) -> TestResult
run_integration(depth: int, **kwargs) -> TestResult
run_data_combination(**kwargs) -> TestResult
run_performance(**kwargs) -> TestResult
list_modules() -> list[str]      # 该成员负责的 3 个模块 id
list_test_cases() -> dict        # 元数据
get_default_params() -> dict     # 默认参数
list_data_cases() -> list[dict]  # 数据组合"待跑"表格行
```

`TestResult` 数据结构见 `server/adapters/base.py`。

2. 在 `server/adapters/<member>.py` 实现桥接层，调用该成员的 interface 模块。

3. 在 `server/adapters/__init__.py` 注册真实 adapter 实例。

4. 在 `server/adapters/integration_catalog.py` 录入该成员实现的集成路径（模块 id tuple → runner）。

刷新页面即可。无需重启 server 之外的步骤。

---

## 现场演示脚本（建议）

> 答辩约 10 分钟，按以下顺序演示，效果最佳。

1. **入口页**（30 秒）：介绍小组成员 + 三大功能模块。
2. **业务流程图**（30 秒）：让观众了解被测站点的业务全貌。
3. **实时测试 · 单元**（2 分钟）：
   - 点商品搜索卡片 → 改关键词为 `dress` → 跑 → Playwright 弹真浏览器自动化（卖点）→ 结果 ✅
   - 重点：让观众看到自动化操作过程。
4. **实时测试 · 集成**（2 分钟）：
   - 演示下拉选 `列表 → 搜索 → 详情`（命中提示 ✅）→ 跑。
   - 再随便乱选一个未实现组合 → 看 ❌ 提示效果。
5. **实时测试 · 性能**（2 分钟）：
   - 演示用 `users=30 / spawn_rate=10 / run_time=20s` 跑（完整规格 120/60s 留作"完整跑"展示选项；当场跑等不及）。
   - 结果：4 张指标卡片 + 报告链接。
6. **实时测试 · 数据组合**（1 分钟）：
   - 不真跑（25 组 ~3 分钟太久）。展示 25 行表格 + 讲解关键词构造逻辑（`combinations.csv` 的 pairwise + 边界用例）。
   - 如果时间够，先准备好的历史记录里挑一条跑过的展示结果。
7. **历史记录**（1 分钟）：
   - 翻出所有跑过的记录 → 展开看 raw_output。
   - 展示按类别 / 成员筛选。

---

## 已知约束

| 项 | 现状 | 缓解 |
|---|---|---|
| 同时只能跑一个测试 | 全局锁，第 2 个请求返回 409 | 演示按串行节奏 |
| Playwright 弹浏览器 | siqi `config.py: HEADLESS = False` | 现场演示卖点；离线用户接受即可 |
| 实时进度反馈 | 无（spinner 等到结束才出结果） | Phase 2 上 SSE 流式日志 |
| 历史报告 HTML 同名覆盖 | 报告路径固定，下一次跑覆盖上一次 | 历史记录里完整 `raw_output` 已存，足够回溯 |
| 历史记录不归档报告副本 | `history.json` 只存元数据 + 日志 | 见上 |
| 数据组合表逐行更新 | MVP 阶段一次性更新 | Phase 2 加 |

---

## 故障排查

### 跑测试报 `ModuleNotFoundError: No module named 'playwright'` / `No module named locust`

错误日志里 python 路径形如 `C:\Users\xxx\miniconda3\python.exe`（不是 `UI/.venv`）就是这个症状。

根因：你机器上有 miniconda / anaconda 等其他 Python，default `python` 命令解析到那个 base 环境；如果 `start.bat` 走的是 `call activate` + `python -m uvicorn` 这条路径，conda 的初始化脚本可能拦截 activate，导致 `python` 其实仍是 miniconda 的，而 miniconda base 没装 playwright / locust。

**已修**：

- `start.bat` / `setup.bat` 不再调用 `activate`，全部用 `.venv\Scripts\python.exe` 绝对路径调起。
- `adapters/siqi.py` 强制覆写 `siqi_interface.PYTHON = UI/.venv/Scripts/python.exe`，无论 uvicorn 自身用什么 python 启动，siqi 子进程都用 venv 的。

**自检**：访问 `http://localhost:8000/health`，看 `uvicorn_python` 和 `siqi_subprocess_python` 两个字段：
- `siqi_subprocess_python` **必须**指向 `UI/.venv/Scripts/python.exe`，否则跑测试肯定挂。
- `uvicorn_python` 理想情况也是 `.venv`，不一致会有 `[diagnostic] note:` 启动日志提示，但只要 siqi 那个对了就能跑。

### `pytest` 跑 siqi 测试出现 "1 deselected / 0 selected"

siqi 的 `conftest.py` 早期版本注册 `--keyword` 选项时未指定 `dest`，与 pytest 内置 `-k` 的 dest 冲突，导致 `--keyword=xxx` 被当成 `-k xxx` 过滤表达式，所有测试被 deselect。

修复：`conftest.py` 中 `parser.addoption("--keyword", ..., dest="siqi_keyword")`，对应 fixture 用 `getoption("siqi_keyword")`。已在当前仓库修复。

### 启动 `start.bat` 报 "未检测到 .venv"

先跑 `setup.bat`。

### 浏览器自动开了但显示"加载失败"

uvicorn 还没起来。等 3-5s 刷新一次浏览器。

### POST /api/run/* 卡很久

Playwright 跑测试本来就慢（10s 起）；性能测试更可能跑几十秒到几分钟。看控制台 uvicorn 输出能看到子进程实时日志。

### POST 返回 409 "已有测试在运行"

后端用全局锁防 Playwright/Locust 并发冲突。等当前测试跑完再点。

---

## 目录结构

```
UI/
├── README.md             ← 本文件
├── ui_design.md          ← 设计文档（SSOT）
├── setup.bat             ← 首次部署
├── start.bat             ← 日常启动
├── requirements.txt
├── .gitignore
├── .venv/                ← venv（gitignored）
├── server/
│   ├── main.py           ← FastAPI app + 所有 endpoint
│   ├── history.py        ← history.json 读写
│   ├── history.json      ← 历史记录（gitignored）
│   └── adapters/
│       ├── base.py       ← Adapter Protocol + TestResult
│       ├── siqi.py       ← 包装 siqi_interface
│       ├── placeholder.py← 可选的未接入成员降级模板
│       ├── zhiyi.py       ← Java/TestNG adapter
│       ├── yusheng.py     ← 购物车测试 adapter
│       ├── xupeng.py      ← 辅助功能测试 adapter
│       ├── integration_catalog.py
│       └── __init__.py   ← 12 模块清单 + 注册表
└── web/
    ├── index.html        ← SPA 壳
    └── static/
        ├── style.css
        ├── app.js        ← 路由 + 各页 view
        ├── team_logo.svg
        ├── icon_*.svg
        └── flowchart.svg ← 完整业务流程总览
```
