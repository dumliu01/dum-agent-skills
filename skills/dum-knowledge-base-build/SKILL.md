---
name: dum-knowledge-base-build
description: 按标准文档体系给项目搭建/维护"知识库"：脚手架 docs/ 全套分类目录（architecture / specification / product-design / tech-design / superpowers / modify_history / deffered / manual_deployment / manual_userguides / report / reference）+ 根与各子项目 CLAUDE.md 入口文档 + 各子项目程序架构文档；并接 PostToolUse hook 自动维护两块——各服务源码目录清单、`docs/docs-index.md` 分类文档索引。触发场景：用户说"整理架构文档" / "生成架构说明" / "搭建知识库" / "知识库文档" / "文档结构" / "文档体系" / "文档索引" / "docs-index" / "CLAUDE.md 入口" / "前端和后端架构文档" / "文件变化后文档自动更新" / "auto-update arch doc" 等。约定输出位置：根 `CLAUDE.md`、`docs/architecture/[service].md`、`docs/docs-index.md`、各子项目 `<service>/CLAUDE.md`。
---

# Dum Knowledge Base Build

## Overview

帮用户在一个项目里建立一套**标准化的知识库文档体系**，并接上 **PostToolUse hook** 让两块自动区在每次 Write/Edit 后同步。这套体系约定如下（一个项目含多个子项目，如后端 / 前端）：

```
<project_root>/
├── CLAUDE.md                  # 🤖 agent 总入口：项目概述 + 子项目列表 + 文档索引 + 核心文档
├── docs/
│   ├── docs-index.md          # 🤖 分类文档索引（自动维护，DOCS-INDEX marker，docs/ 总入口）
│   ├── architecture/          # 各子项目核心架构文档 <service>.md（含源码目录清单，自动维护）
│   ├── specification/         # 编程 / 工程规范
│   ├── product-design/        # 产品（需求）设计      （YYYYMMDD-[标题].md，可按模块分子目录）
│   ├── tech-design/           # 技术方案设计          （YYYYMMDD-[标题].md，对接 dum-solution-design）
│   ├── superpowers/           # superpowers 产出（plans/ + specs/）
│   ├── modify_history/        # 阶段总结 / 修改记录    （YYYYMMDD-[修改摘要].md）
│   ├── deffered/              # 待办 / 暂缓事项        （YYYYMMDD-[摘要].md）
│   ├── manual_deployment/     # 部署文档
│   ├── manual_userguides/     # 用户手册
│   ├── report/                # 分析报告              （YYYYMMDD-[标题].md）
│   └── reference/             # 参考资料 / 外部链接（不放 docs-index）
└── <service>/CLAUDE.md        # 🤖 各子项目入口：核心信息 + 关键文档（架构 / 规范）
```

**两块自动维护的内容**（hook 驱动）：

| 内容 | 回答的问题 | 脚本 | 写到哪 | 标记 |
|---|---|---|---|---|
| **源码目录清单** | 「**代码**有哪些、在哪些目录」 | `update_architecture_<service>.py`（一服务一份） | `docs/architecture/<service>.md` §2 | `<!-- AUTO-GENERATED -->` |
| **分类文档索引** | 「**文档**有哪些、在哪些目录」 | `update_docs_index.py`（一项目一份） | `docs/docs-index.md` | `<!-- DOCS-INDEX -->` |

外加一个**一次性脚手架** `scaffold_docs_structure.py`（不进 hook）：建 docs/ 全套目录 + 每目录 README + docs-index.md 骨架，幂等、不覆盖已有。

## 触发判断

**应该触发**：
- 用户要求生成 / 整理 / 维护"架构文档"、"知识库"、"文档体系"、"文档结构"、"文档索引"
- 用户要求按某套目录结构搭建项目文档（如本 skill 约定的 docs/ taxonomy）
- 用户要求"文件变更后文档自动更新"、"持续维护文档索引"、"auto-update arch doc"
- 项目代码已稳定，但缺少俯瞰全图的入口（CLAUDE.md / 架构文档 / 文档索引）

