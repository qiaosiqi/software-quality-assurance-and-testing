# 综合实验 GUI 设计文档

> 跟踪用文档。本目录最终交付的"统一 GUI 入口"以本文件为单一事实源（SSOT），后续所有改动同步在这里更新。
>
> 上一次更新：2026-05-24（v3：所有待确认收口；准备进入 Phase 1 实施）
> 负责人：siqi（克宝）

---

## 0. 决策快照

| 项 | 决策 | 备注 |
|---|---|---|
| 顶层信息架构 | **入口页 → 三大功能模块** | 历史记录 / 实时测试 / 业务流程图 |
| 实时测试维度 | **以"测试类别"为第一维度** | 单元 / 集成 / 数据组合 / 性能 4 个子页 |
| 集成测试 UX | **看上去自由组合，命中白名单才跑** | 5 个深度下拉框，**允许同模块在不同深度重复**；未命中返回"组合不支持" |
| 数据组合 / 性能测试 UX | **顶部成员切换 tab** | 每人独立展示；性能测试参数按所选成员的 `get_default_params()` 动态渲染 |
| 装饰素材 | **路径占位，用户后续替换** | 入口页插画、业务流程图都引用 `web/static/` 下的占位文件 |
| 运行模型 | 纯实时跑 | 每次点按钮真去 subprocess 跑 pytest/Locust |
| 技术栈 | FastAPI + 原生 HTML/CSS/JS | 零构建、零 CDN；前端用 SPA 路由（hash 路由） |
| 历史持久化 | **JSON 索引文件**（`history.json`），报告 HTML 不归档 | 课程作业不上 SQLite |
| 浏览器弹窗 | 保留 Playwright 有头模式 | 现场演示卖点 |
| 实时日志 | SSE（Server-Sent Events） | Phase 2 加，Phase 1 先 spinner |
| 适配范围 | 先做 siqi，预留 3 个成员扩展位 | 同步给出接口契约文档 |
| 演示场景 | 现场答辩 + 离线提交双兼容 | `start.bat` 双击即起 |

---

## 1. 目标 / 非目标

### 1.1 目标

- **入口清晰**：一个首页三个入口，不让观众/老师在 tab 海里找东西。
- **实时启动**：实时测试页能真跑 pytest/Locust，参数可调、过程可见、结果可读。
- **历史可追**：每次跑完落地一条记录到本地 JSON，按时间倒序看，可按时间/类别筛选。
- **覆盖全员**：单元有 12 个模块候选（4×3），集成下拉框组合"看上去很丰富"，覆盖全员任务分工。
- **接口契约文档化**：让 zhiyi / xupeng / yusheng 后续补接口时知道"接什么形状的洞"。

### 1.2 非目标（明确否决）

- ❌ 用户登录 / 权限。
- ❌ 用 SQLite / 数据库；用一个 `history.json` 足够。
- ❌ 历史记录归档每次的 HTML 报告副本（只存元数据 + 文本日志 raw_output）。
- ❌ 移动端适配。
- ❌ 任何前端框架（React/Vue/Vite/Webpack），自己写原生 HTML/CSS/JS。
- ❌ 自己造测试报告页（直接 iframe 嵌入 pytest-html / locust 的产物）。
- ❌ 多任务并发跑（一次只能跑一个测试，避免 Playwright / Locust 资源冲突）。

---

## 2. 系统架构

