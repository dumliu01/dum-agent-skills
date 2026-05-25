---
name: dum-solution-design
description: Use when user asks "出个技术方案" / "方案设计" / "做个方案" / "帮忙实现 XX 功能" / "设计一下 XX" with requirements or reference image; or when about to design a non-trivial feature that needs to be documented before implementation. Enforces 5-module structure (架构/时序/关键逻辑/接口/遗留) + doc-code separation + 方案设计/ output convention.
---

# dum-solution-design（个人技术方案设计规范）

## Overview

本 skill 是个人技术方案设计规范，强制使用 5 模块结构 + 文档/代码分离 + 文件命名约定。

**核心原则**：方案文档只讲**逻辑和决策**，不写示例代码。代码设计若必需，单独成文。

**绘图工具默认 = Mermaid**：架构图 / 模块图 / 时序图 / 流程图全部默认使用 Mermaid（直接在 markdown 里写 ```mermaid 代码块，无需额外 skill），不要默认走 PlantUML / `superpowers:uml`。仅当 Mermaid 真表达不了（如某些 PlantUML stdlib 特殊图形）时才回退 PlantUML。

## When to Use

| 触发场景 | 例子 |
|---|---|
| 用户明确请求技术方案 | "出个技术方案" / "做个方案设计" / "设计一下 XX 模块" |
| 用户描述需求 + 提供参考材料 | 需求描述 + 截图 / 参考链接 / 类似产品举例 |
| 实现前规划阶段 | 用户说 "帮忙实现 XX 功能"，且复杂度足够需要先写方案而非直接编码 |
| 重要重构 / 跨模块改造 | 影响 ≥ 2 个模块、需要团队对齐设计 |

## When NOT to Use

- 用户只要小修改（< 50 行代码 / 单文件变更）→ 直接改
- bug 修复 → 用 superpowers:systematic-debugging
- 已有 brainstorming spec → 用 superpowers:writing-plans 直接出 plan
- 一次性脚本 / 实验代码 → 不写方案

## Output Specification

### 文件位置（强制）

所有方案文档放到项目根目录下的 `方案设计/` 目录（**不是** `docs/` 或 `docs/product/` 或其他位置）。如果项目没有这个目录，先创建。

```
项目根/
└── 方案设计/
    ├── 20260425-FundamentalAnalyst.md
    ├── 20260425-FundamentalAnalyst-代码实现.md   # 可选
    └── ...
```

### 文件命名（强制）

| 文件类型 | 格式 | 示例 |
|---|---|---|
| 主方案文档 | `YYYYMMDD-方案名称.md` | `20260425-FundamentalAnalyst.md` |
| 代码实现文档（可选） | `YYYYMMDD-方案名称-代码实现.md` | `20260425-FundamentalAnalyst-代码实现.md` |

**强约束**：
- 日期用 `YYYYMMDD` 格式（无分隔符）
- "方案名称" 用驼峰或英文短语，避免空格 / 中文括号 / 路径敏感符号
- 代码实现文档**仅当需要**时创建，不强制

## The 5 Required Modules（主方案文档结构）

主方案文档 `YYYYMMDD-方案名称.md` 必须按下面顺序包含**全部 5 个模块**：

### 1. 架构设计 / 模块设计

**包含**：
- **架构图**（涉及多服务 / 多进程时）：服务/进程之间关系
- **模块类图**（单进程内）：程序内各模块/类之间关系
- **每个模块的作用说明**：1–3 句概括职责 + 依赖

**工具**：默认使用 **Mermaid**（适用于类图、组件图、架构图）。仅当 Mermaid 表达不了时再回退到 `superpowers:uml`（PlantUML）

**输出**：把图嵌入到文档（Mermaid 代码块 ```mermaid ... ```，markdown 渲染器直接出图）

### 2. 关键流程时序图

**包含**：
- 涵盖**关键流程**的时序图（**优先时序图**，不够再用流程图）
- 每个流程的前置条件 + 后置条件 + 错误分支

**工具**：默认使用 **Mermaid sequenceDiagram**。仅当 Mermaid 表达不了时再回退到 `superpowers:uml`（PlantUML sequence diagram）

**经验法则**：
- 每个方案至少 1 个时序图（核心 happy path）
- 复杂方案可加 2–3 个（异常分支 / 并发 / 跨服务）
- 不画过细：调用栈深度 ≤ 5 层

### 3. 关键逻辑

**包含**：
- **本方案最关键要解决的问题**（业务难点 / 技术难点）
- **每个难点的解决方案**（设计选择 + 理由 + 取舍）

**写法**：
- 用 "问题 → 难点 → 方案 → 理由" 四段式
- 每个难点列 2–3 个候选方案 + 选择理由（为什么不选另外的）
- **不写代码**，只描述算法 / 数据结构 / 决策逻辑

### 4. 接口说明

**包含（仅当方案涉及 API / 服务调用 / 模块边界 API 时）**：
- API 端点 / 函数签名 / 消息格式
- 每个接口的：路径 / method / 入参 schema / 出参 schema / 错误码 / 鉴权

**写法**：
- 用表格或 OpenAPI 风格描述
- 项目内现有 API 风格需对齐
- **不写实现**，只写契约

**可省略条件**：方案纯内部模块、无对外接口、无跨服务调用 → 此章节标记 "本方案无对外接口" 即可

### 5. 遗留问题

**包含**：
- 方案实现后**已知未解决**的问题
- 后续可优化方向（不属于本方案 scope 但相关）
- 重开触发条件（什么时候应该回来处理）

**写法**：
- 编号列表 P1 / P2 / P3...（重要性递减）
- 每个问题：现状描述 + 为什么本次不做 + 建议的处理时机

## Document / Code Separation Rule（强制）

### 主方案文档不写示例代码

**禁止内容**：
- ❌ 函数/类的代码实现（`def`/`class`/`function`）
- ❌ 完整 SQL 建表语句（除非是 schema 设计的一部分）
- ❌ 配置文件示例（除非是接口契约的一部分）
- ❌ 单元测试代码

**允许内容**：
- ✅ 函数签名 / 接口定义（描述契约，非实现）
- ✅ 数据 schema（字段名 + 类型 + 约束）
- ✅ 伪代码（仅当算法逻辑必须用代码表达 ）
- ✅ 命令行 / shell 命令示例（接口说明用）

### 何时创建 -代码实现 文档

**创建条件**（任一即可）：
- 方案涉及非平凡算法，需要给开发者代码参考
- 关键代码骨架必须显式展示（如复杂状态机 / DSL 设计）
- 实现包含技术 trick 容易写错（如并发原语 / lock-free 算法）

**不创建条件**：
- 标准 CRUD / boilerplate
- 跟现有代码模式一致的常规实现
- 测试代码

## Workflow

```
1. 用户触发 → 确认方案范围 + 关键决策
2. 出 5 模块主方案文档（默认用 Mermaid 画图，必要时回退 superpowers:uml）
3. 评估是否需要 -代码实现 文档（按上面条件）
   - 需要 → 写代码实现文档
   - 不需要 → 跳过
