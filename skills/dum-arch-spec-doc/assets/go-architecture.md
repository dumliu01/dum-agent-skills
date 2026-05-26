# {{服务名}} — 程序架构文档

> 📐 本文档侧重**系统结构**（描述性）。开发规范见 [`../specification/{{service}}-规范.md`](../specification/{{service}}-规范.md)。
> 🤖 项目入口：[`../../CLAUDE.md`](../../CLAUDE.md) ｜ 文档索引：[`../docs-index.md`](../docs-index.md)（如有）

---

## 1. 概述

### 🎯 项目使命

**{{一句话定位}}** —— {{2-3 行：解决什么问题、面向什么用户/场景、上下游系统}}。

### 技术栈

| 层次 | 技术 |
|------|------|
| 语言/运行时 | Go {{1.22}} |
| Web 框架 | {{Gin / Echo / chi / net/http}} |
| ORM/DB 驱动 | {{GORM / sqlx}} + {{PostgreSQL / MySQL / SQLite}} |
| 实时通信 | {{gorilla/websocket}} |
| 配置 | {{env / viper}} |

### 入口

```
{{cmd/server/main.go}}
└── {{初始化配置 → 连接 DB → 注册路由 → 启动 HTTP server}}
```

---

## 2. 目录结构（自动生成区域）

> 💡 此区域由 `scripts/update_architecture_{{service}}.py` 自动维护（dum-knowledge-base-build 的 hook 驱动）。
> 描述来源：每个 `.go` 文件首部注释。高层分组见下方 §2.1。

<!-- AUTO-GENERATED:START -->
<!-- 占位：首次运行 scripts/update_architecture_{{service}}.py 后自动填充 -->
```
(pending first run)
```
<!-- AUTO-GENERATED:END -->

### 2.1 目录速览（人工维护）

```
{{module}}/
├── cmd/                 # 程序入口
├── internal/            # 私有业务代码（外部不可 import）
│   ├── api/             # HTTP handler + 路由 + 中间件
│   ├── models/          # 数据模型
│   ├── {{ssh|payment}}/ # 业务子系统
│   └── ...
├── pkg/                 # 可复用公共包（errors / logging / utils）
└── configs/             # 配置文件
```

---

## 3. 分层架构（Clean Architecture）

{{描述分层与依赖方向（依赖只能向内）。}}

```
Handler (internal/api) → Service (业务) → Repository (数据访问) → Model
        ↑ 依赖只能向内，pkg/ 不依赖 internal/
```

| 层 | 目录 | 职责 |
|---|---|---|
| Handler | {{internal/api}} | {{解析请求、调用 service、组装响应}} |
| Service | {{...}} | {{业务逻辑}} |
| Repository | {{...}} | {{DB 访问}} |

---

## 4. 启动流程

{{从 main 到 ready 的步骤：加载配置 → InitLogger → 连 DB + AutoMigrate → 装配依赖 → 注册路由 → 监听端口。}}

---

## 5. API 路由总览（现状清单）

> API **风格约定**（POST-only、URL 格式、统一响应）归规范文档；这里只盘点当前有哪些接口。

| 方法 | 路径 | 用途 | 认证 |
|---|---|---|---|
| {{POST}} | {{/api/v1/user/getProfile}} | {{...}} | {{JWT}} |

---

## 6. WebSocket 协议（如有）

{{连接路径、鉴权方式、消息类型枚举、典型时序。只列消息字段契约，不贴 handler 实现。}}

| 消息类型 | 方向 | 字段 |
|---|---|---|
| {{...}} | {{c→s / s→c}} | {{...}} |

---

## 7. 核心子系统

{{按项目实际：SSH 会话管理 / 凭证加密 / 支付 / 计费 …，每个一小节描述架构与关键文件。}}

### 7.1 {{子系统}} (`{{internal/xxx}}`)

**职责**：{{1-2 句}}。关键文件与协作关系：{{...}}。

---

## 8. 数据模型

| 模型 | 表 | 关键字段 | 关系 |
|---|---|---|---|
| {{User}} | {{users}} | {{...}} | {{...}} |

{{迁移方式：AutoMigrate / migration 文件在哪。}}

---

## 9. 认证与安全（现状描述）

{{JWT 怎么签发/校验、中间件链、密钥来源、敏感数据加密体系。具体"必须脱敏/禁止明文"等要求归规范。}}

---

## 10. 配置系统

| 配置项 | 来源 | 用途 |
|---|---|---|
| {{LOG_LEVEL}} | {{.env}} | {{...}} |

---

## 11. 模块依赖关系图

```
{{ASCII art 或 Mermaid：cmd → internal/api → internal/services → pkg/*，画清依赖方向}}
```

---

## 12. 数据库初始化（如有）

{{初始化脚本/种子数据位置与执行方式。}}
