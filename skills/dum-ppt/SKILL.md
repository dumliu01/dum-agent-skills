---
name: dum-ppt
description: 把一份 Markdown 内容（学习笔记、技术文档、行业研究、分享稿）转成「单 HTML 文件、可全屏播放」的专业演示文档。沉淀了多次 PPT 制作的工作流：摄入源材料 → 选场景定风格 → 规划 slide 信息架构 → 拼装单 HTML（含交互、打印、键盘导航）→ 中文排版陷阱复核 → 浏览器预览。触发：用户说"做 PPT / 演示文稿 / 演讲稿 / slide deck / 把这份文档做成 PPT / 根据 xxx.md 生成 PPT"。默认产出位置 `outputs/<topic>.html`。
---

# Dum PPT — 专业演示文档生成

## Overview

把一份 Markdown 文档转换成一份**单文件 HTML 演示稿**（16:9 全屏播放、键盘/触屏导航、Web 字体、玻璃质感卡片、自带打印样式可导出 PDF）。

核心特点：
- 单 HTML 自包含 — 仅依赖 Google Fonts，复制即用
- 内置完整交互层：键盘 / 触屏 / 鼠标滚轮 / URL hash / 概览模式 / 全屏
- 已预设三种适配场景的视觉风格（见下文「风格选择」）
- 对**中文排版**做了专门处理（字距、行高、断行）

## 触发场景

**应该触发**：
- 用户提供一份 markdown，要"做成 PPT" / "生成演讲稿" / "搞成演示文档"
- 用户说"slide deck / presentation / keynote / 演讲 / 分享"
- 用户希望把已有的研究 / 学习笔记 / 培训内容外化为可分享的视觉文档
- 用户提到"PPT.html" 这类单文件演示格式

**不应触发**：
- 用户只想要导出 PDF 或纯阅读版 markdown（用 markdown 渲染即可）
- 用户希望生成图片 slide deck（用 baoyu-slide-deck 之类工具）
- 用户想要一份网页着陆页 / 长滚页（这是 SPA / landing page，不是 PPT）

## 工作流（按顺序执行）

### 第 0 步：读源材料、判定场景

1. **读 markdown** — 完整读完，识别章节结构、关键概念、目标受众
2. **判断使用场景** — 决定走哪条视觉风格分支：

| 场景 | 风格 | 适合 |
|---|---|---|
| 大公司对外分享 / 行业简报 / 客户演示 / 产品发布 | **Fintech Dark**（深紫蓝 + 玻璃 + 渐变文字） | 默认推荐 |
| 学术报告 / 编辑级文档 / 政策研究 / 期刊摘要 | **Editorial Light**（暖白 + 衬线 + 海军蓝） | 严肃克制 |
| 内部技术分享 / 团队培训 / 开发者社区 | **Tech OLED**（纯黑 + Inter + JetBrains Mono + Bento Grid） | 极客风 |

不要靠"猜"。如果用户没说，问一次：「这份 PPT 是对内分享还是对外？目标受众是工程师还是业务/管理层？」

### 第 1 步：规划信息架构

把章节映射到 slide。**惯例 28-35 张**，超过 40 张说明粒度太细需要合并。

固定 5 类 slide 类型（按出现顺序）：

| 类型 | 数量 | 作用 |
|---|---|---|
| Cover / 封面 | 1 | 标题 + 副标题 + 作者 + 日期 + 受众 |
| Foreword / 前言 | 0-1 | About this briefing — 谁该读、三句话总结 |
| Agenda / 目录 | 1 | 全部章节一览 + 页码引用 |
| Section Divider / 章节分隔 | N | 每章一张，超大编号 + chapter-tag + 2 行 slogan + lede |
| 内容页 | 1-4 / 每章 | 主要信息载体（见下文「Slide 组件清单」） |
| 总结 / Thanks | 1-2 | 三句话带走 + 下一步行动 + 致谢 |

把规划写出来给用户确认（一行一张：`05. Part I · 四个发展阶段`），再开始写代码。

### 第 2 步：拼装 HTML

**直接基于模板** `assets/templates/fintech-dark.html` 改：

```bash
cp ~/.claude/skills/dum_ppt/assets/templates/fintech-dark.html outputs/<topic>.html
```

