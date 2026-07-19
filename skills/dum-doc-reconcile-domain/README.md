# dum-doc-reconcile-domain

> 把带日期的历史方案堆**收口**成 `docs/domain-tech-design/` `docs/domain-product-design/` 下按领域模块的"现状真相"权威文档——**报告先行**，确认后才写；鲜度脚本自动标 🟢/🟡。

## 它做什么

dated 方案（`docs/tech-design/` `docs/product-design/`）是一次次决策的存档，想知道某模块"现在是什么样"得翻一堆历史。本技能维护与之 1:1 对照的**现状权威树**：`docs/domain-<type>-design/<模块>/<模块>-<子模块>.md`，每模块一份 README 作总入口 + 鲜度总览表。

**三种模式**：

| 模式 | 何时 | 做什么 |
|---|---|---|
| M · 迁移 | 项目里还有 `*-newest` 旧目录 | `git mv` 改名 domain-* + 批量修链接 + 换新脚本（一次性，独立 commit） |
| A · Bootstrap | 模块在 domain 树下没文档 | 读全量 dated + 深读现状代码，合成 v1.0（只写当前生效的结论） |
| B · Incremental | 鲜度脚本判 🟡 | `git diff` 取证 + 新 dated 快照 + modify_history，只吸收增量不整篇重写 |

**记账体系**：frontmatter 鲜度头（`last-reconciled`/`reconciled-through`/`source.paths` 三件套）+ 修改记录表 + 四步收尾（改正文→追记录→同步 frontmatter→跑脚本转 🟢）。

**打包脚本**（[`scripts/`](scripts/)，首次使用复制到目标项目 `scripts/`）：

- `check_module_freshness.py` — 扫 domain 树，按 frontmatter 比对 git 提交与新 dated 快照，判 🟢/🟡 并回写各模块 README 鲜度表
- `_freshness_lib.py` — 判定纯函数库（仅 stdlib + pyyaml）

## 何时触发

- ✅ "建领域模块现状文档" / "生成领域权威文档" / "把 dated 方案收口成现状"
- ✅ "更新模块现状文档" / "reconcile domain"
- ❌ `docs/architecture/` 或 dated 方案的 prose 漂移校正 → 用 [`dum-doc-reconcile`](../dum-doc-reconcile/)
- ❌ 写新方案 → 用 [`dum-solution-design`](../dum-solution-design/)
- ❌ 总结会话改动 → 用 [`dum-session-summary`](../dum-session-summary/)

## 它交付什么

| | |
|---|---|
| 合成/漂移报告 | 动笔前在对话里给用户审（报告先行硬 gate） |
| domain 权威文档 | 骨架对齐《技术方案文档规范》/《产品文档规范》，架构图/时序图/接口数据全部代码溯源 |
| 鲜度记账 | frontmatter + 修改记录表 + 脚本回写的 README 鲜度总览表 |

## 跟其它技能怎么衔接

- [`dum-session-summary`](../dum-session-summary/) 的**下游**：它记事实 → 鲜度脚本判状态 → 本技能改内容
- 与 [`dum-doc-reconcile`](../dum-doc-reconcile/) 按**路径**分工：`domain-*-design/` 归本技能；`architecture/` 与 dated prose 归它。两套记账约定互不混用
- dated 方案由 [`dum-solution-design`](../dum-solution-design/) 产出，是 Bootstrap 的输入

## 完整工作流

三模式详细步骤、frontmatter/修改记录表模板、两套正文骨架、排版规约、红旗自检与出口判断，详见 [`SKILL.md`](SKILL.md)。
