# TC-ProductDetail — 商品详情模块单测

## TC-ProductDetail-01

| 字段 | 内容 |
|---|---|
| 功能描述 | 商品详情查看 |
| 用例目的 | 验证商品详情页关键信息字段（名称/类别/价格/库存/状态/品牌）齐全可见 |
| 用例编号 | TC-ProductDetail-01 |
| 前提条件 | 商品 ID = 1 存在于站点 |

### 业务流程图

```mermaid
flowchart LR
    A[导航至 /product_details/1] --> B[页面加载]
    B --> C[product-information 容器可见]
    C --> D[名称 / 类别 / 价格 / 库存 / 状态 / 品牌 字段都展示]
```

### 测试步骤

| # | 输入 / 动作 | 期望的输出 / 响应 | 实际情况 | 是否通过 |
|---|---|---|---|---|
| 1 | 浏览器导航至 `/product_details/1` | 页面加载完成 | 加载成功 | 通过 |
| 2 | 检查商品名称 `h2` | 可见且非空 | 可见 | 通过 |
| 3 | 检查 "Category:" 字段 | 可见 | 可见 | 通过 |
| 4 | 检查价格字段（`span > span`） | 可见 | 可见 | 通过 |
| 5 | 检查 "Availability:" 字段 | 可见 | 可见 | 通过 |
| 6 | 检查 "Condition:" 字段 | 可见 | 可见 | 通过 |
| 7 | 检查 "Brand:" 字段 | 可见 | 可见 | 通过 |

### 自动化脚本

`tests/test_unit_product_detail.py::test_product_detail_01_详情字段齐全`

### 人工复现截图

`docs/manual_screenshots/unit/TC-ProductDetail-01/`
- `step1_详情页加载.png`
- `step2_字段全貌.png`