```
┌──────────────────────────────────────────────────┐
│  浏览器（演示终端）                                  │
│  index.html  +  app.js  +  style.css             │
│  hash 路由：#/  #/history  #/live  #/flowchart   │
└─────────────────┬────────────────────────────────┘
                  │ HTTP/JSON + SSE
                  ▼
┌──────────────────────────────────────────────────┐
│  FastAPI 后端  (UI/server/main.py)                │
│  REST:                                            │
│    GET  /api/meta                  ← 12 模块/组员映射 │
│    GET  /api/integration/catalog   ← 已实现组合白名单 │
│    POST /api/run/unit              ← 跑单元         │
│    POST /api/run/integration       ← 跑集成         │
│    POST /api/run/data              ← 跑数据组合      │
│    POST /api/run/performance       ← 跑性能         │
│    GET  /api/history?from=&to=&category=          │
│    GET  /api/jobs/{job_id}/stream  ← SSE 实时日志   │
│  静态: /static, /reports/<member>/...             │
│  本地存储: history.json（每次跑完 append）          │
└─────────────────┬────────────────────────────────┘
                  │ Python 内部 import
                  ▼
┌──────────────────┴───────────────────────────────┐
│  适配层  UI/server/adapters/                      │
│  siqi.py     → import siqi.siqi_interface  ✅    │
│  zhiyi.py    → subprocess mvn test         🚧    │
│  xupeng.py   → 待实现                       🚧    │
│  yusheng.py  → 待实现                       🚧    │
└──────────────────────────────────────────────────┘
```

---

## 3. 数据模型与接口契约

### 3.1 12 个模块清单（单元测试候选）

| # | 业务分组 | 模块 ID | 模块名 | 负责成员 | 实现状态 |
|---|---|---|---|---|---|
| 1 | 账户 | `register` | 注册模块 | 唐知怡（zhiyi） | 🚧 |
| 2 | 账户 | `login` | 登录模块 | 唐知怡（zhiyi） | 🚧 |
| 3 | 账户 | `logout` | 登出模块 | 唐知怡（zhiyi） | 🚧 |
| 4 | 商品浏览 | `product_list` | 商品列表模块 | 乔思齐（siqi） | ✅ |
| 5 | 商品浏览 | `product_detail` | 商品详情模块 | 乔思齐（siqi） | ✅ |
| 6 | 商品浏览 | `search` | 商品搜索模块 | 乔思齐（siqi） | ✅ |
| 7 | 购物车 | `cart_add` | 添加购物车模块 | 曹宇声（yusheng） | 🚧 |
| 8 | 购物车 | `cart_qty` | 购物车数量修改模块 | 曹宇声（yusheng） | 🚧 |
| 9 | 购物车 | `cart_remove` | 删除购物车商品模块 | 曹宇声（yusheng） | 🚧 |
| 10 | 辅助 | `contact` | 联系我们模块 | 沈徐鹏（xupeng） | 🚧 |
| 11 | 辅助 | `category` | 分类筛选模块 | 沈徐鹏（xupeng） | 🚧 |
| 12 | 辅助 | `subscribe` | 订阅模块 | 沈徐鹏（xupeng） | 🚧 |

这份清单由后端 `/api/meta` 返回，前端用它渲染 12 张模块卡片 + 集成下拉框选项。

### 3.2 集成测试组合白名单

UX：5 个深度下拉框，每个选项 = 上述 12 个模块 + `（无）`，深度 4/5 允许为空，**允许同一模块在不同深度重复出现** → 拼出一个 tuple → 查白名单。

> 思路：**照着弹孔画靶**。后端只关心"这个 tuple 是否在白名单里"，命中就调对应 runner（组员代码已经能跑出该集成场景），未命中就报错。一共 4 成员 × 3 路径 = 12 条目标。当前白名单只有 siqi 的 3 条，其他 9 条待其他成员补 adapter。

```python
# UI/server/adapters/integration_catalog.py
INTEGRATION_CATALOG: dict[tuple[str, ...], dict] = {
    # siqi 已实现（深度3/4/5）
    ("product_list", "search", "product_detail"): {
        "owner": "siqi", "depth": 3,
        "runner": ("siqi", "run_integration", {"depth": 3}),
    },
    ("product_list", "product_detail", "product_list", "product_detail"): {
        "owner": "siqi", "depth": 4,
        "runner": ("siqi", "run_integration", {"depth": 4}),
    },
    ("product_list", "search", "product_detail", "product_list", "product_detail"): {
        "owner": "siqi", "depth": 5,
        "runner": ("siqi", "run_integration", {"depth": 5}),
    },
    # 其他成员未实现的组合在他们提交时补进来
    # ("register", "login", "logout"): {...},
}
```

