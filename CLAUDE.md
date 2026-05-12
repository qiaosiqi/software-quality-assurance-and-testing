# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

Coursework for 软件质量保证与测试 (Software Quality Assurance and Testing). Contents are written in Chinese; preserve Chinese in user-facing artifacts (reports, flowcharts, test case docs) and follow the report templates already in the task spec rather than translating them.

The repository currently holds **specifications only** — no implementation code, no build system, no test framework chosen yet. The `.gitignore` anticipates Python, Node/Electron, C/C++, ROS, and AI/DL toolchains; do not infer a stack from it. Ask the user (or check `comprehensive-experiments/<member>/myTask.md` if newly added) before picking a language or framework.

## Layout

- `comprehensive-experiments/` — the only active experiment ("自选网站集成测试", a 4-person group project).
  - `siqi/`, `xupeng/`, `yusheng/`, `zhiyi/` — one directory per team member. Each has a `<name>.md` stub stating role and 完成状态 (completion status).
  - `siqi/myTask.md` — the canonical task spec for the member named `siqi`. **Only `siqi` is active** (`完成状态: 待开始`); the other three members are marked `暂不更新` ("not updating for now"), so do not generate work in their directories unless asked.
  - `GUI/` — empty placeholder, intended for a shared GUI test harness if/when needed.

## Conventions to respect

- Don't restructure or rename the per-member directories — the four-way split mirrors the group submission format.
- When proposing tooling, surface the choice (Selenium vs Playwright, JMeter vs Locust, etc.) and the trade-off rather than picking silently; the user has not committed to a stack.
- Test case IDs follow the `TC-<Feature>-NN` pattern shown in the sample (`TC-Register-01`).
