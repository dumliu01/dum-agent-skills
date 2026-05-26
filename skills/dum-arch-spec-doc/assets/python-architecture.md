# {{服务名}} — 程序架构文档

> 📐 本文档侧重**系统结构**（描述性）。开发规范见 [`../specification/{{service}}-规范.md`](../specification/{{service}}-规范.md)。
> 🤖 项目入口：[`../../CLAUDE.md`](../../CLAUDE.md) ｜ 文档索引：[`../reference/docs-index.md`](../reference/docs-index.md)（如有）

---

## 1. 概述

### 🎯 项目使命

**{{一句话定位}}** —— {{2-3 行：解决什么问题、面向什么用户/场景、上下游系统}}。

### 技术栈

| 层次 | 技术 |
|------|------|
| 语言/运行时 | Python {{3.12}} |
| Web 框架 | {{FastAPI / Flask / Django}} + {{Uvicorn}} |
| 数据校验/配置 | {{Pydantic v2}} |
| 数据访问 | {{SQLAlchemy / asyncpg}} + {{PostgreSQL}} |
| 实时通信 | {{FastAPI WebSocket}} |
| 任务/AI/队列等关键库 | {{...}} |

### 入口

```
{{app/main.py}}
└── {{create_app() → 注册路由/中间件 → 启动 Uvicorn}}
```

---

## 2. 目录结构（自动生成区域）

> 💡 此区域由 `scripts/update_architecture_{{service}}.py` 自动维护（dum-knowledge-base-build 的 hook 驱动）。
> 描述来源：每个 `.py` 文件首部 docstring。高层分组见下方 §2.1。

<!-- AUTO-GENERATED:START -->
<!-- 占位：首次运行 scripts/update_architecture_{{service}}.py 后自动填充 -->
```
(pending first run)
```
<!-- AUTO-GENERATED:END -->

### 2.1 目录速览（人工维护）

```
app/
├── api/ | routes/        # 路由层（endpoint）
├── services/             # 业务逻辑
├── models/ | schemas/    # 数据模型 + Pydantic schema
├── core/ | config/       # 配置、启动、公共
└── ...
config/                   # 声明式配置（yaml 等）
```

---

## 3. 分层 / 执行模式

{{描述分层（route → service → repository/model）或多执行模式（如不同 mode 走不同 service）。}}

| 层 / 模式 | 目录 | 职责 |
|---|---|---|
| {{路由层}} | {{app/routes}} | {{解析请求、调用 service}} |
| {{业务层}} | {{app/services}} | {{核心逻辑}} |

---

## 4. WebSocket 协议（如有）

{{连接路径、鉴权、ConnectionManager、MessageType 枚举、典型时序。只列消息字段契约。}}

| 消息类型 | 方向 | 字段 |
|---|---|---|
| {{...}} | {{c→s / s→c}} | {{...}} |

---

## 5. 核心服务系统

{{按项目实际：AI 模型服务 / Skill 系统 / 计费 / 错误分析管道 …，每个一小节描述架构与关键文件。}}

### 5.1 {{服务}} (`{{app/services/xxx.py}}`)

**职责**：{{1-2 句}}。关键类/函数签名与协作：{{...}}。

---

## 6. 数据模型 / Schemas

| 模型 / Schema | 文件 | 用途 |
|---|---|---|
| {{User}} | {{models/user.py}} | {{ORM 模型}} |
| {{UserOut}} | {{schemas.py}} | {{响应序列化}} |

---

## 7. 认证与安全（现状描述）

{{JWT 怎么校验、依赖注入鉴权、CORS 配置、敏感数据处理现状。"必须脱敏"等要求归规范。}}

---

## 8. 配置系统

{{Pydantic BaseSettings (`config/settings.py`) + `.env` + 声明式 yaml（如 models.yaml）的分工。}}

| 配置项 | 来源 | 用途 |
|---|---|---|
| {{LOG_LEVEL}} | {{.env}} | {{...}} |

---

## 9. 模块依赖关系图

```
{{ASCII art 或 Mermaid：main → routes → services → models/外部客户端，画清依赖方向}}
```
