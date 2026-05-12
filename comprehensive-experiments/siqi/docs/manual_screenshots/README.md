# 人工复现截图

> 任务规格（`myTask.md`）明确要求："运行截图（人工复现时进行截图操作）"。即：**手动按测试步骤操作浏览器**，关键节点用系统截图工具（Win+Shift+S 或 Snipping Tool）截图存盘。

不是自动截图（自动截图归 `reports/screenshots/`，gitignored，仅用于调试）。

## 目录结构

```
manual_screenshots/
├── unit/
│   ├── TC-ProductList-01/
│   ├── TC-ProductDetail-01/
│   └── TC-Search-01/
├── integration/
│   ├── TC-Integration-Depth3-01/
│   ├── TC-Integration-Depth4-01/
│   └── TC-Integration-Depth5-01/
├── data_combination/
│   └── TC-DataCombination/
│       ├── pass_DC-01.png         一组通过示例
│       └── fail_DC-02.png         一组失败示例（前导空格）
└── performance/
    └── TC-Performance-01/
        ├── step1_locust_启动.png
        ├── step2_locust_总结.png
        └── step3_html报告.png
```

## 命名约定

`<step编号>_<中文步骤说明>.png` —— 例 `step2_输入关键词dress.png`。

## 截图要求

- 浏览器**关掉广告**和**第三方插件**（截图干净）
- 包含 URL 栏（证明在正确页面）
- 失败截图要让"实际情况"清晰可见（错误提示 / 空结果区域）

## 提交时

整目录 commit；不要把 PNG 放在 `reports/screenshots/`（那是 gitignored 的运行时产物）。
