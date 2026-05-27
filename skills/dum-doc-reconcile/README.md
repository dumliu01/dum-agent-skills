# dum-doc-reconcile

> 按**时间范围**把 `docs/architecture/` 与 `docs/方案设计/` 跟代码现状对账修正——**报告先行**，确认后才改。

## 它做什么

设计文档不可避免会随代码漂。本技能定期校对：依据 `docs/modify_history/` 的记录（兼查 git）找出"文档现述 vs 当前事实"的漂移点，**先出漂移报告并停下等用户确认**，再动文档——设计文档是精雕内容，未经确认的重写会抹掉有意的细节。

**四相工作流**：

| Phase | 做什么 |
|---|---|
| 1 · 取数 | 解析时间范围；扫 modify_history 范围内的"改动清单 + 关键决策"+ 同范围 git diff；**自己 grep `docs/architecture/` 与 `docs/方案设计/`** 推断待校对清单 |
| 2 · 漂移报告 | 逐文档列【事实性·可直接改】/【需判断·要拍板】/【已核对·无漂移】——**输出后停下** |
| 3 · 应用 | 按确认结果改文档；**不碰** AUTO-GENERATED 区；保 5 模块结构；遗留问题标"已解决" 不删历史 |
| 4 · 水印 | 给改过/核对过的文档打/更新校对水印（H1 下唯一一行） |

## 何时触发

- ✅ "校对/修正设计文档" / "按时间范围更新文档" / "文档对账"
- ✅ "让 architecture/方案设计 保持最新"
- ❌ 要更新代码目录树 → 跑 doc-build 的 `update_architecture_*.py`
- ❌ 写新方案 → 用 [`dum-solution-design`](../dum-solution-design/)
- ❌ 总结某次会话改了什么 → 用 [`dum-session-summary`](../dum-session-summary/)

## 它交付什么

| | |
|---|---|
| 漂移报告 | 按文档+章节列出"现述/应为/依据/类别"的表格（在对话里给用户审） |
| 修正后的文档 | 仅 `docs/architecture/*` 与 `docs/方案设计/*` 两个目录内 |
| 校对水印 | `> 🗓️ 文档校对：已对齐至 YYYY-MM-DD（依据 modify_history + git 至 <hash>）— dum-doc-reconcile` |

## 跟其它技能怎么衔接

- 它是 [`dum-session-summary`](../dum-session-summary/) 的**下游**：后者每次会话只如实记录"改了什么、为什么这么改、否决了什么"，**不再列"受影响的设计文档（待校对）"**；本技能被显式触发时，再据这些记录 + 同范围 git diff 自己 grep 推断哪些设计文档需要校对、然后修正
- AUTO-GENERATED 目录树归 [`dum-knowledge-base-build`](../dum-knowledge-base-build/) 的脚本管，本技能只动语义 prose

## 完整工作流

四相详细步骤、漂移报告模板、水印约定、报告先行的硬性 gate、红旗自检与出口判断，详见 [`SKILL.md`](SKILL.md)。
