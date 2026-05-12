# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Scope: `comprehensive-experiments/siqi/` only. The root `CLAUDE.md` covers repo-wide conventions; this file documents the specific task assigned to member `siqi`. The authoritative spec is `myTask.md` in this directory — when it disagrees with this file, `myTask.md` wins.

## System under test

- Target site: **http://automationexercise.com/** (public demo e-commerce site, no auth required for browsing).
- Modules siqi is responsible for testing:
  1. **商品列表 (Product List)** — browsing the products listing.
  2. **商品详情 (Product Detail)** — viewing an individual product page.
  3. **商品搜索 (Product Search)** — searching products by keyword.

Do not expand scope to other modules (cart, checkout, account) unless the user asks — those belong to other team members.

## Required deliverables (counts are fixed by the spec)

| # | Type | Count | Constraint |
|---|---|---|---|
| 1 | 单个模块测试 (module) | 3 | one per module above |
| 2 | 集成模块测试 (integration) | 3 | path depths **3, 4, 5** (one group each) |
| 3 | 数据组合测试 (data combination) | 1 | **25 data sets** |
| 4 | 性能测试 (performance) | 1 | **120 concurrent threads**, **2 s** response-time limit |

Each deliverable must include: 业务流程图, 运行截图 (manual reproduction), 测试步骤设计, 核心代码设计.

## Test case report format

Every test case follows this structure (see `myTask.md` for the worked example):

- 功能描述 / 用例目的 / 用例编号 (`TC-<Feature>-NN`) / 前提条件
- A 4-column action table: **输入/动作 | 期望的输出/响应 | 实际情况 | 是否通过**

Preserve Chinese headings and column names verbatim in submitted artifacts.

## Tooling (chosen 2026-05-12)

- UI automation: **Playwright (sync API)** driven by `pytest` + `pytest-playwright`.
- Performance: **Locust** (independent from pytest; 120 concurrent users, 2 s SLA).
- Data combinations: **allpairspy** to generate 25 pairwise sets, output committed as `testdata/combinations.csv`.
- Reports: `pytest-html` only.
- Config: single `config.py` at siqi root — no YAML, no `.env`, no pydantic.

Do not reintroduce Selenium / JMeter / config-loader stacks without checking with the user.

## Layout

```
config.py          BASE_URL / TIMEOUT / HEADLESS / SLOW_MO_MS
conftest.py        playwright browser+page fixtures; failure-screenshot hook
pages/             Page Object — one file per page
tests/             pytest cases (unit / integration / data_combo / performance)
testdata/          static fixtures + combinations.csv (committed)
docs/              deliverables: flowcharts, test_cases, manual_screenshots, final_report
reports/           runtime artifacts (gitignored)
```

Note: `testdata/` (not `data/`) — the repo-root `.gitignore` excludes `data/`.

## Conventions

- Artifacts (reports, flowcharts, screenshots, test case docs) stay in Chinese.
- Test case IDs: `TC-<Feature>-NN` — e.g. `TC-Search-01`, `TC-ProductList-02`.
- Integration test naming should make the path depth explicit (e.g. `TC-Integration-Depth3-01`).
- Screenshots are required and must reflect a real manual run of the same steps the automation executes.
