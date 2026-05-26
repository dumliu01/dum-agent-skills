# dum-ppt

> 把一份 Markdown（学习笔记 / 技术文档 / 行业研究 / 分享稿）转成**单 HTML 文件、可全屏播放**的专业演示文档。

## 它做什么

沉淀了多次 PPT 制作的工作流：摄入源材料 → 选场景定风格 → 规划 slide 信息架构 → 拼装单 HTML（含交互、打印、键盘导航）→ 中文排版陷阱复核 → 浏览器预览。

**输出特点**：
- 单 HTML 自包含（仅依赖 Google Fonts，复制即用）
- 完整交互层：键盘 / 触屏 / 鼠标滚轮 / URL hash / 概览模式 / 全屏
- 内置 `@media print` 可 Cmd+P 导出 PDF
- 对**中文排版**做了专门处理（字距、行高、断行——见 SKILL.md 的"陷阱 10 条"）

**三种预设视觉风格**：

| 场景 | 风格 | 适合 |
|---|---|---|
| 大公司对外分享 / 客户演示 / 产品发布 | **Fintech Dark**（深紫蓝 + 玻璃 + 渐变文字） | 默认推荐 |
| 学术报告 / 编辑级文档 / 政策研究 | **Editorial Light**（暖白 + 衬线 + 海军蓝） | 严肃克制 |
| 内部技术分享 / 开发者社区 | **Tech OLED**（纯黑 + Inter + JetBrains Mono + Bento Grid） | 极客风 |

## 何时触发

- ✅ "做 PPT" / "演示文稿" / "演讲稿" / "slide deck"
- ✅ "把这份文档做成 PPT" / "根据 xxx.md 生成 PPT"
- ❌ 只想要导出 PDF / 纯阅读 markdown（用 markdown 渲染）
- ❌ 想要图片 slide deck → 用 baoyu-slide-deck
- ❌ 想要落地页 / 长滚页（那是 landing page，不是 PPT）

## 它交付什么

| | |
|---|---|
| 输出位置 | `outputs/<topic>.html`（默认） |
| 张数惯例 | 28–35 张（>40 张说明粒度太细需合并） |
| 5 类 slide | Cover · Foreword(可选) · Agenda · Section Divider × N · 内容页 · 总结/Thanks |
| 已封装能力 | 33 张 slide 容器示例、CSS tokens、组件清单、JS 交互、打印样式 |

## 跟其它技能怎么衔接

- 跟内容生成类技能无强依赖——只要有 Markdown 就能开工
- 换风格 / 新场景时，可先跑 `ui-ux-pro-max --design-system "<keywords>"` 拿推荐，再在本技能模板上调色

## 完整工作流

7 步流程、5 类 slide 组件清单与 CSS tokens、**中文排版 10 条陷阱**（必读）、Pre-Delivery Checklist、常见错误，详见 [`SKILL.md`](SKILL.md)。

资源：`assets/templates/fintech-dark.html` 三套模板 · `references/chinese-typography.md` 中文排版详解。
