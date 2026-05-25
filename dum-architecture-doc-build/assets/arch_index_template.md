# {{Project Name}} — 架构文档索引 / 知识库地图

> 📚 本页是项目所有文档的总入口（knowledge base index）。
> **上半部分人工维护**「读什么、按什么顺序读」；
> **下半部分（文档地图）由 `scripts/update_doc_map.py` 自动维护**「项目里有哪些文档、分别在哪些目录」，
> 通过 Claude Code Hook（PostToolUse → Write|Edit）在任意 `.md` 变更后刷新。

---

## 架构文档（按服务 / 进程）

| 服务 / 进程 | 文档 | 一句话 |
|---|---|---|
| {{backend}} | [`./backend.md`](./backend.md) | {{后端：进程模型 + 核心模块}} |
| {{frontend}} | [`./frontend.md`](./frontend.md) | {{前端：路由 + store + API 映射}} |
| {{...}} | {{...}} | {{...}} |

## 必读导航（人工维护）

按新人 onboarding 的阅读顺序排，只列 3-8 个最关键的：

1. **开发规范** → [`../../CLAUDE.md`](../../CLAUDE.md)（写代码前必读的硬规矩）
2. **本服务架构** → 上表对应的 `*.md`
3. **方案设计** → [`../../方案设计/`](../../方案设计/)（每个功能一份，命名 `<YYYYMMDD>-<功能名>.md`）
4. **{{Stage 演进史 / ADR / 决策记录}}** → {{路径}}
5. **{{...}}**

> 完整文档清单看下方「文档地图」自动区，不要在这里手抄全量列表。

---

## 文档地图（自动生成区域）

> 💡 此区域由 `scripts/update_doc_map.py` 自动维护，描述来源：
> 每个文档的 frontmatter `title`/`description` → 首个 `#` 标题 → 首行非空正文。
> 想让某份文档在这里显示得清楚，就给它写个好的一级标题。

<!-- DOC-MAP:START -->
<!-- 占位：首次运行 scripts/update_doc_map.py 后自动填充 -->
```
(pending first run)
```
<!-- DOC-MAP:END -->
