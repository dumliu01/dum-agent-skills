# Dum Agent Skills — 技能库索引

本扩展提供一组可复用的工作流技能（skills）。当用户的请求命中下面某个技能的「触发场景」时，
**先完整读取该技能的 `SKILL.md`**，再按其中的步骤执行。技能正文用 Claude Code 的工具名
（Read / Write / Edit / Bash 等）；在 Gemini 里用等价工具即可。

| 技能 | 何时用 | 入口 |
|---|---|---|
| **dum-knowledge-base-build** | 给项目搭建/维护知识库文档体系（docs/ 分类目录 + CLAUDE.md 入口 + 架构文档 + 自动文档索引）；"整理架构文档"/"搭建知识库"/"文档体系" | `skills/dum-knowledge-base-build/SKILL.md` |
| **dum-arch-spec-doc** | 给单个服务按语言（前端/Go/Python）生成分离的两份文档：架构文档（docs/architecture/）+ 规范文档（docs/specification/）；"给前端/Go/Python 写架构文档和规范文档"/"架构和规范分两份" | `skills/dum-arch-spec-doc/SKILL.md` |
| **dum-solution-design** | "出个技术方案"/"方案设计"/"帮忙实现 XX 功能"；动手前要先写设计文档 | `skills/dum-solution-design/SKILL.md` |
| **dum-doc-reconcile** | "校对/修正设计文档"，让 docs/architecture 与方案设计文档跟代码现状对齐 | `skills/dum-doc-reconcile/SKILL.md` |
| **dum-session-summary** | "把这次会话的修改总结成文档"/生成交接文档/记录修改历史到 docs/modify_history | `skills/dum-session-summary/SKILL.md` |
| **dum-ppt** | "做 PPT/演示文稿"，把 Markdown 转成单 HTML、可全屏播放的演示文档 | `skills/dum-ppt/SKILL.md` |