匹配逻辑：
1. 前端发来 5 个槽位的列表（含 `null`），去掉末尾的 `null` 得到 tuple。
2. 后端按 tuple 查 `INTEGRATION_CATALOG`，命中就调对应 runner，未命中返回 `{ok: False, reason: "组合不支持，已实现组合: 列表→搜索→详情 / ..."}`。

> ⚠️ **"12 个已实现组合"如何凑齐**：当前 siqi 实现 3 条（深度 3/4/5）。要凑到 12 条，需要每位成员各实现 3 条。这点待跟其他成员对齐——见 §11 待确认。

### 3.3 Adapter 契约（给 zhiyi / xupeng / yusheng）

`<member>_interface.py` 必须提供：

| 函数 | 必须 | 返回 |
|---|---|---|
| `run_unit(module: str, **kw) -> TestResult` | ✅ | 跑单个模块单元测试 |
| `run_integration(depth: int, **kw) -> TestResult` | ✅ | 跑集成（用户也可以暴露按模块列表跑） |
| `run_data_combination(**kw) -> TestResult` | ✅ | 跑数据组合 |
| `run_performance(users, spawn_rate, run_time, **kw) -> TestResult` | ✅ | 跑性能 |
| `list_modules() -> list[str]` | ✅ | 我负责的 3 个模块 ID |
| `list_test_cases() -> dict` | ✅ | 元数据 |
| `get_default_params() -> dict` | ✅ | 默认参数 |

`TestResult` 必含字段见 `siqi/siqi_interface.py:97-110`，新版需多带一个 `started_at: str`（ISO8601）和 `params: dict` 给历史索引用。

跨语言适配（zhiyi 用 Java/Maven/TestNG）：在 `zhiyi/zhiyi_interface.py` 里 subprocess 调 mvn，解析 surefire 报告：

```python
def run_unit(module: str, **kw) -> TestResult:
    proc = subprocess.run(
        ["mvn", "-f", "automationexercise-selenium-testng/pom.xml",
         "test", f"-Dtest={pick_class(module)}"],
        capture_output=True, text=True, encoding="utf-8"
    )
    # 解析 target/surefire-reports/*.xml 得到 passed/failed
    ...
```

### 3.4 历史记录索引（`UI/server/history.json`）

```json
[
  {
    "id": "20260524-153012-a8c3",
    "started_at": "2026-05-24T15:30:12+08:00",
    "category": "unit",
    "case_name": "商品搜索单元测试",
    "case_id": "TC-Search-01",
    "owner": "siqi",
    "params": {"module": "search", "keyword": "dress"},
    "success": true,
    "passed": 1, "failed": 0, "skipped": 0,
    "duration_sec": 12.4,
    "report_path": "siqi/reports/html/unit_search.html",
    "raw_output": "...完整 stdout+stderr 原文..."
  },
  ...
]
```

- 每次跑完 append 一条；前端默认按 `started_at` 倒序展示。
- `report_path` 是相对仓库根的路径，前端拼成 `/reports/<member>/...` 访问。**注意**报告会被同名覆盖，所以历史里点"打开报告"看到的是该测试类型最近一次的内容。
- **完整 raw_output 都存进 JSON**（用户原话："跑过了就有输出，把输出存一下就好了"）；展开历史记录行可直接看到当时的完整日志。
- 文件超过 1000 条自动裁剪保留最近 1000 条（懒得加 pagination）。

---

## 4. 页面结构

**SPA + hash 路由**：单个 `index.html`，hash 切页面，无前端构建工具。

| 路由 | 页面 | 用途 |
|---|---|---|
| `#/`（默认） | 入口页 | 小组信息 + 三个功能入口 |
| `#/history` | 历史记录 | 时间排序、筛选 |
| `#/live` | 实时测试 | 4 类测试子页 |
| `#/flowchart` | 业务流程图 | 一张图占位 |

### 4.1 入口页 `#/`

