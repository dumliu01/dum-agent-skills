---
name: dum-architecture-doc-build
description: 一次性生成项目的"程序架构文档"（按前后端 / 多服务拆分）+ 一份"知识库索引 / 文档地图"，并把源码目录清单和文档清单都接上 PostToolUse hook 实现 Write/Edit 后自动更新。触发场景：用户说"整理架构文档" / "生成架构说明" / "前端和后端架构文档" / "ARCHITECTURE.md" / "持续维护架构文档" / "文件变化后架构文档自动更新" / "auto-update arch doc" / "知识库文档" / "文档地图" / "哪些文档在哪些目录" / "doc map" 等；或希望让 Claude 在动代码后自动同步目录树注释、动文档后自动同步文档索引。约定输出位置 `docs/architecture/[service].md`（文件命名跟随项目惯例 backend/frontend/server/agent 等）+ `docs/architecture/README.md`（知识库索引）。
---

# Dum Architecture Doc Build

## Overview

帮用户在一个 polyrepo / monorepo 项目里建立**架构说明文档**（按服务/进程拆分，一份一文件）+ 一份**知识库索引 / 文档地图**，并接上 **PostToolUse hook** 让两类自动区在每次 Write/Edit 后同步。

**两类自动维护的清单**（这是本 skill 的核心产出）：

| 清单 | 回答的问题 | 脚本 | 写到哪 | 标记 |
|---|---|---|---|---|
| **源码目录清单** | 「**代码**有哪些、在哪些目录」 | `update_architecture_<service>.py`（一服务一份） | 各服务架构文档 §2 | `<!-- AUTO-GENERATED -->` |
| **文档地图** | 「**文档**有哪些、在哪些目录」 | `update_doc_map.py`（一项目一份） | `docs/architecture/README.md` | `<!-- DOC-MAP -->` |

两脚本同源同设计（幂等 / 静默 / 自我过滤 / 树形渲染），互为姊妹。文档地图让架构文档不只描述代码，也成为整个项目文档的**入口索引**——读者一眼看清方案设计 / ADR / stage history / CLAUDE.md 等都在哪。

两阶段：

1. **首次生成** — 调研项目结构，写各服务架构说明（11 节模板）+ 一份知识库索引页，标注 `<!-- AUTO-GENERATED -->` / `<!-- DOC-MAP -->` 段
2. **接 hook** — 把扫描脚本（源码脚本按服务定制 + 一个文档地图脚本）登记到 `.claude/settings.local.json` 的 `hooks.PostToolUse`，每次 Write/Edit 触发刷新

## 触发判断

**应该触发**：
- 用户明确要求生成 / 整理 / 维护"架构文档"、"程序架构"、"ARCHITECTURE.md"
- 用户提供参考文档（如 `termcat_*/claude_refs/ARCHITECTURE.md` 风格）希望仿写
- 用户要求"文件变更后自动更新文档"、"持续维护目录清单"、"auto-update arch doc"
- 项目代码已稳定，但缺少俯瞰全图的入口文档

**不应触发**：
- 用户只想要 README（用户/产品视角，不是开发者视角）
- 用户问"代码改了哪里"（git log 即可，不要重写架构文档）
- 单文件 / 小脚本项目（< 20 个源文件，不值得引入这套机制）

## 工作流（按顺序，跳一步说原因）

### 第 0 步：摸底

调研当前项目的拓扑：
1. **服务/进程数** — 看 `apps/`、`services/`、`packages/`、根级 `cmd/` 等。一个进程一份文档，不要塞一起
2. **每个服务的语言** — Python / TypeScript / Vue / Go / Rust / Java，影响"描述提取"规则
3. **顶层目录** — 列出每个服务里的核心目录（比如 Python 后端的 `core / apps / infra`，前端的 `apps/web/src`）
4. **是否已存在 `docs/architecture/`、`claude_refs/` 等** — 已有则增量补充，没有则新建 `docs/architecture/`
5. **文档分布盘点** — 项目里散落哪些 `.md` 文档、在哪些目录？典型集散地：`docs/`、`方案设计/`（dum-solution-design 产出）、`claude_refs/`、`docs/资料/`(stage history)、ADR 目录、根级 `CLAUDE.md` / `README.md`。这决定文档地图脚本要不要收窄扫描范围，以及哪些目录是噪音（`node_modules` 自带 README 等）

把摸底结果写进对话（不要存文件），然后跟用户确认要拆几份文档。常见决策：
- monorepo 前后端分离 → `docs/architecture/backend.md` + `docs/architecture/frontend.md` + `docs/architecture/README.md`(知识库索引)
- 三服务（client / agent_server / server）→ 三份各自一份 + 一份索引
- 单服务但分多语言层（如 Electron main+renderer+preload）→ 一份内分大节，文档地图直接嵌进这一份（DOC-MAP 标记跟 §2 的 AUTO-GENERATED 标记共存即可）