**不应触发**：
- 用户只想要面向用户的 README（产品视角，不是开发者知识库）
- 用户问"代码改了哪里"（git log 即可）
- 单文件 / 小脚本项目（< 20 个源文件，不值得引入整套体系）

## 工作流（按顺序，跳一步说原因）

### 第 0 步：摸底

1. **子项目数 + 语言** — 看 `apps/`、`services/`、`packages/`、根级目录等。一个子项目（进程）一份架构文档；语言影响源码"描述提取"规则
2. **顶层目录** — 列出每个子项目的核心目录（Python 后端 `core / apps / infra`、前端 `apps/web/src`）
3. **已有什么** — 是否已有 `docs/`、`CLAUDE.md`（根 / 子项目）、`方案设计/`、`claude_refs/` 等。**已有的一律保护、增量补，不覆盖**
4. **文档散落盘点** — 现有 `.md` 都在哪？哪些该归到 docs/ 的哪个分类（方案设计→tech-design、需求→product-design、报告→report …）

把摸底结果写进对话（不存文件），跟用户确认拆几份架构文档、要不要迁移已有散落文档进 docs/ 分类。

### 第 1 步：脚手架 docs/ 结构

复制 [`scripts/scaffold_docs_structure.py`](scripts/scaffold_docs_structure.py) 到目标项目 `scripts/`，跑一次：

```bash
python3 scripts/scaffold_docs_structure.py
```

它建好 docs/ 全部分类目录 + 每个目录的 `README.md`（写明用途和 `YYYYMMDD-[标题].md` 命名）+ `docs/docs-index.md` 骨架（含 DOCS-INDEX marker）。**幂等**：已存在的不动。
如果项目的分类需求和默认 taxonomy 不同，先改脚本顶部的 `CATEGORIES` 再跑（同时改 `update_docs_index.py` 的 `CATEGORIES` 保持一致）。

### 第 2 步：写 CLAUDE.md 入口（根 + 各子项目）

- **根 `CLAUDE.md`**：用 [`assets/claude_md_root_template.md`](assets/claude_md_root_template.md)。填项目概述、子项目表、文档索引指针、文档结构约定。
- **各子项目 `<service>/CLAUDE.md`**：用 [`assets/claude_md_subproject_template.md`](assets/claude_md_subproject_template.md)。填本子项目概述、技术栈、关键文档链接。

**保护已有**（关键）：CLAUDE.md 是 agent 指令文件，**绝不整体覆盖**。已存在时，只用 Edit 补上缺的「子项目列表 / 文档索引 / 核心文档」段；拿不准就先把现有内容读出来再决定插哪。

### 第 3 步：写各子项目架构文档

每个子项目一份 `docs/architecture/<service>.md`，用 [`assets/arch_doc_template.md`](assets/arch_doc_template.md)（11 节固定结构）。每节填实，不留 `[TODO]`。

**关键约束**：
- §2"目录结构"分两块：`<!-- AUTO-GENERATED:START/END -->` 自动区（脚本维护）+ 人工 `### 2.1 目录速览` 高层分组
- §9 模块依赖图用 ASCII art 或 Mermaid（用户偏好）
- 不写 `[TODO]`、`[占位]`、`稍后补充`；写不出来就走 [`references/sectioning_strategy.md`](references/sectioning_strategy.md) 拆小再写
- 不放手写代码示例（跟 dum-solution-design 同规则）；接口签名 / 类型契约可以，完整实现挪代码本身

### 第 4 步：配置自动更新脚本

**(a) 源码目录清单**（一服务一份）：复制 [`scripts/update_architecture_manifest.py`](scripts/update_architecture_manifest.py) 为 `scripts/update_architecture_<service>.py`，改顶部"项目配置"段：`ARCHITECTURE_MD_REL`（指向 `docs/architecture/<service>.md`）、`SCAN_SUBDIRS`、`INCLUDE_EXTENSIONS`、`EXTRACTOR`（语言相关，见 [`references/language_extractors.md`](references/language_extractors.md)）、`ROOT_LABEL`、`STRIP_SCAN_PREFIX`。

