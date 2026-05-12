# TC-ProductList — 商品列表模块单测

## TC-ProductList-01

| 字段 | 内容 |
|---|---|
| 功能描述 | 商品列表浏览 |
| 用例目的 | 验证商品列表页可正常加载并展示商品 |
| 用例编号 | TC-ProductList-01 |
| 前提条件 | 网络可达 `http://automationexercise.com` |

### 业务流程图

```mermaid
flowchart LR
    A[导航至 /products] --> B[页面加载完成]
    B --> C[可见 All Products 标题]
    C --> D[列出商品卡片 含名称 + 价格]
```

### 测试步骤

| # | 输入 / 动作 | 期望的输出 / 响应 | 实际情况 | 是否通过 |
|---|---|---|---|---|
| 1 | 浏览器导航至 `/products` | 页面加载，URL 正确 | 加载成功 | 通过 |
| 2 | 检查 "All Products" 标题 | 标题元素可见 | 可见 | 通过 |
| 3 | 检查商品卡片数量 | `.product-image-wrapper` 数量 > 0 | N > 0 | 通过 |
| 4 | 检查第 1 个商品名称非空 | `.productinfo p` 文本不为空 | 名称正常 | 通过 |
| 5 | 检查第 1 个商品价格格式 | `.productinfo h2` 以 "Rs." 开头 | 格式正确 | 通过 |

### 自动化脚本

`tests/test_unit_product_list.py::test_product_list_01_列表正常展示`

### 人工复现截图

`docs/manual_screenshots/unit/TC-ProductList-01/`
- `step1_列表加载.png`
- `step2_商品卡片细节.png`
