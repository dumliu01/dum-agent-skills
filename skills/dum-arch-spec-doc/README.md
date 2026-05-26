# dum-arch-spec-doc

> 给**单个服务**按语言（前端 / Go / Python）生成**两份分离**的文档——程序架构文档 + 开发规范文档。

## 它做什么

很多团队（包括 termcat 三个服务的参考文档）习惯把"系统怎么搭"和"写代码要遵守的规矩"塞在一份 `ARCHITECTURE.md` 里，混在一起后两类内容互相干扰。本技能把它们**强制拆成两份**：

| 文档 | 落点 | 性质 | 回答的问题 |
|---|---|---|---|
| **程序架构文档** | `docs/architecture/<service>.md` | 描述性 | 系统是怎么搭的：技术栈、进程/分层、目录结构、核心模块、对外协议、数据模型、依赖图 |
| **开发规范文档** | `docs/specification/<service>-规范.md` | 规范性 | 写代码要守的规矩：命名、注释语言、API 风格、错误码体系、日志规范、性能规则、提交规范 |

**拆分准则**：能从代码**读出来的现状** → 架构；**要求开发者遵守**的约定 → 规范。

**按语言给专属模板**：前端(TS/React/Electron/Vue)、Go 后端、Python 后端各一套贴合的 arch + spec 模板；另带 generic 骨架供 Rust / Java 等扩展。

## 何时触发

- ✅ "给前端/Go/Python 写架构文档和规范文档"
- ✅ "架构和规范分两份" / "别混在一份文档里"
- ✅ 已有混合 `ARCHITECTURE.md` 要拆成两份
- ❌ 要搭**整套**知识库体系 → 用 [`dum-knowledge-base-build`](../dum-knowledge-base-build/)
- ❌ 出某个**功能**的技术方案 → 用 [`dum-solution-design`](../dum-solution-design/)

## 它交付什么

| | |
|---|---|
| 架构文档 | `docs/architecture/<service>.md`（含 `<!-- AUTO-GENERATED -->` 占位，复用 doc-build 的脚本回填源码树） |
| 规范文档 | `docs/specification/<service>-规范.md`（祈使句 + ✅Good/❌Bad 例子） |
| 互链 | 两份文档头部互链，且各链到 CLAUDE.md 入口 |

## 跟其它技能怎么衔接

- 通常先跑 [`dum-knowledge-base-build`](../dum-knowledge-base-build/) 建好目录与 hook，再用本技能逐个服务填实两份文档；也可单用——目录不存在时只补建 `docs/architecture/` 或 `docs/specification/`。
- 架构文档的 AUTO-GENERATED 源码树由 doc-build 的脚本回填，本技能只放占位。

## 完整工作流

6 步流程（摸底 → 选模板 → 写架构 → 写规范 → 交叉引用 → 出口检查）、与 doc-build 的分工细节、各语言模板速查、常见错误与出口判断，详见 [`SKILL.md`](SKILL.md)。

资源：`assets/` 八个模板（4 语言 × arch+spec） · `references/arch-vs-spec-split.md`（拆分 taxonomy） · `references/language-cheatsheet.md`（各语言章节速查）。
