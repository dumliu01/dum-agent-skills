# Changelog

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [1.1.2] - 2026-05-26

### Changed
- **`dum-arch-spec-doc` 日志规范模板补完**：原 `go-specification.md` §6 与
  `frontend-specification.md` §10 只有寥寥几行（"用统一 logger / 禁止裸打印"），生成的
  规范文档不够实操。参考 termcat_server / termcat_client 实际约定，按多维度展开：
  - **Go**（5 个子节）：Logger 使用 · 级别(DEBUG/INFO/ERROR + `LOG_LEVEL`) ·
    格式与结构化字段(固定单行格式 + `WithFields`) · 文件与按日轮转(`LOG_DIR` /
    `LOG_RETAIN_DAYS` / `<svc>-YYYY-MM-DD.log`) · 敏感信息脱敏(含 IP 尾段脱敏)
  - **前端**（6 个子节）：Logger 使用(两种调用形式) · 级别(DEBUG/INFO/WARN/ERROR) ·
    事件键命名(`<domain>.<entity>.<action>`) · 模块常量(`LOG_MODULE` 枚举) ·
    文件存储与轮转(按 OS 路径 + 10MB/5 文件) · 敏感信息脱敏(HTTP 拦截器剥离 + 命令脱敏)
  - 全部祈使句 + ✅/❌ 例子，项目特定值保留 `{{...}}` 占位。
  - Python 模板未动（无对应参考），日后按需补齐。

## [1.1.1] - 2026-05-26

### Fixed
- **`docs-index.md` 默认落点改回 `docs/` 根**：原先 `dum-knowledge-base-build` 与
  `dum-arch-spec-doc` 把分类文档索引放到 `docs/reference/docs-index.md`，使用中发现
  它被埋在子目录里、不再像"docs/ 总入口"。现统一为 **`docs/docs-index.md`**；
  `reference/` 分类目录保留，但只承担"参考资料 / 外部链接"角色，不再装索引文件。
  涉及 14 个文件 / 27 处路径 + 2 个脚本常量（`scaffold_docs_structure.py`、
  `update_docs_index.py`）+ 3 棵目录树插图 + 1 处 scaffold 给 reference/ 写的描述。
  - **升级影响**：老项目里 `docs/reference/docs-index.md` 仍可读，新生成的会落到
    `docs/docs-index.md`。若想统一，把老文件 `git mv` 过去再跑一次脚本即可。

### Added
- **各技能的「介绍文档」**（`skills/<name>/README.md`）：人类视角的概览
  （一句话定位 / 它做什么 / 何时触发 / 它交付什么 / 跟其它技能怎么衔接 / 指向 SKILL.md），
  6 个技能各一篇。主 `README.md` 技能一览表加一列「完整工作流」直接指向 `SKILL.md`，
  并在 GitHub 上点进任何 `skills/<name>/` 都会自动渲染对应介绍。

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
