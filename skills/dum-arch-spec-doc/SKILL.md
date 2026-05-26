---
name: dum-arch-spec-doc
description: 给单个服务/子项目按语言生成两份分离的文档——「程序架构文档」（描述性，落 docs/architecture/<service>.md）和「开发规范文档」（规范性，落 docs/specification/<service>-规范.md），前端(TS/React/Electron/Vue) / Go 后端 / Python 后端各有专属模板，另带 generic 骨架可扩展。触发场景：用户说"给前端/Go/Python 写架构文档和规范文档" / "架构文档和规范分成两份" / "生成开发规范文档" / "程序架构文档 + 编码规范" / "拆分架构与规范" 等。区别于 dum-knowledge-base-build（那个搭整套 docs/ 体系 + hook + 文档索引；本技能只**产出这两份文档内容**，复用它建好的目录）。
---

# Dum Arch Spec Doc

## Overview

给一个服务（一个进程 / 子项目）产出**两份分离的文档**——很多团队（包括 termcat 的参考文档）把这两类内容混在一份 `ARCHITECTURE.md` 里，本技能把它们拆开：

| 文档 | 落点 | 性质 | 回答的问题 |
|---|---|---|---|
| **程序架构文档** | `docs/architecture/<service>.md` | 描述性 | 系统是怎么搭的：技术栈、进程/分层模型、目录结构、核心模块、对外协议、数据模型、依赖图 |
| **开发规范文档** | `docs/specification/<service>-规范.md` | 规范性 | 写代码要守的规矩：命名、注释语言、API 风格、错误码体系、日志规范、性能规则、测试规范、开发速查、提交规范 |

**拆分判定（核心准则）**：能从代码**读出来的现状** → 架构；**要求开发者遵守**的约定 → 规范。灰区按这条判，详见 [`references/arch-vs-spec-split.md`](references/arch-vs-spec-split.md)。

**按语言给专属模板**：前端 / Go / Python 各一套贴合的 arch + spec 模板，外加 generic 骨架供扩展（Rust / Java …）。

## 触发判断

**应该触发**：
- 用户要给某个服务写 / 整理「架构文档」并且同时要「规范文档 / 编码规范 / 开发规范」
- 用户明说「架构和规范分开两份」「别混在一份文档里」
- 项目已有一份混合的 `ARCHITECTURE.md`，要拆成架构 + 规范两份
- 给前端、Go 后端、Python 后端**分别**出这两类文档

**不应触发**：
- 用户要搭**整套** docs/ 知识库体系 + CLAUDE.md 入口 + hook 自动索引 → 用 [dum-knowledge-base-build]，再用本技能补单服务文档
- 用户只要一份混合文档、明确不想拆 → 直接按模板取需要的章节，但提醒拆分的好处
- 出某个**功能**的技术方案（架构/时序/接口/遗留）→ 用 dum-solution-design

## 与 dum-knowledge-base-build 的分工

| | dum-knowledge-base-build | **dum-arch-spec-doc（本技能）** |
|---|---|---|
| 职责 | 搭/维护**整套** docs/ taxonomy + 根&子项目 CLAUDE.md + 文档索引 + PostToolUse hook | 给**单个服务**产出架构 + 规范两份内容 |
| 输出 | 目录骨架、入口、索引、自动更新脚本 | `docs/architecture/<service>.md` + `docs/specification/<service>-规范.md` |
| 自动区 | **拥有** `update_architecture_<service>.py` 脚本 + hook | 只在架构文档放 AUTO-GENERATED 占位，**复用**它的脚本回填 |

**配合用法**：先跑 dum-knowledge-base-build 建目录与 hook，再用本技能逐个服务填实两份文档。也可单用本技能——目录不存在时只补建 `docs/architecture/` 或 `docs/specification/`，不拉整套脚手架。

## 工作流（按顺序，跳一步说原因）

### 第 0 步：摸底

1. **判语言**：看服务根的标志文件——`package.json` + `tsconfig`/`.tsx`/`vue` → 前端；`go.mod` → Go；`pyproject.toml`/`requirements.txt`/`.py` → Python；都不像 → generic。一个服务一组（架构 + 规范）文档。
2. **定落点**：`docs/architecture/` 与 `docs/specification/` 在不在？不在就**只补建用到的那个目录**（不要建整套 taxonomy，那是 dum-knowledge-base-build 的活）。
3. **保护已有**：`docs/architecture/<service>.md` / `docs/specification/<service>-规范.md` 已存在时**不整体覆盖**——先读出来，缺哪节补哪节。已有一份混合 `ARCHITECTURE.md` 时，按 [`references/arch-vs-spec-split.md`](references/arch-vs-spec-split.md) 把每节归到两份的对应章节。

把摸底结论写进对话（语言、落点、是否拆分已有混合文档），跟用户确认后再动手。

### 第 1 步：选模板

按语言挑两份模板（`<lang>` ∈ frontend / go / python / generic）：
- 架构：[`assets/<lang>-architecture.md`](assets/)
- 规范：[`assets/<lang>-specification.md`](assets/)

各语言该有哪些章节、差异点、以及**怎么加新语言**，见 [`references/language-cheatsheet.md`](references/language-cheatsheet.md)。

### 第 2 步：写架构文档 → `docs/architecture/<service>.md`