模板里的占位符（替换即可）：
- `{{DECK_TITLE}}` — 浏览器标签栏标题
- `{{DECK_DESCRIPTION}}` — meta description
- `{{BRAND_NAME}}` — 顶部品牌名（公司 / 团队）
- `{{BRAND_TAGLINE}}` — 品牌副标语（如 "Engineering Insights"）
- `{{BRAND_INITIAL}}` — 品牌名首字母（左上 logo 方块里显示）
- `{{DATE_LABEL}}` — 日期标签（如 "May 2026"）
- `{{VERSION}}` — 版本号（如 "v1.0"）

模板已包含的能力（不要重写）：
- CSS 设计 tokens（色彩、字体、间距、圆角、阴影）
- Top brand bar + 进度条 + 底部 pager + 章节标签
- 33 个 slide 容器示例 — **替换内部内容，保留外层 `.slide` 结构**
- 完整 JS 交互：← →、空格、Page Up/Down、Home/End、F 全屏、O 概览、ESC、触屏、滚轮
- 打印样式（每页一张 slide，可 Cmd+P 导出 PDF）

### 第 3 步：写 slide 内容（关键）

每张 slide 的标准骨架：

```html
<section class="slide" data-title="标题文字" data-section="Part X">
  <div class="slide-head">
    <div class="lhs">
      <span class="eyebrow">章节 · 副标题</span>
      <h2 class="page-h">主标题，<span class="gradient-text">关键词</span>用渐变。</h2>
    </div>
    <div class="rhs">05 · I</div>
  </div>
  <div class="content">
    <!-- 主内容区 -->
  </div>
</section>
```

**章节分隔页用 chapter-tag + gold-dash 结构**（防止中文标题挤）：

```html
<section class="slide section-divider" data-title="I · 范式转变" data-section="Part I">
  <div>
    <span class="eyebrow">PART · I</span>
    <p class="caption" style="margin-top: 8px;">Chapter one of eight</p>
  </div>
  <div style="display: flex; align-items: center; gap: clamp(32px, 5vw, 80px); flex: 1;">
    <div class="roman">I</div>
    <div style="max-width: min(880px, 100%); flex: 1;">  <!-- 必须 880，不要回退到 720（见陷阱 #10） -->
      <div class="chapter-tag-row">
        <span class="chapter-tag">范式之变</span>
        <span class="gold-dash"></span>
      </div>
      <h2 class="section-h">
        主标题第一行，<br/>                    <!-- ≤ 14 个中文字符/行（见陷阱 #10） -->
        主标题<span class="gradient-text">关键词</span>第二行。
      </h2>
      <p class="body strong" style="margin-top: 28px; font-size: 17px; max-width: 640px;">
        副标题段落 — 一两句话点题。
      </p>
    </div>
  </div>
  <div class="meta-grid">
    <div><div class="label">In this section</div><div class="value">章节内容概要</div></div>
    <div><div class="label">Key concept</div><div class="value">关键概念</div></div>
    <div><div class="label">Estimated</div><div class="value">X 分钟</div></div>
  </div>
</section>
```

## Slide 组件清单（已在模板中实现）

### 容器与卡片
- `.glass` — 玻璃质感卡片（基础），加 `.glow` 或 `.glow-accent` 启用发光
- `.glass.edge-top` — 顶部彩色渐变光线（用于强调主卡）
- `.account-card` — 紫蓝渐变填充卡（用于"推荐配置"等突出展示）

### 排版
- `.display-h` — 封面/Thanks 超大字（80-120px）
- `.section-h` — 章节分隔页主标题（36-60px）
- `.page-h` — 内容页标题（28-42px）
- `.card-h` — 卡片内标题（18-24px）
- `.sub-h` — 小标题（15-18px）
- `.lede` — 引言段（18-22px，行高松）
- `.body` `.body.strong` — 正文
- `.caption` — 注释文字
- `.eyebrow` — 章节/类型标签（11px，大写，带左侧 dot）
- `.kicker` — 强调小标（已被 eyebrow 替代，可选用）

### 强调
- `.gradient-text` — 渐变高亮（仅用于关键词，**一句话 1-2 处足够**）
- `.pull-quote` + `.pull-quote-wrap` — 引言块（左侧渐变细线）
- `.chapter-tag` + `.gold-dash` — 章节小标 + 金色细线（仅用于章节分隔页）

### 数据呈现
- `table.t` — 扁平表格（仅上下横线、tabular-nums）
- `.stat .figure / .label` — 大数字 + 标签（首屏统计用）
- `.timeline` + `.timeline-col` — 横向 4 列时间轴
- `.stage-badge` / `.stage-badge.active` — 阶段编号
- `.compare-row` + `.compare-arrow` — 左右对比（旧 vs 新）
- `pre.code` — 代码块（带语义着色）

