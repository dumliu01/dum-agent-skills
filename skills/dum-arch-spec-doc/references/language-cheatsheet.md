# 各语言 arch / spec 章节速查

每种语言两份文档该有哪些节、差异点在哪，以及怎么加新语言。章节是**建议骨架**——按项目实际增删，但别把规范内容塞进架构（见 [`arch-vs-spec-split.md`](arch-vs-spec-split.md)）。

## 前端（TS / React / Electron / Vue）

**架构** [`assets/frontend-architecture.md`]：概述(使命/技术栈/进程模型) · 目录结构(AUTO-GENERATED) · 视图与路由 · 状态管理 · IPC 通信(Electron) · 服务层 · 组件结构 · 类型系统 · 主题与国际化 · 数据同步/认证 · 构建与部署 · 模块依赖图

**规范** [`assets/frontend-specification.md`]：命名 · 注释语言 · 组件编写 · TS 类型 · 状态管理 · 样式 · API 调用 · **性能(分包/懒加载/事件隔离)** · 国际化 · 日志 · 提交 · 开发速查

差异点：
- Electron 才有「IPC 通信」「main 进程文件 I/O」；纯 Web/Vue 删掉，换成路由/store 章节。
- 性能规范是前端重头戏（bundle 分包、懒加载边界、"禁止静态导入"硬规则），别省。
- 「数据同步/认证」描述现状归架构；「API 调用必须走统一封装」归规范。

## Go 后端

**架构** [`assets/go-architecture.md`]：概述(使命/技术栈/入口) · 目录结构(AUTO-GENERATED) · 分层(Clean Architecture) · 启动流程 · API 路由总览 · WebSocket 协议 · 核心子系统 · 数据模型 · 认证与安全 · 配置系统 · 模块依赖图 · 数据库初始化

**规范** [`assets/go-specification.md`]：命名与包组织 · 注释语言 · 错误处理 · **API 风格约定** · **错误码体系** · 日志 · 并发 · 配置 · 测试 · 提交 · 开发速查

差异点：
- 分层（internal/、pkg/、cmd/）是 Go 架构核心，画清依赖方向。
- API 风格（RPC-style POST、统一 code 响应）+ 错误码分段是 Go 规范两大重头。
- 并发规范（goroutine 生命周期、context 取消、channel 关闭方）Go 专属，必写。

## Python 后端

**架构** [`assets/python-architecture.md`]：概述(使命/技术栈/入口) · 目录结构(AUTO-GENERATED) · 分层/执行模式 · WebSocket 协议 · 核心服务系统 · 数据模型/schemas · 认证与安全 · 配置系统(Pydantic) · 模块依赖图

**规范** [`assets/python-specification.md`]：命名(PEP8) · 注释与 docstring 语言 · 类型注解 · **异步规范** · **错误处理与错误码** · 日志(结构化/脱敏) · 配置(Pydantic/env) · 依赖管理 · 测试(pytest) · 提交 · 开发速查

差异点：
- 类型注解 + Pydantic 模型在 Python 后端是规范重点（FastAPI 项目尤甚）。
- 异步规范（async/await、不阻塞 event loop、阻塞调用丢线程池）必写。
- 配置规范围绕 Pydantic BaseSettings + .env + yaml 声明式定义。

## 通用骨架（扩展用）

[`assets/generic-architecture.md`] / [`assets/generic-specification.md`] 是不绑语言的精简骨架，加新语言（Rust / Java / Kotlin …）时从这两份起手。

## 怎么加一种新语言

1. 复制 `generic-architecture.md` → `<lang>-architecture.md`、`generic-specification.md` → `<lang>-specification.md`。
2. 按该语言习惯改章节：架构补它特有的分层/运行模型（如 Rust 的 crate/feature、Java 的模块/Bean）；规范补它特有的写法约定（如 Rust 的 ownership/clippy、Java 的异常/注解）。
3. 在本文件加一节，列出新语言的章节清单 + 差异点。
4. 在 `SKILL.md` 第 0 步「判语言」加该语言的标志文件识别（如 `Cargo.toml` → Rust）。