```
┌─────────────────────────────────────────────────────────────┐
│  [ web/static/banner.png 装饰条 占位 ]                       │
│                                                             │
│         软件质量保证与测试 · 综合实验                          │
│         被测站点：automationexercise.com                     │
│                                                             │
│  [ web/static/team_logo.png ]                                │
│  组员：乔思齐（组长） / 唐知怡 / 沈徐鹏 / 曹宇声                │
│                                                             │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │ icon_hist    │  │ icon_live    │  │ icon_flow    │    │
│   │ .svg 占位     │  │ .svg 占位     │  │ .svg 占位     │    │
│   │  历史记录     │  │  实时测试     │  │  业务流程图    │    │
│   │ 时间排序回溯  │  │ 在线启动测试  │  │ 站点全局流程  │    │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│   底部小字：技术栈 / 上次更新时间 / 报告总数                   │
└─────────────────────────────────────────────────────────────┘
```

- 三张大卡片，hover 上浮+变色，点击切到对应 hash。
- 底部小字调 `/api/history?stats` 拿"累计跑了多少次"。

**装饰素材清单**（用户后续直接替换文件即可，前端引用路径写死）：

| 用途 | 文件路径 | 占位形式 |
|---|---|---|
| 顶部 banner | `web/static/banner.png` | 纯色矩形 SVG 占位 |
| 团队/课程 logo | `web/static/team_logo.png` | 文字 logo SVG 占位 |
| 历史记录卡片图标 | `web/static/icon_history.svg` | 简笔 SVG |
| 实时测试卡片图标 | `web/static/icon_live.svg` | 简笔 SVG |
| 业务流程图卡片图标 | `web/static/icon_flowchart.svg` | 简笔 SVG |

### 4.2 历史记录页 `#/history`

```
┌─────────────────────────────────────────────────────────────┐
│  ← 返回入口    历史记录                                       │
├─────────────────────────────────────────────────────────────┤
│  筛选： 时间 [2026-05-01 → 2026-05-24]                       │
│        类别 [全部 ▼] [单元] [集成] [数据] [性能]              │
│        成员 [全部 ▼] [siqi] [zhiyi] [xupeng] [yusheng]      │
├─────────────────────────────────────────────────────────────┤
│  时间               类别  用例                  结果  时长     │
│  2026-05-24 15:30  单元  TC-Search-01           ✅   12.4s   │
│  2026-05-24 15:25  集成  TC-Integration-D5      ❌   45.2s   │
│  2026-05-24 14:10  性能  TC-Performance-01       ✅   60.0s  │
│  ...                                                         │
│  （点行展开：参数 / 日志摘要 / 打开报告）                     │
└─────────────────────────────────────────────────────────────┘
```

- 默认显示最近 7 天；时间筛选器是两个 `<input type="date">`。
- 类别 / 成员可多选（chip 形式）。
- 表格每行可展开折叠：参数、`raw_output_excerpt`、"打开报告"按钮。
- 数据来源：`GET /api/history?from=&to=&category=&owner=`。

### 4.3 实时测试页 `#/live`

顶部 4 个 sub-tab（hash 二级：`#/live/unit` / `/integration` / `/data` / `/performance`）。

#### 4.3.1 单元测试 `#/live/unit`

```
┌─────────────────────────────────────────────────────────────┐
│  [单元] [集成] [数据] [性能]                                  │
├─────────────────────────────────────────────────────────────┤
│  账户                                                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ 注册模块    │ │ 登录模块    │ │ 登出模块    │              │
│  │ 唐知怡 🚧   │ │ 唐知怡 🚧   │ │ 唐知怡 🚧   │              │
│  └────────────┘ └────────────┘ └────────────┘              │
│  商品浏览                                                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ 商品列表    │ │ 商品详情    │ │ 商品搜索    │              │
│  │ 乔思齐 ✅   │ │ 乔思齐 ✅   │ │ 乔思齐 ✅   │              │
│  └────────────┘ └────────────┘ └────────────┘              │
│  购物车                                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ 添加购物车   │ │ 数量修改    │ │ 删除商品    │              │
│  │ 曹宇声 🚧   │ │ 曹宇声 🚧   │ │ 曹宇声 🚧   │              │
│  └────────────┘ └────────────┘ └────────────┘              │
│  辅助                                                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ 联系我们    │ │ 分类筛选    │ │ 订阅模块    │              │
│  │ 沈徐鹏 🚧   │ │ 沈徐鹏 🚧   │ │ 沈徐鹏 🚧   │              │
│  └────────────┘ └────────────┘ └────────────┘              │
├─────────────────────────────────────────────────────────────┤
│  右侧抽屉：参数表单（按选中模块的 supports 渲染）+ 跑结果 + 日志 │
└─────────────────────────────────────────────────────────────┘
```

