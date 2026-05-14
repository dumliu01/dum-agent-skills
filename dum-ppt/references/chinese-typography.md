# 中文排版踩坑笔记 — PPT 场景

本文沉淀的是「英文为主的现代字体系统应用到中文标题/正文时」反复出现的具体问题与已验证的解法。**全部来自真实修改对话的迭代**，不是网上抄的通用规则。

---

## 1. 字距（letter-spacing）

### 问题
英文标题为追求精致紧凑感，常用 `letter-spacing: -0.025em ~ -0.035em`。直接套到中文方块字上 → **字与字粘连、视觉拥挤**。

### 规则
| 字号 | 英文（拉丁） | 中文（方块字） |
|---|---|---|
| Display (60-120px) | -0.025em ~ -0.035em | -0.01em ~ 0 |
| Section (36-68px)  | -0.02em ~ -0.025em | -0.005em ~ 0 |
| Page H (28-44px)   | -0.015em             | -0.005em ~ 0 |
| Body (14-18px)     | 0                    | 0 ~ +0.01em |
| Small (12-13px)    | 0                    | +0.01em ~ +0.02em |

### CSS 做法（多语言并存）

```css
.section-h {
  letter-spacing: -0.005em;          /* 中文友好默认值 */
  line-height: 1.22;
}
/* 用 :lang() 给纯英文场景恢复紧凑 */
.section-h:lang(en) {
  letter-spacing: -0.025em;
  line-height: 1.05;
}
```

或者在 HTML 上加 `lang="en"`：
```html
<h2 class="section-h" lang="en">Banking Made Simple</h2>
```

---

## 2. 行高（line-height）

### 问题
英文标题 `line-height: 1.05` 看起来精致，因为拉丁字符上下空隙大。中文方块字本身高度接近字号，1.05 会让两行**贴在一起**。

### 规则

| 字号区间 | 英文起点 | 中文最低 | 推荐 |
|---|---|---|---|
| Display (60-120px) | 1.0 | 1.08 | **1.08-1.15** |
| Section/Page (28-68px) | 1.05 | 1.2 | **1.22-1.3** |
| Card H / Sub-H | 1.2 | 1.25 | **1.25-1.35** |
| Body | 1.4 | 1.55 | **1.6-1.7** |
| Pull quote | 1.2 | 1.3 | **1.3-1.4** |

### 真实案例
原版 `.section-h { line-height: 1.05 }`，"团队协作 ——" + "从横向分工" + "到垂直赋能。"三行渲染时下一行的"从"字盖到了上一行"——"的下沿。改为 `1.22` 后正常。

---

## 3. max-width 与 ch 单位陷阱

### 问题
`max-width: 24ch` 看起来"约 24 个字符宽"，**但 `ch` 是基于父级字号的 `0` 字符宽度**。

如果父 div 没设字号 → 继承 body 的 16px → `1ch ≈ 8px` → `24ch ≈ 192px`。

但 `.pull-quote` 字号是 36px，**一个中文字宽就 36px+**，192px 顶多放 5 个汉字 → 强制换行。

### 规则
- **标题/大字号容器**禁用 `ch` 单位。用绝对像素：`max-width: min(720px, 100%)`
- 只有**正文段落**才能用 `ch`，且要确保父级字号一致

### 修复模式
```css
/* 错 */
.pull-quote { max-width: 24ch; }

/* 对 */
.pull-quote { max-width: min(720px, 100%); }
```

```html
<!-- 错 -->
<div style="max-width: 42ch;">
  <h2 class="section-h">60px 中文标题</h2>
</div>

<!-- 对 -->
<div style="max-width: min(720px, 100%); flex: 1;">
  <h2 class="section-h">60px 中文标题</h2>
</div>
```

---

## 4. 章节分隔页：拆三层

### 问题
直接把"章节名 —— 主标题 关键词" 塞进一个 `<h2>` 标题里 → 第一行是"章节名 ——"占了 4-5 字宽 → 标题被迫断成 3 行甚至 4 行。

### 规则
分成三层独立元素：

```html
<!-- ① chapter-tag — 章节小标 + 金色细线 -->
<div class="chapter-tag-row">
  <span class="chapter-tag">范式之变</span>
  <span class="gold-dash"></span>
</div>

<!-- ② section-h — 主标题，最多 2 行 -->
<h2 class="section-h">
  从「写好代码」，<br/>
  到「让 AI <span class="gradient-text">写好代码</span>」。
</h2>

<!-- ③ lede / body — 副标题段 -->
<p class="body strong" style="margin-top: 28px; font-size: 17px; max-width: 640px;">
  准确率从 70% 跨到 95% — 跨越了一条决定性的边界。
</p>
```