### 第 1 步：写主文档骨架 + 知识库索引页

**(a) 各服务架构文档**：用 [`assets/arch_doc_template.md`](assets/arch_doc_template.md) 作为骨架（11 节固定结构）。每节填实内容，不要留 `[TODO]`。

**关键约束**：
- 第 2 节"目录结构"必须分两块：`<!-- AUTO-GENERATED:START/END -->` 自动生成区（脚本维护），**外加**人工维护的 `### 2.1 目录速览` 高层分组（保留 onboarding 用）
- 第 9 节模块依赖图用 ASCII art 或 Mermaid（用户偏好）
- 不写 `[TODO]`、`[占位]`、`稍后补充` 这类草稿语；写不出来就走 [`references/sectioning_strategy.md`](references/sectioning_strategy.md) 看怎么拆得更小再写
- 主文档不放手写代码示例（跟 dum-solution-design 同规则）；接口签名、类型定义可以；完整实现挪到代码本身

**(b) 知识库索引页**：用 [`assets/arch_index_template.md`](assets/arch_index_template.md) 写 `docs/architecture/README.md`。它有三块：① 各服务架构文档链接表；② 人工维护的「必读导航」（按 onboarding 顺序挑 3-8 个关键文档）；③ `<!-- DOC-MAP:START/END -->` 自动生成的全项目文档地图。单服务项目可省掉独立索引页，把 DOC-MAP 标记直接放进那一份架构文档（与 AUTO-GENERATED 标记共存）。怎么填见 [`references/sectioning_strategy.md`](references/sectioning_strategy.md) 的「文档地图」节。

### 第 2 步：实现自动更新脚本

需要两类脚本：源码清单脚本（一服务一个）+ 文档地图脚本（一项目一个）。

#### (a) 源码目录清单脚本

每个服务一个脚本，路径规范：`scripts/update_architecture_<service>.py`（如果项目已有 `scripts/` 目录则放进去，否则新建）。

骨架在 [`scripts/update_architecture_manifest.py`](scripts/update_architecture_manifest.py)。**直接复制**这个文件到目标项目，然后：

1. 把顶部的 `--- 项目配置 ---` 段改成本项目的实际值：
   - `ARCHITECTURE_MD` — 指向 `docs/architecture/<service>.md`
   - `SCAN_SUBDIRS` — 列出本服务的源代码顶层目录（相对项目根）
   - `TRIGGER_KEYWORDS` — 通常等于 `tuple(SCAN_SUBDIRS)`，hook 触发时按这个过滤
   - `INCLUDE_EXTENSIONS` — `.py` 后端 / `.ts .vue` 前端 / `.go` Go / `.rs` Rust ...
   - `EXTRACTOR` — 选语言相关的提取器名（见下条）

2. 选/写"描述提取器"。骨架里有三个内置：
   - `extract_python_docstring` — `ast.get_docstring` 取模块 docstring 首行（Python 标准）
   - `extract_first_comment` — 首个 `// xxx` / `/* xxx */` / JSDoc 单行注释（TS/JS/Vue/Go/Rust/C/C++ 都能用）
   - `extract_yaml_top_comment` — YAML 文件首行 `# xxx`
   - 其它语言（如 Java javadoc、Rust `///`）参考 [`references/language_extractors.md`](references/language_extractors.md) 自己加

3. 调整 `ROOT_LABEL`（树根那一行的显示，通常是服务名）和 `STRIP_SCAN_PREFIX`（前端这种 `apps/web/src` 类深嵌套要设 True 避免树里 path 重复嵌套）

4. **手动跑一次验证**：
   ```bash
   python3 scripts/update_architecture_<service>.py
   ```
   首次跑应该输出 `Updated docs/architecture/<service>.md (N files)`；再跑一次应该静默 (no diff)。

#### (b) 文档地图脚本

整个项目**一个** `scripts/update_doc_map.py`（不按服务拆）。骨架在 [`scripts/update_doc_map.py`](scripts/update_doc_map.py)。**直接复制**，然后改顶部「项目配置」段：

- `DOC_MAP_MD_REL` — 指向知识库索引页（默认 `docs/architecture/README.md`；单服务可指向那一份架构文档）
- `DOC_SCAN_DIRS` — 默认 `["."]` 扫全项目（靠 `EXCLUDE_DIRS` + 自动跳过 dotdir 兜底）；文档很散且噪音多时收窄成白名单，如 `["docs", "方案设计", "claude_refs"]`
- `DOC_EXTENSIONS` — 默认 `{".md"}`；按需加 `.mdx` / `.rst` / `.adoc`
- `ROOT_LABEL` — 项目名
- `EXCLUDE_FILES` — 默认排除 `CHANGELOG.md` / `LICENSE.md`（机器生成 / 非知识库）；按需加