- 12 张模块卡片，点击 = 选中。
- 选中后右侧抽屉拉出：模块标题 + 负责成员 + 参数表单（动态渲染） + 大按钮 `🚀 开始测试`。
- 🚧 卡片可点击但 disabled，hover 提示"等待 xxx 提交接口"。
- 跑完结果卡片在抽屉底部，含"打开报告"按钮。

#### 4.3.2 集成测试 `#/live/integration`

```
┌─────────────────────────────────────────────────────────────┐
│  集成路径组合                                                │
│  深度 1：[ 商品列表    ▼ ]                                   │
│  深度 2：[ 商品搜索    ▼ ]                                   │
│  深度 3：[ 商品详情    ▼ ]                                   │
│  深度 4：[（无）       ▼ ]                                   │
│  深度 5：[（无）       ▼ ]                                   │
│                                                             │
│  [ 🚀 运行此组合 ]                                           │
│                                                             │
│  ─ 命中提示 ─────────────────                                │
│  ✅ 已命中：列表 → 搜索 → 详情（深度 3，由 siqi 实现）         │
│  （未命中时显示：❌ 该组合暂未实现，已实现组合见下方列表）      │
│                                                             │
│  ─ 已实现组合一览（折叠） ─────                               │
│  • 列表 → 搜索 → 详情（深度 3，siqi）                         │
│  • 列表 → 详情 → 列表 → 详情（深度 4，siqi）                  │
│  • 列表 → 搜索 → 详情 → 列表 → 详情（深度 5，siqi）           │
│  • ...                                                      │
├─────────────────────────────────────────────────────────────┤
│  右侧：跑结果 + 日志                                          │
└─────────────────────────────────────────────────────────────┘
```

- 5 个 `<select>`，选项 = 12 个模块 + `（无）`。
- 实时校验：用户每改一次选择，前端立即向 `/api/integration/catalog` 比对（或前端缓存好白名单本地比对），头部显示"✅ 已命中 …" 或"❌ 未实现"。
- 点"运行"才真跑；未命中就 disable 按钮。
- 折叠的"已实现组合一览"让观众清楚地知道可以挑哪些组合演示。

#### 4.3.3 数据组合测试 `#/live/data`

```
┌─────────────────────────────────────────────────────────────┐
│  [ siqi ✅ ] [ zhiyi 🚧 ] [ xupeng 🚧 ] [ yusheng 🚧 ]      │
├─────────────────────────────────────────────────────────────┤
│  数据组合测试（25 组，pairwise 20 + 边界 5） · 负责成员：siqi  │
│  ☐ 重新生成 CSV   [ 🚀 跑全部 25 组 ]                        │
├─────────────────────────────────────────────────────────────┤
│  # | 关键词         | 期望      | 实际    | 结果              │
│  1 | dress         | 命中 > 0  | 14 件  | ✅                │
│  2 | TOP           | 命中 > 0  | 8 件   | ✅                │
│  3 | "  dress"     | 命中 > 0  | 0 件   | ❌（不 lstrip）   │
│  ...（25 行）                                                │
├─────────────────────────────────────────────────────────────┤
│  下方：通过率 84% (21/25) 图  +  失败用例汇总                 │
└─────────────────────────────────────────────────────────────┘
```

