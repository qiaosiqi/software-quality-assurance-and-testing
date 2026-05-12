# 业务流程图

每个测试用例的业务流程图以 **mermaid** 形式直接内嵌在 `docs/test_cases/TC-*.md` 中。GitHub、VSCode、Typora 等都能直接渲染。

## 如果需要导出为 PNG（提交 Word 报告时）

任选其一：

1. **Mermaid Live Editor** — 把 markdown 里的 mermaid 代码块粘到 <https://mermaid.live>，导出 PNG / SVG。
2. **VSCode** + 插件 *Markdown Preview Mermaid Support* — 预览后右键截图。
3. **draw.io / drawio-desktop** — 重新画一份更精美的版本，导出 `.png` 放到本目录，命名形如：

```
docs/flowcharts/
├── TC-Search-01.png
├── TC-ProductList-01.png
├── TC-ProductDetail-01.png
├── TC-Integration-Depth3-01.png
├── TC-Integration-Depth4-01.png
├── TC-Integration-Depth5-01.png
├── TC-DataCombination.png
└── TC-Performance-01.png
```

PNG 文件本目录可直接 commit（小图体积 OK）。

## 如果你只交 markdown / pdf

不用导出，mermaid 源码就是最终交付物。