### 徽章
- `.pill` — 圆角小标签，子类：`.primary` `.accent` `.success` `.gold` `.rose`
- `.badge` `.badge-primary/accent/success/gold/rose` — 带左侧 dot 的徽章
- `.icon-box` `.icon-box.accent/success/gold/violet/rose` — 圆角图标背板

### 布局
- `.grid-2` `.grid-3` `.grid-4` — 等分网格
- `.grid-2-3` `.grid-3-2` — 2:3 / 3:2 不等分
- `.stack` `.stack-sm` `.row` — 垂直/水平流式

## 设计 Tokens（深色 Fintech 风格）

```
背景       --bg            #0A0E27       深紫蓝
卡片底     --bg-glass      rgba(255,255,255,0.04)  玻璃
主色       --primary       #6366F1       indigo
强调       --accent        #06B6D4       cyan
渐变文字   var(--grad-text)              indigo → cyan → mint
成功       --success       #22C55E
警示       --gold          #FBBF24
错误       --rose          #F43F5E
文字       --text/--text-dim/--text-muted/--text-faint
```

字体：
- 拉丁标题：**Space Grotesk**
- 拉丁正文：**DM Sans**
- 等宽：**JetBrains Mono**
- 中文：依次回退 PingFang SC / Noto Sans SC / Microsoft YaHei / system-ui

## 中文排版陷阱（必读）

详细见 [`references/chinese-typography.md`](references/chinese-typography.md)。**速记**：

1. **不要给中文标题用负字距** — `letter-spacing: -0.025em` 是给英文的，方块字加负值会挤
2. **中文行高至少 1.2** — 英文 1.05 看起来精致，中文会粘连
3. **避免 `max-width: 24ch` 这种 ch 单位** — `ch` 基于父级 16px 字号的 "0" 宽度，标题字号 60px 时空间根本不够
4. **章节分隔页拆三层** — chapter-tag（小） + section-h（2 行主标题） + lede（副标题），不要塞 3 行主标题里
5. **按钮的 SVG 一定要 `flex-shrink:0` + 固定宽高** — 否则会挤压文字换行
6. **按钮文字加 `white-space: nowrap`** — 防中文被强制换行
7. **gradient-text 用得稀** — 一句话最多 1-2 处关键词，到处都是反而失焦
8. **带 `::before` 的列表（`ol.lcn` 等）不要手动塞占位 `<div></div>`** — CSS `::before` 已经是 grid 第一列（编号 badge），手动占位会把真正的内容挤到下一行第 1 列（36px 宽），中文会被压成一字一行。`<li>` 直接放一个内容 div 即可
9. **封面/Thanks 的短标题（≤6 字，如「谢谢大家」「Thank you」）不用 `<br/>` 强行拆行** — `display-h` 字号已经够大，4 个字拆成 2+2 看起来「字数太少」很奇怪。直接一行 + 加 `white-space: nowrap` 防小屏意外换行
10. **章节分隔页 `.section-h` 每行 ≤ 14 个中文字符**（更严格 ≤ 12）— **算术**：默认 `--t-section` 是 4.4vw，1440 屏 = 63px；中文一字 ≈ 1em；容器 880px ÷ 63px ≈ **14 字/行**。超过这个数浏览器会在你的 `<br/>` 之前自动换行。模板已默认应用 scoped CSS `.section-divider .section-h { font-size: clamp(30px, 3.6vw, 54px) }`（→ 1440 屏 52px，约 17 字/行）+ 容器 `min(880px, 100%)`。**不要回退**到 720px。文案确实超长时（如要列 3-4 个并列词），<u>改写</u>比放宽更可靠

## Pre-Delivery Checklist

提交前对照检查：