4. 文档保存到 方案设计/ 目录
5. 让用户审，反馈修改
6. 通过后 → 进入实施阶段（用 superpowers:writing-plans 出 plan）
```

## Quick Reference

| 项 | 规则 |
|---|---|
| 输出位置 | `方案设计/`（项目根） |
| 主文档命名 | `YYYYMMDD-方案名称.md` |
| 代码文档命名 | `YYYYMMDD-方案名称-代码实现.md`（可选） |
| 必含模块数 | 5（架构 / 时序 / 关键逻辑 / 接口 / 遗留） |
| 主文档可写代码？ | **否**，仅签名 / schema / 伪代码 |
| 图工具 | **默认 Mermaid**（直接写 ```mermaid 代码块）；不够用再回退 `superpowers:uml`（PlantUML） |
| 时序 vs 流程图 | **优先时序图** |
| 文档与代码分离 | 主文档不写实现代码；需要时单独写 -代码实现.md |

## Common Mistakes

| 错误 | 后果 | 修正 |
|---|---|---|
| 文档放到 `docs/` 或 `docs/product/` | 项目结构污染 / 与其他项目设计文档混淆 | 严格放 `方案设计/` |
| 文件名加 "方案设计" 后缀 | 与本 skill 约定不符 | 用 `YYYYMMDD-方案名称.md`，不加后缀 |
| 主文档夹杂代码实现 | 文档和代码绑定 / 重构后过时 | 代码挪 -代码实现.md |
| 漏掉"遗留问题"模块 | 后续不知道为什么没做 | 即使无遗留也要写 "本方案无遗留问题"  |
| 用流程图代替时序图 | 看不出调用顺序和角色 | 优先时序图，不够再加流程图 |
| 接口说明写实现细节 | 契约和实现耦合 | 只写 path / method / schema / 错误码 |
| 跳过架构图 | 模块关系不可视 | 必须画（默认 Mermaid 类图 / flowchart，必要时再用 PlantUML） |

## Red Flags — STOP

出现下面任何一项 = 你正在偏离本 skill：

- 写了第一个 `def` / `class` / `function`（除签名 + 类型）→ 移到 -代码实现.md
- 文件名带 `方案设计` 后缀 → 改名
- 文件位置不在 `方案设计/` → 移动
- 模块数 < 5 → 补全（无内容标记 "无相关问题/接口"）
- 时序图缺失 → 补一个 happy path
- 用 ASCII art 画图替代 → 默认用 Mermaid，需要时再用 `superpowers:uml`（PlantUML）

**任何一项触发都意味着停下、修复、重读本 skill 再继续。**

## Cross-References

- **DEFAULT DIAGRAM TOOL**: **Mermaid**（直接在 markdown 里写 ```mermaid 代码块，无需额外 skill）— 类图 / 时序图 / 流程图都用它
- **FALLBACK SUB-SKILL**: `superpowers:uml` — 仅当 Mermaid 表达不了（如复杂组件图、特殊 PlantUML 特性）时才用
- **NEXT STEP**: `superpowers:writing-plans` — 方案审核通过后，把方案落成可执行的 plan
- **ALTERNATIVE**: `superpowers:brainstorming` — 如果方案本身还没明确（用户只有模糊想法），先 brainstorm 再来用本 skill