对应 CSS：
```css
.chapter-tag-row {
  display: flex; align-items: center; gap: 16px;
  margin-bottom: 20px;
}
.chapter-tag {
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(15px, 1.3vw, 20px);
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.02em;
}
.gold-dash {
  flex: 0 0 56px;
  height: 1px;
  background: linear-gradient(90deg, var(--accent-2), transparent);
}
```

### 视觉优势
- 章节名独立，不与主标题争视觉权重
- 主标题保持 2 行节奏感
- 金色细线视觉收口，强化「冷的科技感 + 暖的精致感」对比

---

## 5. 按钮文字被挤换行（SVG 失控）

### 问题
```html
<button class="btn-primary">
  <svg viewBox="0 0 24 24">...</svg>
  阅读完整简报
</button>
```

按钮用 `inline-flex`，但 SVG 没设宽高 → SVG 在 flex 容器里宽度变成 auto → 撑大占走文字空间 → "阅读完整简报"变成 3 行 "阅读 / 完整 / 简报"。

### 规则
```css
.btn-primary, .btn-secondary {
  display: inline-flex; align-items: center; gap: 8px;
  white-space: nowrap;        /* 必加：禁止文字换行 */
  line-height: 1.2;           /* 中文按钮文字 */
}
.btn-primary svg, .btn-secondary svg {
  width: 16px; height: 16px;  /* 固定大小 */
  flex-shrink: 0;             /* 不被挤压 */
}
```

### 检查清单
- [ ] 按钮的所有 SVG 都设了 `width` `height`
- [ ] 按钮父类都有 `white-space: nowrap`
- [ ] SVG 加 `flex-shrink: 0`（也包括 icon-box、列表项前缀的 ✓ 等）

---

## 6. 渐变高亮（gradient-text）的克制

### 问题
喜欢用 `.gradient-text` 高亮关键词 → 一张 slide 上 4-5 处都用 → **没有重点反而失焦**，渐变颜色还会和图标、徽章打架。

### 规则
- **每张 slide 最多 2 处** `.gradient-text`
- 优先用在"主标题里的关键词"或"封面/Thanks 的核心动词"
- 不要给数据/数字/正文段落里加（数字用 `.figure`，正文用 `b` + `color: var(--text)`）

### 反例 → 正例

```html
<!-- 错：每个名词都渐变 -->
<h2>从<span class="gradient-text">细节</span>到<span class="gradient-text">原理</span>，从<span class="gradient-text">个人</span>到<span class="gradient-text">团队</span></h2>

<!-- 对：只强调最关键的一个对比 -->
<h2>从掌握细节，到掌握<span class="gradient-text">原理</span>。</h2>
```

---

## 7. 标点与符号

### 中英文混排
- **标点跟随主体语言**：句子是中文 → 用全角逗号句号；是英文 → 用半角
- **「」与 ""**：在 PPT 标题里"「」"比 `""` 更有"出版物质感"
- **破折号 ——** 在中文里是两个 em-dash，**不要写一个**；英文用 `—` 单个

### 数字与单位
```css
.t, .stat .figure {
  font-variant-numeric: tabular-nums;   /* 等宽数字，防止表格列错位 */
  font-feature-settings: "tnum";
}
```

数字与单位之间：
- 中文：「**100K** 用户」（数字粗，单位窄空格）
- 英文：「**100K** users」（一个空格）

百分比、货币、温度紧贴数字，不加空格：`95%` `$2` `27°C`

---

## 8. 字体回退顺序

最稳的中文回退（覆盖 Mac + Windows + Linux + Web）：

```css
font-family:
  'Space Grotesk',         /* 主：英文几何字体 */
  'DM Sans',               /* 主：英文正文 */
  'PingFang SC',           /* Mac 中文 */
  'Microsoft YaHei',       /* Windows 中文 */
  'Noto Sans SC',          /* Web Font 中文 */
  system-ui, sans-serif;
```

**注意顺序**：先英文优先字体 → 再中文回退 → 最后 system-ui。这样英文字符走 Space Grotesk，中文走 PingFang，混排不会有不协调感。

---

## 9. 实战速查表（贴在屏边）

| 症状 | 一定先检查 |
|---|---|
| 中文标题挤 | `letter-spacing` 是负值？`line-height < 1.2`？ |
| 中文标题断行多 | 父容器是 `Nch` 单位？换 `min(720px, 100%)` |
| 章节分隔页很满 | 把"章节名 ——"拆成 `.chapter-tag-row` |
| 按钮文字纵向 | SVG 没设宽高？按钮没 `white-space: nowrap`？ |
| 渐变文字到处都是 | 一张 slide 超过 2 处？删 |
| 数字列错位 | 加 `font-variant-numeric: tabular-nums` |
| 中英标点混乱 | 整段统一全角或半角 |
| Web Font 加载慢 | `<link rel="preconnect">` 加上没？ |
| 中文加粗看着假 | 是不是用了 `font-weight: 900`？降到 700 |