- [ ] 总数 28-35 张 slide
- [ ] 章节分隔页用 chapter-tag + gold-dash，**不是** "章节名 ——" 挤进 section-h
- [ ] 中文标题：line-height ≥ 1.2、letter-spacing 不为负
- [ ] 所有 `max-width: Nch` 限制都改为像素或 `min(720px, 100%)`
- [ ] 章节分隔页 `.section-h` **每行 ≤ 14 个中文字符**；容器是 `min(880px, 100%)`（不是 720px）；scoped CSS `.section-divider .section-h { font-size: clamp(30px, 3.6vw, 54px) }` 在位
- [ ] 所有 button 里的 SVG 有 `flex-shrink:0` + 固定 width/height
- [ ] 所有 button 有 `white-space: nowrap`
- [ ] `ol.lcn` / 任何 grid + `::before` 的列表里 `<li>` **只有一个**内容子元素（不要手动加占位 div）
- [ ] 封面 / Thanks 页的短标题（≤6 字）不用 `<br/>` 拆行，并加 `white-space: nowrap`
- [ ] 没有 emoji 当图标（用 inline SVG）
- [ ] 每张 slide 有 `data-title` 和 `data-section`（概览模式与底部章节标签需要）
- [ ] 关键 CTA 元素加 `aria-label`
- [ ] `prefers-reduced-motion` 媒体查询保留
- [ ] `@media print` 保留（用户可能要导出 PDF）
- [ ] 浏览器实际打开预览 — 至少检查 1 张章节分隔页 + 1 张正文页 + 封面 + Thanks

## 默认产出与命名

- 输出位置：`outputs/<topic>.html`（如项目里没有 `outputs/` 就建一个）
- 不要写中间步骤的临时 markdown 文件 — 直接出最终 HTML
- 如果用户给了多个 markdown 文件作为输入，整合到一个 PPT 里，不要每个文件一份

## 常见错误与规避

| 错误 | 表现 | 修正 |
|---|---|---|
| 标题挤成 3 行 | section-h 第一行是「章节名 ——」 | 拆 chapter-tag-row + 2 行 section-h |
| pull-quote 一句话换 3-4 次 | max-width: 24ch 太窄 | 改 `min(720px, 100%)` |
| 按钮文字纵向显示 | SVG 没设宽高 | `.btn-primary svg { width:16px; height:16px; flex-shrink:0 }` |
| 太多渐变文字反而看不清重点 | 每张 slide 多处 gradient-text | 每张最多 2 处，且只用于真正的关键词 |
| Emoji 当图标在不同系统渲染不一 | 🎨 🚀 ⚙️ 等 | 改 inline SVG（Heroicons / Lucide 风格） |
| 表格数字晃动 | 用户调整字号时数字列错位 | 表格加 `font-variant-numeric: tabular-nums` |
| 长 markdown 改完 PPT 章节顺序混乱 | 1:1 复制章节没合并 | 先规划 slide list 给用户看，再写 HTML |
| `ol.lcn` 列表内容一字一行 | `<li>` 里手动加了空 `<div></div>` 占位，把内容挤到下一行 36px 列 | 删空 div，`<li>` 只放一个内容 div；`::before` 已经是第一列 |
| 封面 / Thanks 短标题字数显得太少 | `<br/>` 把 4 字标题拆成 2+2 行 | 去 `<br/>` + `white-space: nowrap` 防小屏换行 |
| 章节分隔页主标题在 `<br/>` 之前就自动换行了 | 容器 720px + 字号 4.4vw → 1440 屏每行只能放 11 个中文字符 | 容器改 `min(880px, 100%)` + 加 scoped CSS `.section-divider .section-h { font-size: clamp(30px, 3.6vw, 54px); line-height: 1.28 }`；模板已默认这样写 |
| 章节分隔页主标题挤但容器和字号都已经设对 | 文案本身 ≥ 15 个中文字符 | 重写文案 ≤ 14 字/行；3-4 个并列词改成 2+2 或合并；地名/公司名连串（如「OpenAI / LangChain / HashiCorp」）改写为「一线团队」 |

## 与 ui-ux-pro-max 的关系

- **dum_ppt** 偏沉淀模板与流程，给定一份内容直接出 HTML
- **ui-ux-pro-max** 适合在做新风格 / 新场景时调研推荐（`--design-system` 命令）
- 想换风格 → 先跑 `ui-ux-pro-max --design-system "<keywords>"` 拿推荐，再在 dum_ppt 模板上调色

## 一个典型对话示例

```
用户："根据 raw/personal/分享.md 生成对外分享的 PPT"

第 1 步：读源材料 → 识别 8 章节、约 27K 字
第 2 步：场景判断 → "对外分享" → Fintech Dark 风格
第 3 步：信息架构规划（向用户报告）：
   - 33 张
   - Cover / About / Agenda / 8 × (Section Divider + 1-4 内容页) / 总结 / Thanks
   - 给出 slide list
第 4 步：cp template → outputs/分享.html，替换占位符
第 5 步：写 33 张 slide 的内容
第 6 步：对照 Pre-Delivery Checklist
第 7 步：在浏览器打开预览
```
