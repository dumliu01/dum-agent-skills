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

## 4. 章节分隔页：字号 × 容器宽度的算术（最高频踩坑）

### 问题
**章节分隔页主标题在我写的 `<br/>` 之前就自动换行了。** 这是写中文 PPT 最容易遇到、也最反直觉的一个坑。看起来字数不多（"上下文 · 架构 · 反馈 · 熵管理。" 只有 12 个字符），却被浏览器拦腰断开。

### 算术诊断（必背）

| 项 | 默认值 | 1440 屏实际值 |
|---|---|---|
| `.section-h` 字号 | `clamp(36px, 4.4vw, 68px)` | **63px** |
| 中文方块字宽度 | ≈ 1em（同字号） | **63px** |
| 容器宽度（模板原值） | `max-width: min(720px, 100%)` | **720px** |
| → **每行最多放几个中文字符** | 720 ÷ 63 | **≈ 11 字** |

11 字是上限。**实际经验：超过 10 字就开始有视觉风险，超过 12 字必然换行。** 几个例子：

```
✗ 上下文 · 架构 · 反馈 · 熵管理。       (≈ 17 em，3 个中点全角，必断)
✗ 来自 OpenAI / LangChain / HashiCorp 的  (≈ 17 em，英文 0.5em/字，串联公司名很危险)
⚠ 到「设计好运行环境」。                (≈ 11 em，刚好卡边界，部分浏览器会断)
✓ 翻车方式。                            (5 em，安全)
✓ 范式之变                              (4 em，安全)
```

### 解决方案（双管齐下）

**① 缩小 section-h 字号 + ② 加宽容器**：

```css
/* 在 .section-h:lang(en) 那行之后追加 */
.section-divider .section-h {
  font-size: clamp(30px, 3.6vw, 54px);   /* 1440 屏 ≈ 52px */
  line-height: 1.28;
}
```

```html
<!-- 所有章节分隔页的文本容器，把 720 改成 880 -->
<div style="max-width: min(880px, 100%); flex: 1;">
```

修复后算术：880 ÷ 52 ≈ **17 字/行**（从 11 提到 17，富余 ≈ 50%）。

### 文案改写规则（即使容器修好了，仍然要遵守）

| 上限 | 风险 |
|---|---|
| ≤ 12 字/行 | 安全，绝对不换 |
| 13-14 字/行 | 安全，留点呼吸感 |
| 15-16 字/行 | 偏挤，看起来有点贴边 |
| ≥ 17 字/行 | 必断，必须改写 |

**改写策略**：
- 3-4 个并列词太长 → 砍掉一个或合并：「上下文 · 架构 · 反馈 · **熵管理**」 → 「上下文 · 架构 · 反馈 · **熵**」（关键词压到下一行）
- 公司/产品名连串 → 抽象化：「OpenAI / LangChain / HashiCorp」 → 「一线团队」
- 标题里的修饰语 → 移到副标题段（`.body.strong`）

### 不要做的事
- ❌ **不要回退到 720px 容器**。后人复制你的代码会继承坑
- ❌ **不要用 `white-space: nowrap` 解决**。文本会溢出 slide 边界，看起来更糟
- ❌ **不要改全局 `--t-section`**。会影响所有 section-h 用例（虽然目前只有章节分隔页用，但未来可能扩展）

### 排错路径

如果还看到「想要的 `<br/>` 没生效」：

1. 打开浏览器开发者工具，选中那个 `<h2 class="section-h">`
2. 看 Computed 里的 `font-size` 和容器的 `width`
3. 算 `width / font-size` ≈ 多少（中文一字一 em）
4. 数一下你这一行的实际中文字数（半角字符算 0.5）
5. 如果你的字数 ≥ 算出来的字符数 - 1，就是这个坑

---

## 5. 章节分隔页：拆三层

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

## 6. 按钮文字被挤换行（SVG 失控）

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

## 7. 渐变高亮（gradient-text）的克制

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

## 8. 标点与符号

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

## 9. 字体回退顺序

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

## 10. 实战速查表（贴在屏边）

| 症状 | 一定先检查 |
|---|---|
| 中文标题挤 | `letter-spacing` 是负值？`line-height < 1.2`？ |
| 中文标题断行多 | 父容器是 `Nch` 单位？换 `min(720px, 100%)` |
| 章节分隔页主标题在 `<br/>` 之前就自动断行 | 容器是 720px 而不是 880px？scoped CSS `.section-divider .section-h { font-size: clamp(30px, 3.6vw, 54px) }` 没加？文案 ≥ 15 字/行？参见 §4 |
| 章节分隔页很满 | 把"章节名 ——"拆成 `.chapter-tag-row` |
| 按钮文字纵向 | SVG 没设宽高？按钮没 `white-space: nowrap`？ |
| 渐变文字到处都是 | 一张 slide 超过 2 处？删 |
| 数字列错位 | 加 `font-variant-numeric: tabular-nums` |
| 中英标点混乱 | 整段统一全角或半角 |
| Web Font 加载慢 | `<link rel="preconnect">` 加上没？ |
| 中文加粗看着假 | 是不是用了 `font-weight: 900`？降到 700 |
