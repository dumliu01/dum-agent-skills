# Commit message 模板

按 stage 分 commit（避免一坨 diff 看不清结构）。三段：① 知识库骨架 + 文档内容；② 自动更新 infrastructure。小项目可合一。

## Commit 1：知识库结构 + 文档内容

```
docs: scaffold knowledge base + {{service-1}}/{{service-2}} arch docs

- scaffold docs/ taxonomy (architecture / specification / product-design /
  tech-design / superpowers / modify_history / deffered / manual_deployment /
  manual_userguides / report / reference), each with a README
- CLAUDE.md (root): project overview + sub-project table + doc index
- {{service-1}}/CLAUDE.md, {{service-2}}/CLAUDE.md: sub-project entries
- docs/architecture/{{service-1}}.md + {{service-2}}.md: 11-section template
  (overview / dir structure / modules / API / config / persistence / tests /
  build / dep graph / invariants / status)
- docs/reference/docs-index.md: doc index skeleton (DOCS-INDEX markers)
```

文件清单：
- 根 `CLAUDE.md` + 各 `<service>/CLAUDE.md`
- `docs/**/README.md`（脚手架生成）+ `docs/architecture/<service>.md` × N
- `docs/reference/docs-index.md`

## Commit 2：自动更新 infrastructure

```
feat(docs): auto-update source manifests + doc index on Write|Edit

- scripts/scaffold_docs_structure.py: one-shot idempotent scaffolder for
  the docs/ taxonomy (never overwrites existing).
- scripts/update_architecture_{{service-1,2}}.py: walk {{SCAN_SUBDIRS}};
  extract {{描述来源}}; write between AUTO-GENERATED markers in
  docs/architecture/<service>.md; rewrite only on tree-shape changes.
- scripts/update_docs_index.py: scan docs/ by category, parse
  YYYYMMDD-title filenames, render a categorized index (newest-first)
  between DOCS-INDEX markers in docs/reference/docs-index.md. Title
  changes DO refresh (unlike source manifests).
- All scripts filter by CLAUDE_TOOL_USE_INPUT.file_path; silent no-op
  when markers absent.
- .claude/settings.local.json: PostToolUse Write|Edit hook invokes the
  per-service manifests + update_docs_index.py (10s timeout each).
```

文件清单：
- `scripts/scaffold_docs_structure.py`
- `scripts/update_architecture_<service>.py` × N
- `scripts/update_docs_index.py`
- `docs/architecture/<service>.md` × N + `docs/reference/docs-index.md`（自动区填好后会再 diff）
- `.claude/settings.local.json`

## 如果一次性提交（小项目）

```
docs: knowledge base — docs/ taxonomy + CLAUDE.md + arch docs + auto-update hook

- scaffold docs/ taxonomy with per-dir READMEs; root + sub-project CLAUDE.md
- docs/architecture/<service>.md: 11-section arch docs (AUTO-GENERATED tree)
- docs/reference/docs-index.md: categorized doc index (DOCS-INDEX, auto)
- scripts/{scaffold_docs_structure,update_architecture_<service>,update_docs_index}.py
- .claude/settings.local.json: PostToolUse Write|Edit hook (10s timeout)

End-to-end verified: Write new code file → arch doc updates; Write new
docs/**/*.md → docs-index updates; rm + manual rerun → both clean up.
```

## 反模式（避免）

- ❌ commit message 里写"docs: update arch"（信息密度过低，未来 git log 看不到关键变更）
- ❌ 整体覆盖已有 CLAUDE.md（抹掉用户 agent 指令）——只补缺段
- ❌ 把脚本和文档分两个独立 commit 但脚本 commit 在前（脚本会立刻在第一次 hook 触发时改文档，之后就分不清"自动生成 vs 手写"的边界）
- ❌ 把端到端验证细节也写进 commit body（commit body 关注"做了什么"而非"怎么验证"）
