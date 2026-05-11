---
name: dum-architecture-doc-build
description: 一次性生成项目的"程序架构文档"（按前后端 / 多服务拆分），并把目录清单接上 PostToolUse hook 实现 Write/Edit 后自动更新。触发场景：用户说"整理架构文档" / "生成架构说明" / "前端和后端架构文档" / "ARCHITECTURE.md" / "持续维护架构文档" / "文件变化后架构文档自动更新" / "auto-update arch doc" 等；或希望让 Claude 在动代码后自动同步目录树注释。约定输出位置 `docs/architecture/[service].md`（文件命名跟随项目惯例 backend/frontend/server/agent 等）。
---

# Dum Architecture Doc Build

## Overview

帮用户在一个 polyrepo / monorepo 项目里建立**架构说明文档**（按服务/进程拆分，一份一文件），并接上 **PostToolUse hook** 让目录清单区域在每次 Write/Edit 后自动同步。

两阶段：

1. **首次生成** — 调研项目结构，写一份手工的架构说明（10 节模板），标注 `<!-- AUTO-GENERATED:START/END -->` 段
2. **接 hook** — 写一个扫描脚本（按目录/语言定制），登记到 `.claude/settings.local.json` 的 `hooks.PostToolUse`，每次 Write/Edit 触发刷新

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

把摸底结果写进对话（不要存文件），然后跟用户确认要拆几份文档。常见决策：
- monorepo 前后端分离 → `docs/architecture/backend.md` + `docs/architecture/frontend.md`
- 三服务（client / agent_server / server）→ 三份各自一份
- 单服务但分多语言层（如 Electron main+renderer+preload）→ 一份内分大节

### 第 1 步：写主文档骨架

用 [`assets/arch_doc_template.md`](assets/arch_doc_template.md) 作为骨架（11 节固定结构）。每节填实内容，不要留 `[TODO]`。

**关键约束**：
- 第 2 节"目录结构"必须分两块：`<!-- AUTO-GENERATED:START/END -->` 自动生成区（脚本维护），**外加**人工维护的 `### 2.1 目录速览` 高层分组（保留 onboarding 用）
- 第 9 节模块依赖图用 ASCII art 或 Mermaid（用户偏好）
- 不写 `[TODO]`、`[占位]`、`稍后补充` 这类草稿语；写不出来就走 [`references/sectioning_strategy.md`](references/sectioning_strategy.md) 看怎么拆得更小再写
- 主文档不放手写代码示例（跟 dum-solution-design 同规则）；接口签名、类型定义可以；完整实现挪到代码本身

### 第 2 步：实现自动更新脚本

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

### 第 3 步：在主文档插入 marker

打开第 1 步写好的 `docs/architecture/<service>.md`，找到 `## 2. 目录结构（自动生成区域）`节，把里面的占位 fence 替换成：

````markdown
<!-- AUTO-GENERATED:START -->
<!-- 占位：首次运行 scripts/update_architecture_<service>.py 后自动填充 -->
```
(pending first run)
```
<!-- AUTO-GENERATED:END -->
````

然后跑一次脚本（第 2 步第 4 条），自动填好。

### 第 4 步：注册 PostToolUse hook

修改 `<project_root>/.claude/settings.local.json`（不是 `~/.claude/`，是**项目根**下的）。骨架在 [`assets/hook_block.json`](assets/hook_block.json)。

如果文件不存在，先创建包含 `permissions.allow: []` 的最小骨架，再 merge `hooks` 段。**不要**用 update-config skill 强行重写整个文件，避免破坏用户已有的 permission 列表。

每个服务对应一个 hook entry。多个服务并列在 `hooks.PostToolUse[0].hooks` 数组里：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/update_architecture_backend.py\"", "timeout": 10 },
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/update_architecture_frontend.py\"", "timeout": 10 }
        ]
      }
    ]
  }
}
```

每个脚本内部通过 `CLAUDE_TOOL_USE_INPUT.file_path` 自我过滤（不是它管辖的服务直接 exit 0），所以"无关文件触发"开销可忽略（< 10 ms）。

### 第 5 步：端到端验证

**关键步骤，必跑**：

1. **加文件验证**：用 Write 工具创建一个 `<scan_dir>/_test_marker.py`（或对应语言的扩展名），文件里就一个 docstring。预期：架构文档 `<!-- 最后更新: ... -->` 时间戳变化，新文件出现在树里。
2. **删文件验证**：`rm <scan_dir>/_test_marker.py`，再手动跑一次脚本（hook 不触发删除事件）。预期：树里干净移除。

如果第 1 步时间戳没变：
- 看脚本是否真被 hook 触发：临时在脚本顶部加 `print(f"[hook] {sys.argv}", file=sys.stderr)`
- 看 `.claude/settings.local.json` 是否合法 JSON（`python3 -c "import json; json.load(open('.claude/settings.local.json'))"`）
- 看 hook 是否需要重启 Claude Code session（settings.local.json 中途修改有时不会即时生效）
- 排除"只改了描述没改结构"的情况（脚本设计是只在树形**结构**变化时重写，避免噪音 commit）—— 这种情况手动跑一次确认能更新就行

### 第 6 步：commit

`git add scripts/update_architecture_*.py docs/architecture/*.md .claude/settings.local.json`

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

## Skill 内的资源

- [`scripts/update_architecture_manifest.py`](scripts/update_architecture_manifest.py) — 通用脚本骨架，复制到目标项目按"项目配置"段改即可
- [`assets/arch_doc_template.md`](assets/arch_doc_template.md) — 主文档 11 节骨架（含 marker 占位）
- [`assets/hook_block.json`](assets/hook_block.json) — `.claude/settings.local.json` 的 hooks 段示例
- [`references/sectioning_strategy.md`](references/sectioning_strategy.md) — 11 节模板每节怎么写、写不出来怎么拆
- [`references/language_extractors.md`](references/language_extractors.md) — Python / TS / Vue / Go / Rust / Java 描述提取规则
- [`references/commit_template.md`](references/commit_template.md) — 各阶段建议的 commit message 模板

## 出口判断

完成的标志（按顺序）：
1. ✅ `docs/architecture/<service>.md` 存在且非占位草稿
2. ✅ `<!-- AUTO-GENERATED:START -->` 后面有真实树形（不是 `(pending first run)`）
3. ✅ `scripts/update_architecture_<service>.py` 手动跑两次，第二次静默
4. ✅ `.claude/settings.local.json` 里 `hooks.PostToolUse` 包含每个服务的脚本
5. ✅ 端到端测试：加文件 → 时间戳变 → 删文件 → 手跑脚本 → 树清干净
6. ✅ 一个 commit 完成所有更改，message 说明此 stage 的目的

漏任一项就还没完成，不要交付。
