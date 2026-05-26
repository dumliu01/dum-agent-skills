# dum-knowledge-base-build

> 给项目搭建/维护**标准化知识库文档体系**：docs/ 分类目录 + CLAUDE.md 入口 + 自动文档索引 + hook 驱动的源码清单。

## 它做什么

很多项目的文档分散在各处、缺一个俯瞰入口、找不到"现在系统长什么样"。本技能在项目里建立一套**约定俗成的文档骨架**：

```
<project>/
├── CLAUDE.md                  # agent 总入口（项目概述 + 子项目 + 文档索引）
├── docs/
│   ├── docs-index.md          # 分类文档索引（自动维护，docs/ 总入口）
│   ├── architecture/          # 各子项目架构文档（含 AUTO-GENERATED 源码树）
│   ├── specification/         # 编程/工程规范
│   ├── product-design/ tech-design/ superpowers/
│   ├── modify_history/ deffered/ report/
│   ├── manual_deployment/ manual_userguides/
│   └── reference/             # 参考资料 / 外部链接
└── <service>/CLAUDE.md        # 各子项目入口
```

外加两个**自动更新的区域**（PostToolUse hook 驱动）：各服务源码目录清单写进对应架构文档；分类文档索引写进 `docs/docs-index.md`。

## 何时触发

- ✅ "整理架构文档" / "搭建知识库" / "文档体系" / "文档索引"
- ✅ 项目代码稳定但缺俯瞰入口（CLAUDE.md / 架构文档 / 索引）
- ❌ 只想要面向用户的 README（产品视角，用别的）
- ❌ 单文件/小脚本项目（< 20 源文件，不值得整套体系）

## 它交付什么

| | |
|---|---|
| 一次性脚手架 | `scripts/scaffold_docs_structure.py` 建好全套 docs/ + README |
| 入口文档 | 根 `CLAUDE.md` + 各子项目 `<service>/CLAUDE.md` |
| 架构文档 | `docs/architecture/<service>.md`（11 节模板 + AUTO-GENERATED 占位） |
| 自动脚本 | `update_architecture_<service>.py`（一服务一份）+ `update_docs_index.py`（一项目一份） |
| Hook 配置 | `.claude/settings.local.json` 的 PostToolUse 段 |

## 跟其它技能怎么衔接

- 它搭骨架 + 装 hook；**填实单个服务的「架构 + 规范」两份文档**交给 [`dum-arch-spec-doc`](../dum-arch-spec-doc/)
- `dum-session-summary` 写进 `docs/modify_history/`、`dum-doc-reconcile` 据此对账 `docs/architecture/` 与 `docs/方案设计/`、`dum-solution-design` 出方案到 `docs/tech-design/`——**这三个技能的产出都落进本技能搭好的目录**

## 完整工作流

8 步流程、AUTO-GENERATED marker 约定、各语言源码描述提取规则、hook 配置骨架、常见错误与出口判断，详见 [`SKILL.md`](SKILL.md)。

资源：`assets/` 模板 · `scripts/` 三个脚本 · `references/` 章节策略与语言提取器与 commit 模板。