描述提取器是内置的 `extract_doc_title`：frontmatter `title`/`description` → 首个 `#` 标题 → 首行非空正文，不用改。跟源码脚本的两点差异：① hook 触发时按"被改文件扩展名是不是文档"过滤（不是按路径关键字）；② 文档地图把**描述也纳入 diff**——文档标题改了也刷新（源码脚本为避免噪音只在树形结构变化时刷新）。

手动验证同上：首次 `Updated docs/architecture/README.md (N docs)`，再跑静默。

### 第 3 步：在文档里插入 marker

两类 marker：

**(a) 源码清单** — 打开 `docs/architecture/<service>.md` 的 `## 2. 目录结构（自动生成区域）`节，把占位 fence 替换成：

````markdown
<!-- AUTO-GENERATED:START -->
<!-- 占位：首次运行 scripts/update_architecture_<service>.py 后自动填充 -->
```
(pending first run)
```
<!-- AUTO-GENERATED:END -->
````

**(b) 文档地图** — `docs/architecture/README.md` 用了 [`assets/arch_index_template.md`](assets/arch_index_template.md) 的话，`<!-- DOC-MAP:START/END -->` 已经在里面了，跳过本条。否则手动插一对 DOC-MAP marker（结构同上，markers 换成 `DOC-MAP`）。

然后各跑一次对应脚本（第 2 步），自动填好。

### 第 4 步：注册 PostToolUse hook

修改 `<project_root>/.claude/settings.local.json`（不是 `~/.claude/`，是**项目根**下的）。骨架在 [`assets/hook_block.json`](assets/hook_block.json)。

如果文件不存在，先创建包含 `permissions.allow: []` 的最小骨架，再 merge `hooks` 段。**不要**用 update-config skill 强行重写整个文件，避免破坏用户已有的 permission 列表。

每个服务一个 hook entry，**外加一个项目级的 `update_doc_map.py`**（只需一个），并列在 `hooks.PostToolUse[0].hooks` 数组里：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/update_architecture_backend.py\"", "timeout": 10 },
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/update_architecture_frontend.py\"", "timeout": 10 },
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/update_doc_map.py\"", "timeout": 10 }
        ]
      }
    ]
  }
}
```

每个脚本内部通过 `CLAUDE_TOOL_USE_INPUT.file_path` 自我过滤（源码脚本看路径关键字、文档地图看扩展名；不归它管的改动直接 exit 0），所以"无关文件触发"开销可忽略（< 10 ms）。

### 第 5 步：端到端验证

**关键步骤，必跑**（源码清单 + 文档地图各验一遍）：

1. **加源码文件**：用 Write 工具创建一个 `<scan_dir>/_test_marker.py`（或对应语言的扩展名），文件里就一个 docstring。预期：架构文档 `<!-- 最后更新: ... -->` 时间戳变化，新文件出现在树里。
2. **加文档文件**：用 Write 工具创建一个 `docs/_test_marker.md`，里面写个 `# 测试`。预期：`docs/architecture/README.md` 的 DOC-MAP 区出现这条、时间戳变化。
3. **删文件验证**：`rm <scan_dir>/_test_marker.py docs/_test_marker.md`，再手动各跑一次脚本（hook 不触发删除事件）。预期：两个树里都干净移除。

如果时间戳没变：
- 看脚本是否真被 hook 触发：临时在脚本顶部加 `print(f"[hook] {sys.argv}", file=sys.stderr)`
- 看 `.claude/settings.local.json` 是否合法 JSON（`python3 -c "import json; json.load(open('.claude/settings.local.json'))"`）
- 看 hook 是否需要重启 Claude Code session（settings.local.json 中途修改有时不会即时生效）
- 排除"只改了描述没改结构"的情况（脚本设计是只在树形**结构**变化时重写，避免噪音 commit）—— 这种情况手动跑一次确认能更新就行

### 第 6 步：commit

`git add scripts/update_architecture_*.py scripts/update_doc_map.py docs/architecture/*.md .claude/settings.local.json`

commit message 模板见 [`references/commit_template.md`](references/commit_template.md)。

## 常见错误