**(b) 分类文档索引**（一项目一份）：复制 [`scripts/update_docs_index.py`](scripts/update_docs_index.py)，一般不用改（默认就扫 `docs/` 全套分类写到 `docs/docs-index.md`）。只有当第 1 步改过 taxonomy 时，才同步它的 `CATEGORIES`。

**手动各跑一次验证**：首次输出 `Updated ... (N ...)`，再跑静默 (no diff)。

### 第 5 步：插入 / 确认 marker

- **源码清单**：打开 `docs/architecture/<service>.md` 的 §2，把占位 fence 换成 `<!-- AUTO-GENERATED:START -->` … `<!-- AUTO-GENERATED:END -->` 一对（中间放 ```\n(pending first run)\n``` ）。
- **文档索引**：scaffold 已在 `docs/docs-index.md` 里放好 `<!-- DOCS-INDEX:START/END -->`，确认即可。

然后各跑一次对应脚本，自动填好。

### 第 6 步：注册 PostToolUse hook

修改**项目根** `<project_root>/.claude/settings.local.json`（不是 `~/.claude/`）。骨架在 [`assets/hook_block.json`](assets/hook_block.json)。文件不存在则先建含 `permissions.allow: []` 的最小骨架再 merge `hooks` 段；**不要**用 update-config skill 整体重写，避免破坏已有 permission 列表。

每个子项目一个 `update_architecture_<service>.py` 项 + 一个项目级 `update_docs_index.py` 项，并列在 `hooks.PostToolUse[0].hooks` 里。`scaffold_docs_structure.py` 是一次性脚手架，**不进 hook**。

每个脚本内部按 `CLAUDE_TOOL_USE_INPUT.file_path` 自我过滤（源码脚本看路径关键字、文档索引看扩展名；不归它管的改动直接 exit 0），无关触发开销可忽略。

### 第 7 步：端到端验证

**必跑**（源码清单 + 文档索引各验一遍）：

1. **加源码文件**：Write 一个 `<scan_dir>/_test_marker.py`（或对应语言扩展名），就一个 docstring。预期：对应架构文档时间戳变、新文件进树。
2. **加文档文件**：Write 一个 `docs/tech-design/20260101-_test.md`，里面写 `# 测试`。预期：`docs-index.md` 的「技术方案」节出现这条、时间戳变。
3. **删文件**：`rm` 上面两个，再手动各跑一次脚本（hook 不触发删除）。预期：两处都干净移除。

时间戳没变的排查见 [`references/sectioning_strategy.md`](references/sectioning_strategy.md) 末尾 / 下方常见错误。

### 第 8 步：commit

```bash
git add CLAUDE.md "*/CLAUDE.md" docs/ scripts/scaffold_docs_structure.py \
        scripts/update_architecture_*.py scripts/update_docs_index.py \
        .claude/settings.local.json
```

commit message 模板见 [`references/commit_template.md`](references/commit_template.md)。

## 常见错误