- **顶部成员切换 tab**：每人独立展示自己的数据组合测试，不同人的"测试用例数据"格式可能不同（关键词组合 / 表单字段组合 / ...），由各成员 adapter 自行决定表格列。
- siqi 当前实现：25 组关键词，列固定为 `编号 / 关键词 / 期望 / 实际 / 结果`。
- 表格上方按钮 + 复选框（控制 `regenerate`）。
- 跑前先调成员 adapter 的 `list_data_cases() -> list[dict]` 拿表格行展示（灰色 "待跑"）。
- 跑完逐行更新"实际/结果"列（MVP 阶段一次性更新，Phase 2 加 SSE 实时）。

#### 4.3.4 性能测试 `#/live/performance`

```
┌─────────────────────────────────────────────────────────────┐
│  [ siqi ✅ ] [ zhiyi 🚧 ] [ xupeng 🚧 ] [ yusheng 🚧 ]      │
├─────────────────────────────────────────────────────────────┤
│  性能测试 · 负责成员：siqi  · 工具：Locust                    │
│                                                             │
│  〔参数表单按当前成员的 get_default_params() 动态渲染〕         │
│  并发用户数  [  120 ]                                         │
│  每秒新增   [  10  ]                                         │
│  持续时长   [  60s ]                                         │
│  [ 🚀 开始压测 ]                                             │
├─────────────────────────────────────────────────────────────┤
│  跑完后展示：                                                 │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │ 总请求     │ │ 总失败     │ │ 失败率     │ │ p95 RT    │   │
│  │ 1,951     │ │ 1,204     │ │ 61.71%    │ │ 2.4s      │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│  [ 打开 HTML 报告 ]                                          │
└─────────────────────────────────────────────────────────────┘
```

- **顶部成员切换 tab**，同数据组合页。
- **参数表单完全由 adapter 驱动**：切换成员时前端重新拉 `list_test_cases()['performance']['supports']` + `get_default_params()['performance']` 重新渲染。
- 默认值就用各成员自己的默认（siqi 默认 120/10/60s，符合任务规格）。
- 跑完结果区根据 `extra` 字段动态渲染关键指标卡，缺失字段不显示对应卡片。

### 4.4 业务流程图 `#/flowchart`

```
┌─────────────────────────────────────────────────────────────┐
│  ← 返回入口    automationexercise.com 全局业务流程             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│         <img src="/static/flowchart.png" />                 │
│                                                             │
│         （用户替换 web/static/flowchart.png 即可生效）        │
└─────────────────────────────────────────────────────────────┘
```

- 前端固定引用 `web/static/flowchart.png`，路径写死。
- MVP 阶段放一张占位 PNG/SVG（"业务流程图待补充"字样的纯色图），用户后续替换同名文件即可。
- 后续优化方向（不在 Phase 1 范围）：可点击热区跳 `#/live/unit?selected=xxx`、SVG zoom-pan。

---

## 5. 交互流程（实时测试为例）

```
用户                  浏览器                FastAPI                Adapter (siqi)
 │                      │                     │                       │
 │ 进入 #/live/unit     │                     │                       │
 ├──点商品搜索卡片──────►│                     │                       │
 │                      ├─GET /api/meta──────►│                       │
 │                      │◄────12 模块 + 默认参数                       │
 │                      ├─渲染参数表单         │                       │
 │ 填 keyword=jeans     │                     │                       │
 │ 点 "🚀 开始测试"      │                     │                       │
 │                      ├─POST /api/run/unit─►│                       │
 │                      │  {module:search,    ├─启动后台线程──────────►│
 │                      │   keyword:jeans}    │   run_unit(...)        │
 │                      │◄─{job_id:"..."}─────│                       │
 │                      ├─EventSource          │                       │
 │                      │  /api/jobs/.../stream                       │
 │                      │                     │◄─proc.stdout─────────┤
 │                      │◄─SSE event:log──────│                       │
 │                      │  "test_search PASS" │                       │
 │ 看日志滚动            │                     │                       │
 │                      │                     │◄─跑完 TestResult──────┤
 │                      │                     ├─append history.json   │
 │                      │◄─SSE event:result───│                       │
 │                      │  TestResult JSON    │                       │
 │ 看到结果卡片          │                     │                       │
 │ 点"打开报告"          │                     │                       │
 │                      ├─新窗口/iframe →      │                       │
 │                      │  /reports/siqi/...                          │
```