| 错误 | 后果 | 修正 |
|---|---|---|
| 骨架脚本扫描了项目根而不是限定到 SCAN_SUBDIRS | 把 `node_modules / .venv / dist` 全扫进去 | 严格按 `SCAN_SUBDIRS` 限定 |
| `STRIP_SCAN_PREFIX=False` 但 SCAN_SUBDIRS 里是深路径（如 `apps/web/src`） | 树形结构里出现 `apps/web/src/ → apps/ → web/ → src/` 重复嵌套 | 改为 True，让脚本以 SCAN 入口目录为相对根 |
| 描述提取器对 .vue 文件直接读首行注释 | 拿到 `<template>` 注释或空字符串 | 用 [`references/language_extractors.md`](references/language_extractors.md) 里的 .vue 专用提取器（先定位 `<script>` 块） |
| 把 hook 写到 `~/.claude/settings.local.json` | 全局生效，污染其它项目 | 写到**项目根** `<project>/.claude/settings.local.json` |
| 主文档 ARCHITECTURE.md 与脚本里的路径不一致 | 脚本静默 exit 0，文档永远不更新 | 脚本里 `ARCHITECTURE_MD = PROJECT_ROOT / "docs" / "architecture" / "<service>.md"` 必须与实际文件位置一致 |
| 主文档没有 `<!-- AUTO-GENERATED:START/END -->` marker | 脚本 print warning 后 exit 0 | 第 3 步必须先插 marker |
| hook 的 timeout 太短（< 5s） | 大项目扫描超时 | 默认 10s，超过 200 文件用 15s |
| 同时改了主文档手写区和脚本生成区然后 commit | git diff 满屏，不知谁先谁后 | 分两 commit：先改主文档手写区 → 跑脚本 → 单独 commit 自动区改动 |
| 文档地图 `DOC_SCAN_DIRS=["."]` 但项目里有未被 `EXCLUDE_DIRS` 覆盖的 vendored 目录（如 `third_party/`、`examples/`） | 一堆依赖自带 README 涌进文档地图 | 把目录加进 `EXCLUDE_DIRS`，或把 `DOC_SCAN_DIRS` 收窄成白名单 |
| 给每个服务都建了一个 `update_doc_map.py` | 多份文档地图互相覆盖 / 重复 | 文档地图是**项目级**，全项目只建一个，写到一份索引页 |
| 文档地图脚本和源码脚本指向同一份文档但用同一对 marker | 后跑的脚本覆盖前一个的输出 | 源码用 `AUTO-GENERATED`、文档地图用 `DOC-MAP`，两对 marker 不能混用 |
| 文档没有一级 `#` 标题 / frontmatter title | 文档地图里这条只有路径没有描述 | 给文档补个一级标题（提取器优先 frontmatter title → 首个 `#` → 首行正文） |

## Skill 内的资源

- [`scripts/update_architecture_manifest.py`](scripts/update_architecture_manifest.py) — 源码目录清单脚本骨架（一服务一份），复制后按"项目配置"段改
- [`scripts/update_doc_map.py`](scripts/update_doc_map.py) — 文档地图脚本骨架（一项目一份），扫全项目 `.md` 建知识库索引
- [`assets/arch_doc_template.md`](assets/arch_doc_template.md) — 各服务架构文档 11 节骨架（含 AUTO-GENERATED marker 占位）
- [`assets/arch_index_template.md`](assets/arch_index_template.md) — 知识库索引页骨架 `docs/architecture/README.md`（含 DOC-MAP marker 占位）
- [`assets/hook_block.json`](assets/hook_block.json) — `.claude/settings.local.json` 的 hooks 段示例（含源码脚本 + 文档地图脚本）
- [`references/sectioning_strategy.md`](references/sectioning_strategy.md) — 11 节模板每节怎么写 + 文档地图怎么填、写不出来怎么拆
- [`references/language_extractors.md`](references/language_extractors.md) — Python / TS / Vue / Go / Rust / Java 描述提取规则
- [`references/commit_template.md`](references/commit_template.md) — 各阶段建议的 commit message 模板

## 出口判断

完成的标志（按顺序）：
1. ✅ `docs/architecture/<service>.md` 存在且非占位草稿
2. ✅ `<!-- AUTO-GENERATED:START -->` 后面有真实树形（不是 `(pending first run)`）
3. ✅ `docs/architecture/README.md` 知识库索引页存在，`<!-- DOC-MAP:START -->` 后面有真实文档树（覆盖到 `方案设计/` / `claude_refs/` / `docs/` 等各处文档）
4. ✅ `scripts/update_architecture_<service>.py` 和 `scripts/update_doc_map.py` 都手动跑两次，第二次静默
5. ✅ `.claude/settings.local.json` 里 `hooks.PostToolUse` 包含每个服务的脚本 + 一个 `update_doc_map.py`
6. ✅ 端到端测试：加源码文件 + 加文档文件 → 两份时间戳各自变 → 删文件 → 手跑脚本 → 两树清干净
7. ✅ 一个 commit 完成所有更改，message 说明此 stage 的目的

漏任一项就还没完成，不要交付。
