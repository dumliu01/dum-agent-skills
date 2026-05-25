# Dum Agent Skills

一组可复用的工作流技能（skills），覆盖文档体系搭建、技术方案设计、文档对账、会话总结、PPT 生成。
作为**多 agent 插件**发布：技能正文集中放在 `skills/`，各 agent 生态各有一份薄 manifest 指向它。

> 给 AI agent：当用户请求命中某技能的「触发场景」时，**先完整读取该技能的 `SKILL.md`**，
> 再按其中步骤执行。不要只凭下表的一句话摘要就动手。

## 技能清单

| 技能 | 何时用 | 入口 |
|---|---|---|
| **dum-architecture-doc-build** | 给项目搭建/维护知识库文档体系：脚手架 `docs/` 分类目录 + 根与子项目 `CLAUDE.md` 入口 + 各服务架构文档 + 自动维护的源码清单与文档索引。触发："整理架构文档"/"搭建知识库"/"文档体系"/"文档索引" | `skills/dum-architecture-doc-build/SKILL.md` |
| **dum-solution-design** | 出结构化技术方案（架构/时序/关键逻辑/接口/遗留 五段 + 文档与代码分离）。触发："出个技术方案"/"方案设计"/"帮忙实现 XX 功能" | `skills/dum-solution-design/SKILL.md` |
| **dum-doc-reconcile** | 按时间范围依据 `docs/modify_history`（兼查 git）把 architecture/方案设计文档跟代码现状对账修正。触发："校对/修正设计文档"/"文档对账" | `skills/dum-doc-reconcile/SKILL.md` |
| **dum-session-summary** | 把本次会话的改动总结进 `docs/modify_history/`，生成交接/续接文档。触发："把这次会话的修改总结成文档"/"记录修改历史" | `skills/dum-session-summary/SKILL.md` |
| **dum-ppt** | 把 Markdown 转成单 HTML、可全屏播放的专业演示文档。触发："做 PPT"/"演示文稿"/"把这份文档做成 PPT" | `skills/dum-ppt/SKILL.md` |

这几个技能相互衔接：`dum-solution-design` 出方案 → 实现 → `dum-session-summary` 记录改动 →
`dum-doc-reconcile` 据此对账文档；`dum-architecture-doc-build` 提供承载这一切的 `docs/` 文档体系。

## 跨 agent 工具名对照

技能正文使用 Claude Code 工具名。其它 agent 用等价工具即可：

| Claude Code | 含义 | 其它 agent |
|---|---|---|
| Read / Write / Edit | 读 / 写 / 改文件 | 各 agent 的文件读写工具 |
| Bash | 执行命令 | shell / terminal 工具 |
| Grep / Glob | 搜索 | 各 agent 的搜索工具 |

`dum-architecture-doc-build` 里的自动更新依赖 Claude Code 的 PostToolUse hook + `.claude/settings.local.json`，
这是 Claude Code 专有机制；在别的 agent 上，生成脚本仍可手动跑，只是"文件变更后自动刷新"需换成该 agent 的 hook 机制。

## 安装

见 [`README.md`](README.md)（按 Claude Code / Codex / Gemini CLI / Cursor 分别说明）。