---

## 6. 关键技术点

### 6.1 SSE 实时日志

siqi 现版本是 `subprocess.run`（阻塞、跑完才出 stdout）。GUI 后端在 jobs 层另写 `_run_streaming` 用 `Popen + iter(readline)` 逐行推送：

```python
# UI/server/jobs.py
async def stream_logs(job_id: str) -> AsyncGenerator[dict, None]:
    proc = JOBS[job_id]["proc"]
    for line in iter(proc.stdout.readline, ""):
        yield {"event": "log", "data": line.rstrip()}
    proc.wait()
    result = JOBS[job_id]["result_future"].result()
    yield {"event": "result", "data": json.dumps(result.to_dict())}
```

> 取舍：复用 siqi_interface 拿不到流式（spinner 模式）；自己拼 pytest 命令能流式但参数映射要重写。**MVP 复用 siqi_interface 走 spinner，Phase 2 再上 SSE**。

### 6.2 Playwright 弹窗

`siqi/config.py: HEADLESS = False`，跑测试弹真浏览器 = 演示卖点，不改。
答辩排版：主屏看 Playwright 自动化操作，副屏放 GUI 看日志/结果。

### 6.3 报告嵌入

```python
# UI/server/main.py
from fastapi.staticfiles import StaticFiles
app.mount("/reports/siqi", StaticFiles(directory="../siqi/reports"), name="siqi-reports")
```

历史页 / 实时结果卡片的"打开报告"按钮新窗口打开 `/reports/<member>/...`。

### 6.4 单任务串行

后端用全局锁，同时只允许一个 job 运行；前端按钮置灰直到结束。Locust 抢 8089、Playwright 多实例抢端口的问题都靠这个绕。

### 6.5 集成组合匹配

前端首次进入实时测试页时 GET `/api/integration/catalog` 拿白名单缓存到内存；用户改下拉框时本地比对，给出即时反馈（无需每次往后端发请求）。

### 6.6 Python 环境与启动

- **`UI/.venv`** 独立 venv，自包含所有依赖（FastAPI + Uvicorn + siqi 全套：playwright/pytest/pytest-playwright/pytest-html/locust/allpairspy）。
- `UI/requirements.txt` 把上述依赖都列上；安装步骤含 `playwright install chromium`（README 里写）。
- `adapters/siqi.py` 用 `sys.path.insert(0, str(SIQI_ROOT))` 把 `comprehensive-experiments/siqi/` 加进路径再 `import siqi_interface`，不需要 siqi 包装成 pip 包。
- `start.bat`：激活 `UI/.venv` → 后台启 `uvicorn server.main:app --port 8000` → `start http://localhost:8000` 自动开浏览器。

### 6.7 数据组合表格"逐行更新"

需要 pytest 跑的过程中按用例进度推送进度。siqi 当前用 `@pytest.mark.parametrize` 跑 25 个用例，可用 `pytest-json-report` 插件 + 监听文件或 stdout 解析。**MVP 不做实时更新**，跑完一次性渲染整张表。

---

## 7. 目录结构

```
comprehensive-experiments/UI/
├── ui_design.md          ← 本文件
├── README.md             ← 启动 / 演示说明
├── start.bat             ← 双击启动
├── requirements.txt      ← fastapi + uvicorn + sse-starlette
├── server/
│   ├── __init__.py
│   ├── main.py           ← FastAPI app
│   ├── jobs.py           ← 任务管理 + SSE
│   ├── history.py        ← history.json 读写
│   ├── history.json      ← 运行时生成
│   └── adapters/
│       ├── __init__.py
│       ├── base.py       ← Adapter 抽象 + TestResult dataclass
│       ├── siqi.py       ← ✅
│       ├── zhiyi.py      ← 🚧
│       ├── xupeng.py     ← 🚧
│       ├── yusheng.py    ← 🚧
│       └── integration_catalog.py  ← 集成组合白名单
└── web/
    ├── index.html
    ├── style.css
    ├── app.js
    └── static/
        └── flowchart_placeholder.svg
```

