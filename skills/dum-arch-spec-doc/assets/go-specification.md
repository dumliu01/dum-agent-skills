# {{服务名}} — 开发规范

> 📏 本文档是**写代码必须遵守的约定**（规范性）。系统结构见 [`../architecture/{{service}}.md`](../architecture/{{service}}.md)。
> 🤖 项目入口：[`../../CLAUDE.md`](../../CLAUDE.md)
>
> 每条规范用祈使句 + ✅Good / ❌Bad 例子。下方为模板，**请替换成本项目实际约定**。

---

## 1. 命名与包组织规范

| 对象 | 约定 | 例 |
|---|---|---|
| 包名 | {{小写单词、无下划线、与目录同名}} | `payment` |
| 文件 | {{snake_case.go}} | `ssh_client.go` |
| 导出标识 | {{PascalCase}} | `NewClient` |
| 私有标识 | {{camelCase}} | `parseConfig` |
| 接口 | {{-er 后缀或语义名}} | `Encryptor` |
| 错误变量 | {{Err 前缀}} | `ErrNotFound` |

- {{私有业务代码放 `internal/`；可复用、无业务的放 `pkg/`}}。
- {{`pkg/` 禁止 import `internal/`（依赖只能向内）}}。

---

## 2. 注释语言

- {{**所有代码注释必须使用英文**}}（含 doc comment、TODO/FIXME）。
- {{导出标识必须有以名字开头的 doc comment}}。
- commit message {{使用英文}}；`.md` 文档{{可中文}}。

```go
// ✅ Good
// NewClient creates an SSH client and dials the host.
func NewClient(cfg Config) (*Client, error) { ... }

// ❌ Bad: // 创建客户端
```

---

## 3. 错误处理规范

- {{错误必须处理或显式返回，禁止 `_ =` 吞错}}。
- {{包装错误用 `fmt.Errorf("...: %w", err)` 保留链}}。
- {{哨兵错误用 `errors.Is`/`errors.As` 判断，不比较字符串}}。
- {{不 panic 业务错误；panic 仅用于不可恢复的初始化失败}}。

```go
// ✅ if err != nil { return fmt.Errorf("dial host: %w", err) }
// ❌ if err != nil { return errors.New("failed") }  // 丢了原因和链
```

---

## 4. API 风格约定

- {{采用 **RPC 风格**：所有业务接口统一 `POST`，参数与响应走 JSON Body}}。
- {{URL 格式 `POST /api/v{N}/{module}/{action}`；module 用单数名词，action 用 camelCase 动词}}。
- {{不用 GET/PUT/DELETE（健康检查、WS 升级、第三方回调除外）；ID/分页/筛选放 Body，不用 query string}}。
- {{HTTP 状态码恒为 200（传输异常除外），业务结果由 `code` 区分}}：

```json
{ "code": 0,    "message": "success", "data": { } }
{ "code": 1001, "message": "invalid request", "data": null }
```

---

## 5. 错误码体系

- {{错误码集中定义在 `pkg/errors/errors.go`，分段管理；新增错误码必须落到对应段并配 message}}。

| 范围 | 模块 | 示例 |
|------|------|------|
| 0 | 成功 | {{ErrCodeSuccess}} |
| {{1001-1099}} | 通用 | {{InvalidRequest, InternalError}} |
| {{1100-1199}} | 认证 | {{Unauthorized, InvalidToken}} |
| {{1200-1299}} | 权限 | {{Forbidden}} |
| {{...}} | {{业务模块}} | {{...}} |

---

## 6. 日志规范

- {{统一用 `pkg/logging`，禁止裸 `fmt.Println`}}。
- {{级别：{{DEBUG/INFO/ERROR 各用于什么}}；级别由 `LOG_LEVEL` 控制}}。
- {{用结构化字段 `WithFields`，关键路径带 request_id 等上下文}}。
- {{禁止打印 token / 密码 / 凭证明文}}。

格式约定示例：`[YYYY-MM-DD HH:MM:SS] [LEVEL] key=val | message`

---

## 7. 并发规范

- {{每个 goroutine 必须有明确的退出条件，禁止泄漏}}。
- {{用 `context.Context` 传递取消信号，长操作必须 select ctx.Done()}}。
- {{channel 由发送方负责关闭；禁止向已关闭 channel 写}}。
- {{共享状态用 mutex 或 channel 保护，避免 data race（CI 跑 `-race`）}}。

---

## 8. 配置规范

- {{所有可变参数走配置（env / configs/*.yaml），禁止硬编码}}。
- {{env 命名 UPPER_SNAKE_CASE；新增配置项必须给默认值并在架构文档配置表登记}}。
- {{机密只从环境/密钥管理读，禁止入库 git}}。

---

## 9. 测试规范

- {{测试与被测文件同包，命名 `xxx_test.go`}}。
- {{表驱动测试优先；关键业务路径必须有用例}}。
- {{外部依赖用接口 + mock 隔离}}。

---

## 10. 提交规范

- {{commit message 用英文，格式 `<type>: <subject>`}}。
- {{提交前跑 `go vet` / `golangci-lint` / `go test ./...`}}。

---

## 11. 开发速查

| 场景 | 操作位置 |
|------|----------|
| 新增 API 接口 | {{internal/api 加 handler + struct → routes 注册 POST}} |
| 新增数据模型 | {{internal/models 加 struct → AutoMigrate}} |
| 新增错误码 | {{pkg/errors 加 const + message}} |
| 新增中间件 | {{internal/api/middleware → routes 使用}} |
| 新增 WS 消息类型 | {{...}} |
| 调整日志级别 | {{.env LOG_LEVEL}} |
