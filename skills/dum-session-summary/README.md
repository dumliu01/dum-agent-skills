# dum-session-summary

> 把**一次会话的改动**如实沉淀成标准结构的 Markdown，存进 `docs/modify_history/`。**只记录，不对账、不修文档。**

## 它做什么

git 知道**改了什么**；但只有会话记得**为什么这么改、试过什么被否决**——后者正是 git 永远拿不到的，也是本技能最大的价值。

**单一职责**：把这次会话发生了什么如实记下来，给两类下游消费：
1. **续接**（本技能直接服务）：切换/新开会话时，照这篇就能快速接上——做到哪、怎么继续、从哪个文件入手
2. **后续校对设计文档**（由 [`dum-doc-reconcile`](../dum-doc-reconcile/) 被显式触发时读取本记录完成）：本技能**不主动 grep 设计文档、不列"待校对清单"、不给修改建议、不修任何 `docs/architecture/` 或 `docs/方案设计/` 下的文件**

**核心原则**：以 git 为客观事实骨架（取 commit + diff），用会话上下文补"为什么"。

## 何时触发

- ✅ "总结这次会话/把改动记录下来/生成交接文档/方便下次继续"
- ✅ 一段较大的工作刚收尾、准备切换上下文
- ❌ 只想要一条 commit message → 用 git
- ❌ 只想知道改了哪些文件 → `git status`
- ❌ 写面向用户的 release notes（产品视角）
- ❌ 想对账/修正设计文档 → 用 [`dum-doc-reconcile`](../dum-doc-reconcile/)，不是本技能

## 它交付什么

| | |
|---|---|
| 路径 | `docs/modify_history/YYYY-MM-DD-<标题>.md` |
| 结构 | 固定 **6 节**：一句话概述 / 背景目标 / 改动清单 / 关键决策与理由 / 当前状态与验证 / 如何续接 |
| 关键节 | "关键决策与理由" 必含**被否决方案** |
| 不做 | 不写"受影响的设计文档（待校对）"一节；不去修 `docs/architecture/` 或 `docs/方案设计/`；不顺手触发 `dum-doc-reconcile` |

## 跟其它技能怎么衔接

- **上游**接代码改动；**下游**接 [`dum-doc-reconcile`](../dum-doc-reconcile/)——后者**在被用户显式触发**时读这些记录去对账 `docs/architecture/` 与 `docs/方案设计/`。本技能只产出原材料，不替它启动。
- 落点目录由 [`dum-knowledge-base-build`](../dum-knowledge-base-build/) 搭好；它的 `update_docs_index.py` 会把本文档自动收录进 `docs/docs-index.md`

## 完整工作流

三步流程（取数 → 写文档 → 落盘）、6 节模板的填写细节、常见错误与出口判断，详见 [`SKILL.md`](SKILL.md)。
