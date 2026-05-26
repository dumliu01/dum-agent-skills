# Changelog

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [1.1.0] - 2026-05-26

### Added
- **新技能 `dum-arch-spec-doc`**：给单个服务按语言（前端 / Go / Python，另带 generic 骨架）
  生成**分离的两份**文档——程序架构文档（`docs/architecture/<service>.md`，描述性）+
  开发规范文档（`docs/specification/<service>-规范.md`，规范性）。
  含 8 个语言模板 + 2 篇 references（架构 vs 规范拆分 taxonomy、各语言章节速查）。

### Changed (Breaking)
- **重命名技能** `dum-architecture-doc-build` → **`dum-knowledge-base-build`**。
  原名"只搭架构文档"太窄，新名更贴合它实际承担的"搭整套知识库框架"职责
  （docs/ 分类目录 + CLAUDE.md 入口 + 文档索引 + PostToolUse hook）。
  - **升级路径**：装了本插件的用户跑 `claude plugin update dum-agent-skills` 后，
    旧名 `dum-architecture-doc-build` 会消失、新名 `dum-knowledge-base-build` 出现；
    任何写死旧名的脚本 / 文档 / 工作流需手动改为新名。
  - 仓库内的交叉引用、`CLAUDE.md` / `README.md` / `GEMINI.md` 索引、
    `dum-session-summary` 等其它 skill 对它的引用、目录内 3 个脚本里的注释，均已同步更新。

### Docs
- `CLAUDE.md` / `README.md` / `GEMINI.md`：技能清单加 `dum-arch-spec-doc` 行；
  「技能相互衔接」段补充与 `dum-knowledge-base-build` 的分工说明。

## [1.0.0] - 2026-05-25

首个正式版多 agent 插件发布。技能集合：
- `dum-architecture-doc-build`（在 1.1.0 重命名为 `dum-knowledge-base-build`）
- `dum-solution-design`
- `dum-doc-reconcile`
- `dum-session-summary`
- `dum-ppt`

打包为 Claude Code / Codex / Gemini CLI / Cursor 四套 manifest，正文集中于 `skills/`。