用 `assets/<lang>-architecture.md`，逐节填实。**关键约束**：
- 「目录结构」节保留 `<!-- AUTO-GENERATED:START -->` … `<!-- AUTO-GENERATED:END -->` 占位（中间放 ```\n(pending first run)\n```），由 dum-knowledge-base-build 的脚本回填源码树；本技能只写 §x.1「目录速览」高层分组。
- 模块依赖图用 ASCII art 或 Mermaid（用户偏好）。
- **不写手写实现代码**：接口签名 / 消息字段 / 类型契约可以，完整函数体挪代码本身（与 dum-solution-design 同规则）。
- 不留 `[TODO]` / `[占位]` / `稍后补充`；写不出来就把那节拆细再写。

### 第 3 步：写规范文档 → `docs/specification/<service>-规范.md`

用 `assets/<lang>-specification.md`。规范文档是**祈使句**：每条是"必须 / 禁止 / 应该"，配 ✅Good / ❌Bad 例子。从代码里**实际提取**项目现行约定（命名、注释语言、错误码段、日志格式、API 风格），不要照抄模板里的示例值。「开发速查」表（场景→关键文件）特别有用，务必填实。

### 第 4 步：交叉引用 + 入口

- 两份文档头部互链：架构文档指向 `../specification/<service>-规范.md`，规范文档指向 `../architecture/<service>.md`。
- 都链到项目入口 `CLAUDE.md` 和（若有）`docs/docs-index.md`。
- 若 dum-knowledge-base-build 的 docs-index hook 在跑，新文件会被自动收录；没有就手动在索引里加两行。

### 第 5 步：出口检查

见下方「出口判断」。逐项过，漏任一项不交付。

## 命名与落点约定

| | 路径 | 一级标题 |
|---|---|---|
| 架构 | `docs/architecture/<service>.md` | `# <服务名> — 程序架构文档` |
| 规范 | `docs/specification/<service>-规范.md` | `# <服务名> — 开发规范` |

`<service>` 用短横线小写服务名（如 `termcat-client`）。规范文件中文后缀 `-规范.md`，与仓库中文风格一致。

## 常见错误

| 错误 | 后果 | 修正 |
|---|---|---|
| 把规范内容（命名/错误码/日志格式/性能规则）写进架构文档 | 两份职责糊在一起，又退回混合文档 | 按 arch-vs-spec-split 的准则归位：约定→规范 |
| 把架构内容（模块职责/数据流/依赖图）写进规范文档 | 规范文档变成第二份架构文档 | 现状描述→架构 |
| 整体覆盖已有架构/规范文档 | 抹掉人工补的内容 | 只 Edit 补缺节，先读出来再决定插哪 |
| 架构文档没留 AUTO-GENERATED marker | dum-knowledge-base-build 的脚本无处回填，目录树永远空 | 第 2 步先放好一对 marker |
| 规范照抄模板示例值（错误码段、命名前缀） | 文档与项目实际约定对不上 | 从代码实际提取现行约定 |
| 自己又建了整套 docs/ taxonomy | 与 dum-knowledge-base-build 职责重叠、目录冗余 | 只补建 architecture/ 或 specification/，整套交给那个技能 |
| 架构文档塞手写实现代码 | 代码漂移、文档难维护 | 只留签名/字段/契约 |
| 规范文档写成陈述句（"项目用 snake_case"） | 读者不知道是要求还是描述 | 用祈使句 + ✅/❌ 例子 |

## Skill 内的资源

- [`assets/frontend-architecture.md`](assets/frontend-architecture.md) / [`assets/frontend-specification.md`](assets/frontend-specification.md) — 前端(TS/React/Electron/Vue) 架构 + 规范模板
- [`assets/go-architecture.md`](assets/go-architecture.md) / [`assets/go-specification.md`](assets/go-specification.md) — Go 后端架构 + 规范模板
- [`assets/python-architecture.md`](assets/python-architecture.md) / [`assets/python-specification.md`](assets/python-specification.md) — Python 后端架构 + 规范模板
- [`assets/generic-architecture.md`](assets/generic-architecture.md) / [`assets/generic-specification.md`](assets/generic-specification.md) — 通用骨架（扩展新语言起手）
- [`references/arch-vs-spec-split.md`](references/arch-vs-spec-split.md) — 内容归属 taxonomy + 灰区判定（拆混合文档必看）
- [`references/language-cheatsheet.md`](references/language-cheatsheet.md) — 各语言 arch/spec 章节清单、差异点、怎么加新语言

## 出口判断

完成的标志（按顺序）：
1. ✅ 语言判定正确，落点目录存在（必要时只补建了 architecture/ 或 specification/）
2. ✅ `docs/architecture/<service>.md` 存在且非占位，每节填实，无 `[TODO]`
3. ✅ 架构文档「目录结构」节有 `<!-- AUTO-GENERATED:START/END -->` 一对 marker
4. ✅ `docs/specification/<service>-规范.md` 存在且非占位，规范是祈使句 + ✅/❌ 例子，约定取自代码实际
5. ✅ 两份文档头部互链，且各链到 CLAUDE.md 入口（及 docs-index，如有）
6. ✅ 架构文档无手写实现代码（仅签名/字段/契约）
7. ✅ 没有把规范内容写进架构、或把架构内容写进规范（抽查 3 节自检）

漏任一项就还没完成，不要交付。
