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

### 6.1 Logger 使用

- **必须**使用统一 logger（{{`pkg/logging`}}），**禁止**裸 `fmt.Println` / 标准库 `log.Println` 打业务日志。
- **必须**在 `main` 启动时先调用 {{`logging.InitLogger(level, dir, retainDays)`}}，再做后续依赖装配。
- **应该**用模块级实例承载固定字段：`log := logger.WithFields(logging.Logfield{"module": "ssh"})`。

```go
// ✅ Good — 模块作用域 + 结构化字段
log := logger.WithFields(logging.Logfield{"module": "ssh", "host_id": hostID})
log.Infof("ssh.session.opened", "session ready for user=%s", userID)

// ❌ Bad
fmt.Println("session ready")              // 裸打印
log.Printf("ok")                          // 标准库 log，无级别、无字段
```

### 6.2 日志级别

| 级别 | 值 | 用途 |
|------|----|------|
| {{DEBUG}} | {{0}} | {{开发调试；按模块开关，生产默认关闭}} |
| {{INFO}}  | {{1}} | {{用户可感知的关键事件：连接建立、订单生成、会话关闭}} |
| {{ERROR}} | {{2}} | {{需要人介入的错误；必须带错误码或 `%w` 包装的原始 err}} |

- 级别由 {{`LOG_LEVEL` 环境变量}}控制（{{`SetLogLevelFromString`}}）；**禁止**在业务代码里调用 `SetLogLevel` 硬改。
- **禁止**用 INFO 打印高频循环事件（>10 次/秒），改用 DEBUG 或采样。

### 6.3 日志格式与结构化字段

- 单行格式固定：`[YYYY-MM-DD HH:MM:SS] [LEVEL] key=val key2=val2 | message`
- **必须**用 {{`WithFields(Logfield{...})`}} 注入结构化字段，**禁止**把 `key=val` 拼进 message。
- 调用位置（`file:line` + `funcName`）由 logger {{自动注入}}，**禁止**手动拼到 message。
- 请求路径与跨服务调用**必须**带 {{`request_id` / `user_id` / `session_id`}} 等可追踪上下文字段。

```go
// ✅ 字段走 WithFields
log.WithFields(logging.Logfield{"request_id": rid}).Infof("ssh.connect", "dialed %s", addr)

// ❌ 字段塞进 message，破坏聚合检索
log.Infof("ssh.connect", "request_id=%s dialed %s", rid, addr)
```

### 6.4 日志文件与按日轮转

- 配置 {{`LOG_DIR`}} 后 logger 同时写 stdout 与文件（{{`io.MultiWriter`}}）；未配置则仅 stdout。
- 文件命名固定：当天 {{`<service>.log`}}（追加写入），按日轮转后改名为 {{`<service>-YYYY-MM-DD.log`}}。
- {{`LOG_RETAIN_DAYS`}} 控制保留天数（默认 {{30}}；`<=0` 表示永不删除）。
- 轮转由 logger 内部协程负责（{{`dailyRotateLoop` → `rotateLogFile` → `cleanExpiredLogs`}}）。**禁止**绕过 logger 直接 `os.OpenFile` 写日志路径——会让轮转与清理失效。

### 6.5 敏感信息脱敏

- **禁止**打印明文 token / password / 私钥 / 加密 key / 凭证 / 完整邮箱。
- 中间件/包装层若需打印请求体，**必须**对敏感字段（`password` / `token` / `secret` / `apiKey` / `authorization` 等）替换为 `***`。
- 客户端 IP 在访问日志里**必须**做{{尾段脱敏}}（如 `192.168.*.*`）。

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