---

## 8. 视觉规范

- **主色**：`#2E3192`（深蓝紫）+ `#FF5F6D`（强调红）+ `#10B981`（通过绿）+ `#6B7280`（灰）。
- **字体**：`system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif`；日志区 `"JetBrains Mono", Consolas, monospace`。
- **不依赖任何 CDN / npm 包**。
- **响应式**：桌面端 1366×768 最低，移动端不管。
- **状态色**：✅ 通过 = 绿；❌ 失败 = 红；🚧 待接入 = 灰；⏳ 运行中 = 蓝带 spinner。

---

## 9. 实施分阶段

### Phase 1 ─ MVP（先跑通三入口骨架）

1. FastAPI server + 4 个 siqi 测试端点（同步阻塞）+ history.json 落盘。
2. SPA 三个路由：入口页 / 历史页（简表） / 实时页（4 sub-tab）。
3. 实时页：单元 12 卡片（仅 siqi 3 张可点）、集成 5 下拉 + 白名单匹配（仅 siqi 3 条命中）、数据组合（25 行表，跑完更新）、性能（自定义+完整规格双按钮）。
4. 业务流程图页：贴占位 SVG。
5. `start.bat` 双击可用。
6. **不**做 SSE，跑测试时只显示 spinner。

完成标准：点入口 → 进实时 → 选搜索模块 → 跑 → 看结果 → 回历史页能看到刚才那条记录。

### Phase 2 ─ 演示打磨

- SSE 实时日志。
- 数据组合表格逐行更新。
- 历史页加筛选 chip + 行展开。
- 视觉精修：动画、空状态插画、卡片 hover 效果。

### Phase 3 ─ 多成员接入

- 把 §3.3 抽成独立 `adapter_contract.md` 推给其他成员。
- 其他人提交一个 adapter → 在 `INTEGRATION_CATALOG` 加几行 → 模块卡片自动从 🚧 转 ✅。

---

## 10. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 现场断网，automationexercise.com 打不开 | 中 | 高 | 答辩前留一份历史记录 + 报告快照作 backup |
| Playwright 弹窗遮挡 GUI | 高 | 中 | 投屏前演练；准备好窗口排版预设 |
| 性能测试 60s 等不及 | 高 | 中 | 演示版默认 30 用户 / 20s；完整规格放单独按钮 |
| 其他成员永不提交接口 | 高 | 低 | UI 侧 🚧 占位，不影响 siqi 部分 |
| 集成组合白名单凑不满 12 个 | 高 | 中 | UI 不强求"必须 12 个"，已实现几个就显示几个；下拉框组合空间本身就大，观感不打折扣 |
| history.json 并发写损坏 | 低 | 低 | 单任务串行 + 写时加 fcntl/msvcrt 文件锁（或简单 threading.Lock） |
| 报告同名覆盖让历史链接失真 | 中 | 低 | 历史页"打开报告"按钮 hover 提示"显示该测试类型最近一次结果" |

---

## 11. 已确认的关键决策（v3 收口）

- [x] **集成 12 条 = 4 成员 × 3 路径**。组员还没给具体路径，我们形式上匹配 tuple 即可，命中就调对应组员代码（代码已能跑该集成场景）。
- [x] **集成下拉框允许同模块在不同深度重复**。照着弹孔画靶，"在某一层实现了的模块一定能被选中"。
- [x] **历史记录存完整 raw_output**，不归档 HTML 报告副本。
- [x] **业务流程图**：前端固定引用 `web/static/flowchart.png`，用户替换同名文件即可。
- [x] **入口页装饰素材**：banner / logo / 三张卡片图标都用占位文件，用户后续替换同名文件即可。
- [x] **数据组合 / 性能测试加成员切换 tab**，每人独立展示。
- [x] **性能测试参数完全由 adapter 驱动**（`get_default_params()`），不写死。
- [x] **Phase 1 优先**：其他成员占位，先把 siqi 串通跑出原型，验证需求后再迭代。
