# 11 节模板的填法

每节如果填不出来，多半是粒度错了。下面给每节常见的"写不出来怎么办"。

## 节 1 概述

写不出"项目使命"那一句 → 直接抄 README.md / `pyproject.toml.description` / `package.json.description`。如果都没有，看入口文件（main.py / index.ts）的第一段 docstring。

技术栈表格只列**主框架**和**有版本/选型决策意义**的依赖；不要把 `pytest>=8.0` 这种通用 dev dep 也列进来。

## 节 2 目录结构

§2 自动生成区写完后，§2.1 人工速览**只挑出 5-15 个一级目录**，一行一个，每行一句话用途。不要复制完整 200 文件树（那是 §2 干的事）。如果项目顶层目录就是少（< 5 个），§2.1 可以省略，加一句"目录扁平，直接看 §2 自动生成的清单"。

## 节 3 核心模块详解

每个模块一节（§3.1 / §3.2 / ...）。决定哪些是"模块"的标准：

- 一个进程内有清晰边界、可单独单测、有 README/docstring 说明的代码包
- 跨多文件、单文件不足以表达
- 上层调用方关心它的接口

不要把每个目录都拆一节。比如 Python 项目 `core/data/` 一节就够了；`core/data/adapters/` 不必单开。

每节内组织：
1. **职责** 1-2 句
2. **关键子目录 / 文件 表格**（路径 + 用途）
3. （可选）**演进史** — 跨多 stage 的话点一下
4. （可选）**数据流图** — 用 mermaid `flowchart` 或 `sequenceDiagram`

如果一个模块大到要 5+ 段才能讲清楚，把它升级为单独的方案文档（参考 dum-solution-design），本节只放摘要 + 链接。

## 节 4 对外接口设计

**API 服务**：列 endpoint 表（method + path + 一句话用途）。schema 不要写在这里——指向 `core/*/schemas.py` 或 OpenAPI doc。

**Library**：列公开 import 路径 + 主要类/函数签名（不写实现）。

**CLI**：列 `<cmd> <subcmd>` 全表 + 一句话用途。

**前端**：列 `api/<domain>.ts` ↔ 后端 router 的一对一映射表 + 路由表。

模块没有对外接口（纯内部计算包）就写 "本服务不对外暴露 HTTP/CLI 接口"，不要硬凑。

## 节 5 配置与机密

只列**会影响运行时行为**的设置。`pytest.ini`、`.editorconfig` 不算。

格式：每个 settings 类一段，关键字段做表格（字段名 + 类型 + 一句话用途）；YAML 配置文件单独一段。

## 节 6 持久化

- 关系数据库：列表名 + 关键迁移（migration_id + 用途）
- 时序/列存（CH/InfluxDB）：列表族
- 缓存（Redis）：列 key 命名空间
- 对象存储 / FS：列 bucket/dir 用途
- 没有该类持久化就不写该段

## 节 7 测试

```
| 目录 | 数量 | 性质 |
| tests/unit/ | 760 | 纯函数/类，无 IO |
| tests/integration/ | 40 | testcontainers 拉 PG/CH |
| tests/golden/ | 3 | 黄金回归 |
| tests/e2e/ | opt-in | 真外部依赖 |
```

加一段说明 CI 在哪个文件、跑了哪些 step、是否有 marker。

## 节 8 构建 / 运行

三个子节固定：本地开发 / 部署 / 测试 lint。每个子节直接列命令，不解释命令含义（命令名自解释）。

## 节 9 模块依赖图

ASCII art 或 Mermaid，看用户偏好。**只画"高层架构层"**：

- ✅ 入口进程 → 业务核心层 → 基础设施层
- ❌ 类图（属于具体模块的方案文档；超出本架构文档范围）
- ❌ 调用栈细节（超出本架构文档范围）

如果模块多到画不下，分两层：先画"服务/进程间"，再画"单进程内核心模块间"。

## 节 10 关键约定与 invariants

回答："读完本文档的开发者，写代码前需要知道哪些不能违反的项目硬规矩？"

例子：

- **PIT 数据约束**：所有 fundamental 查询必须传 `as_of`
- **注册表自注册**：新加 alpha/factor/engine 必须在对应 REGISTRY 登记
- **Live trading fail-fast**：`broker_type=ib_live` 强制要 `IB_LIVE_CONFIRM` env
- **棘轮阈值**：`golden_thresholds.yaml` 仅 bump up 不下调
- **本地 merge + tag 工作流**：单人项目从 Stage X 起不开 PR
- **Stage 演进史权威源**：`docs/资料/stage-history.md`
- **方案文档强制位置**：`方案设计/<YYYYMMDD>-<功能名>.md`
- **全局命名/编码约定**：snake_case for files, PascalCase for classes 等

每条 1 句话规则 + 1 句话原因，不展开。展开放方案文档或单独 ADR。

## 节 11 当前状态

不要写"全部完成"或"持续迭代"这种废话。引用权威 stage history 文档，列最近 1-3 个 stage 名 + tag + 一句话内容；下一步候选列 2-4 个。

Stage history 文档不在则跳过本节，整节删除（不要留空 placeholder）。

---

# 文档地图 / 知识库索引（docs/architecture/README.md）

骨架见 `assets/arch_index_template.md`。这页回答的是「**项目里有哪些文档、分别在哪些目录**」，跟架构文档回答「代码结构」互补。三块内容：

## ① 架构文档链接表（人工）

一行一个服务，链到对应 `*.md`，加一句话。多服务才需要；单服务直接省掉这页，把 DOC-MAP 标记嵌进唯一那份架构文档。

## ② 必读导航（人工）

**只挑 onboarding 必读的 3-8 个**，按阅读顺序排。每条 = 文档名 + 链接 + 一句话「为什么要读它」。

典型必读集：

- **开发规范** `CLAUDE.md` — 写代码前的硬规矩
- **方案设计目录** `方案设计/` — 每个功能一份（dum-solution-design 产出，命名 `<YYYYMMDD>-<功能名>.md`）
- **Stage 演进史** — 项目怎么一路演化到现在
- **ADR / 决策记录** — 为什么这么选型

不要在这里手抄全量文档列表（那是 ③ 自动区干的事）；这里只做「先看什么」的策展。

## ③ 文档地图（自动区，DOC-MAP marker）

`scripts/update_doc_map.py` 自动渲染全项目文档树。你不用手写这块，但要保证：

- **描述能被提取到**：每份文档有 frontmatter `title`/`description`，或至少一个一级 `#` 标题。否则地图里只剩路径没有说明。
- **噪音被排除**：`node_modules` / `.git` / dotdir 默认已排；`third_party/`、`examples/`、依赖 vendored 的 README 要手动加进脚本的 `EXCLUDE_DIRS` 或把 `DOC_SCAN_DIRS` 收窄成白名单。
- **范围合理**：默认扫全项目 `["."]`。如果项目文档很集中（都在 `docs/` + `方案设计/`），收窄白名单让地图更干净。

## 单服务项目怎么办

不值得单开索引页时：把 ② 的必读导航 + ③ 的 DOC-MAP marker 直接放进唯一那份架构文档（放在 §1 概述之后、§2 目录结构之前都行）。`update_doc_map.py` 的 `DOC_MAP_MD_REL` 指向这份文档即可。`AUTO-GENERATED`（源码）和 `DOC-MAP`（文档）两对 marker 在同一文件里共存，互不干扰。
