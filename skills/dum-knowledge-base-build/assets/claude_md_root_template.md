# {{Project Name}} — Agent 入口文档

> 🤖 本文件是 Claude Code / agent 进入本项目的**第一入口**。先读这里，再按文档索引深入。
> 写代码前必读：规范文档 + 对应子项目的架构文档。

## 项目概述

**{{一句话定位}}** —— {{2-3 行：解决什么问题、面向什么用户/场景、关键技术选型}}。

## 子项目

| 子项目 | 目录 | 说明 | 入口文档 |
|---|---|---|---|
| {{backend}} | `{{backend/}}` | {{后端服务，一句话}} | [`{{backend}}/CLAUDE.md`]({{backend}}/CLAUDE.md) |
| {{frontend}} | `{{frontend/}}` | {{前端服务，一句话}} | [`{{frontend}}/CLAUDE.md`]({{frontend}}/CLAUDE.md) |

（单服务项目删掉本节）

## 文档索引

📚 **完整文档清单（自动维护）**：[`docs/docs-index.md`](docs/docs-index.md)

核心文档：

- **架构** → [`docs/architecture/`](docs/architecture/)（每个子项目一份）
- **规范** → [`docs/specification/`](docs/specification/)（写代码前必读）
- **产品设计** → [`docs/product-design/`](docs/product-design/)
- **技术方案** → [`docs/tech-design/`](docs/tech-design/)
- {{挑 2-4 个本项目最常翻的，如部署手册 / 修改记录}}

## 文档结构约定

```
docs/
├── docs-index.md      # 🤖 分类文档索引（自动维护，DOCS-INDEX marker，docs/ 总入口）
├── architecture/      # 各子项目核心架构文档
├── specification/     # 编程 / 工程规范
├── product-design/    # 产品（需求）设计      （YYYYMMDD-[标题].md）
├── tech-design/       # 技术方案设计          （YYYYMMDD-[标题].md）
├── superpowers/       # superpowers 产出（plans/ specs/）
├── modify_history/    # 阶段总结 / 修改记录    （YYYYMMDD-[修改摘要].md）
├── deffered/          # 待办 / 暂缓事项        （YYYYMMDD-[摘要].md）
├── manual_deployment/ # 部署文档
├── manual_userguides/ # 用户手册
├── report/            # 分析报告              （YYYYMMDD-[标题].md）
└── reference/         # 参考资料 / 外部链接（不放 docs-index）
```

各目录用途详见其 `README.md`。

## 关键约定

1. **新文档落位**：按上表分类放进对应 `docs/` 子目录，文件名遵守 `YYYYMMDD-[标题].md`。
2. **文档索引自动维护**：`docs/docs-index.md` 由 hook 自动刷新，**别手动编辑它的自动区**。
3. {{项目特有的硬规矩，如分支策略 / 提交规范，可指向 docs/specification/}}
