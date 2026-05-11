# Commit message 模板

按 stage 分两次 commit（避免一坨 diff 看不清结构）。

## Commit 1：架构文档骨架

```
docs(architecture): add {{service-1}} + {{service-2}} architecture docs

- docs/architecture/{{service-1}}.md (N lines): {{进程模型}} + {{核心模块}}
  + {{对外接口}} + {{持久化}} + {{测试}} + {{构建}} + {{依赖图}} +
  {{N 条 invariant}}
- docs/architecture/{{service-2}}.md (M lines): {{...}}

Format mirrors {{参考来源}} (e.g., termcat_*/claude_refs/ARCHITECTURE.md
references; or whatever the user pointed you at).
```

文件清单：
- `docs/architecture/<service>.md` × N

## Commit 2：自动更新 infrastructure

```
feat(docs): auto-update architecture manifests on Write|Edit

- scripts/update_architecture_{{service-1}}.py: walks {{SCAN_SUBDIRS}};
  extracts {{描述来源}} from each {{扩展名}}; writes between AUTO-GENERATED
  markers in docs/architecture/{{service-1}}.md (N files indexed).
- scripts/update_architecture_{{service-2}}.py: walks {{...}}; extracts
  {{...}} from each {{...}} (M files).
- Both scripts: silent no-op when AUTO-GENERATED markers absent;
  filter by CLAUDE_TOOL_USE_INPUT.file_path so each hook only re-runs
  on its own service's file changes; rewrites only on tree-shape
  changes (descriptions ignored to avoid noisy timestamp diffs).
- .claude/settings.local.json: PostToolUse hook on Write|Edit invokes
  both scripts (10s timeout each).
- {{service-1}}.md / {{service-2}}.md: section 2 split into
  auto-generated tree + manually-curated speed-read view (§2.1).

Pattern lifted from {{参考来源}} (e.g., termcat_agent_server/scripts/
update_architecture_manifest.py).
```

文件清单：
- `scripts/update_architecture_<service>.py` × N
- `docs/architecture/<service>.md` × N（自动生成区填好后会再 diff）
- `.claude/settings.local.json`

## 如果一次性提交（小项目）

```
docs(architecture): {{service-1}} + {{service-2}} arch docs + auto-update hook

- docs/architecture/{{service-1}}.md + {{service-2}}.md: 11-section
  template (overview / dir structure / module deep-dives / API surface /
  config / persistence / tests / build / dep graph / invariants / status)
- scripts/update_architecture_{{service-{1,2}}}.py: scan SCAN_SUBDIRS,
  extract {{描述来源}}, write between AUTO-GENERATED markers; filter by
  CLAUDE_TOOL_USE_INPUT.file_path; rewrite only on tree-shape changes
- .claude/settings.local.json: PostToolUse Write|Edit hook (10s timeout)

End-to-end verified: Write new file → arch doc timestamp updates +
new file appears in tree; rm + manual rerun → tree cleanly removes it.
```

## 反模式（避免）

- ❌ commit message 里写"docs: update arch"（信息密度过低，未来 git log 看不到关键变更）
- ❌ 把脚本和文档分两个独立 commit 但脚本 commit 在前（脚本会立刻在第一次 hook 触发时改文档，之后就分不清"自动生成 vs 手写"的边界）
- ❌ 把端到端验证细节也写进 commit body（保留在脑子里 / TIL 里，commit body 关注"做了什么"而非"怎么验证"）