| 错误 | 后果 | 修正 |
|---|---|---|
| 整体覆盖已有 CLAUDE.md | 抹掉用户的 agent 指令 | 只 Edit 补缺段，永不覆盖；拿不准先读出来 |
| scaffold 改了 `CATEGORIES` 但没同步 `update_docs_index.py` | 索引分类与目录对不上、某类文档不进索引 | 两个脚本的 `CATEGORIES` 必须一致 |
| 文档没写一级 `#` 标题 / frontmatter title | 索引里这条只剩文件名当标题 | 提取顺序 frontmatter title → 首个 `#` → 首行；补个好标题 |
| 文档命名不带日期（该带的类） | 索引里排到"无日期"段、丢失时间排序 | product-design / tech-design / report / modify_history / deffered 用 `YYYYMMDD-[标题].md` |
| 源码脚本扫了项目根不限定 SCAN_SUBDIRS | 把 `node_modules / .venv / dist` 全扫进去 | 严格按 `SCAN_SUBDIRS` 限定 |
| `STRIP_SCAN_PREFIX=False` 但 SCAN_SUBDIRS 是深路径（`apps/web/src`） | 树里路径重复嵌套 | 改 True，以 SCAN 入口为相对根 |
| 把 hook 写到 `~/.claude/settings.local.json` | 全局生效污染其它项目 | 写**项目根** `<project>/.claude/settings.local.json` |
| 把 `scaffold_docs_structure.py` 也塞进 hook | 每次 Write 都跑脚手架（无害但多余） | 脚手架只手动跑一次 |
| 架构文档没有 AUTO-GENERATED / 索引没有 DOCS-INDEX marker | 脚本 print warning 后 exit 0，永不更新 | 第 5 步先确认两对 marker 都在 |
| 手动编辑了 docs-index.md 的自动区 | 下次 hook 覆盖你的改动 | 自动区只读；要加说明写在 marker 外面 |

## Skill 内的资源

- [`scripts/scaffold_docs_structure.py`](scripts/scaffold_docs_structure.py) — 一次性脚手架：建 docs/ 全套分类目录 + README + docs-index.md 骨架（幂等、不覆盖）
- [`scripts/update_architecture_manifest.py`](scripts/update_architecture_manifest.py) — 源码目录清单脚本骨架（一服务一份），复制后改"项目配置"段
- [`scripts/update_docs_index.py`](scripts/update_docs_index.py) — 分类文档索引脚本（一项目一份），扫 docs/ 各分类写到 docs/docs-index.md
- [`assets/claude_md_root_template.md`](assets/claude_md_root_template.md) — 根 CLAUDE.md 模板（项目概述 / 子项目 / 文档索引 / 结构约定）
- [`assets/claude_md_subproject_template.md`](assets/claude_md_subproject_template.md) — 子项目 CLAUDE.md 模板
- [`assets/arch_doc_template.md`](assets/arch_doc_template.md) — 各子项目架构文档 11 节骨架（含 AUTO-GENERATED marker 占位）
- [`assets/hook_block.json`](assets/hook_block.json) — `.claude/settings.local.json` 的 hooks 段示例（源码脚本 + 文档索引脚本）
- [`references/sectioning_strategy.md`](references/sectioning_strategy.md) — 架构文档 11 节怎么写 + 文档索引怎么填、写不出来怎么拆
- [`references/language_extractors.md`](references/language_extractors.md) — Python / TS / Vue / Go / Rust / Java 源码描述提取规则
- [`references/commit_template.md`](references/commit_template.md) — 各阶段建议的 commit message 模板

## 出口判断

完成的标志（按顺序）：
1. ✅ `docs/` 全套分类目录存在，每个有 README.md（跑过 scaffold）
2. ✅ 根 `CLAUDE.md` 存在且非占位（含子项目列表 + 文档索引指针）；各子项目 `<service>/CLAUDE.md` 存在
3. ✅ `docs/architecture/<service>.md` 存在且非占位草稿，`<!-- AUTO-GENERATED:START -->` 后有真实源码树
4. ✅ `docs/docs-index.md` 的 `<!-- DOCS-INDEX:START -->` 后有按分类分节的真实文档列表（不是 `(pending first run)`）
5. ✅ `update_architecture_<service>.py` 和 `update_docs_index.py` 都手动跑两次，第二次静默
6. ✅ `.claude/settings.local.json` 的 `hooks.PostToolUse` 含每个服务的脚本 + 一个 `update_docs_index.py`
7. ✅ 端到端测试：加源码文件 + 加文档文件 → 两处时间戳各自变 → 删文件 → 手跑脚本 → 两处清干净
8. ✅ 一个 commit 完成所有更改，message 说明此 stage 的目的

漏任一项就还没完成，不要交付。
