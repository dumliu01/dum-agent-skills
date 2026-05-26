# {{服务名}} — 开发规范

> 📏 本文档是**写代码必须遵守的约定**（规范性）。系统结构见 [`../architecture/{{service}}.md`](../architecture/{{service}}.md)。
> 🤖 项目入口：[`../../CLAUDE.md`](../../CLAUDE.md)
>
> 每条规范用祈使句 + ✅Good / ❌Bad 例子。下方为模板，**请替换成本项目实际约定**。

---

## 1. 命名规范（PEP 8）

| 对象 | 约定 | 例 |
|---|---|---|
| 模块/包 | {{snake_case}} | `ai_model.py` |
| 函数/变量 | {{snake_case}} | `parse_config` |
| 类 | {{PascalCase}} | `AIModelService` |
| 常量 | {{UPPER_SNAKE_CASE}} | `MAX_RETRY` |
| 私有 | {{前缀下划线}} | `_build_prompt` |

- {{遵循 PEP 8；用 {{ruff / black}} 统一格式}}。

---

## 2. 注释与 docstring 语言

- {{**所有代码注释与 docstring 使用英文**}}（含 TODO/FIXME）。
- {{公共模块/类/函数必须有 docstring（{{Google / NumPy}} 风格）}}。
- commit message {{使用英文}}；`.md` 文档{{可中文}}。

```python
# ✅ Good
def parse_ssh_config(raw: dict) -> SSHConfig:
    """Parse and validate raw SSH config into a typed object."""

# ❌ Bad: # 解析配置
```

---

## 3. 类型注解规范

- {{所有函数签名必须有参数与返回类型注解；禁止裸 `Any`（不得已用 `object`/`TypeVar` + 收窄）}}。
- {{对外数据用 Pydantic 模型校验，不传裸 dict}}。
- {{开启 {{mypy / pyright}} 检查，CI 拦截类型错误}}。

```python
# ✅ async def get_user(uid: int) -> UserOut: ...
# ❌ def get_user(uid): ...
```

---

## 4. 异步规范

- {{I/O 密集路径必须 `async def` + `await`，禁止在 async 函数里做阻塞调用}}。
- {{阻塞库（CPU 密集 / 同步 SDK）必须丢线程池：`await asyncio.to_thread(...)`}}。
- {{并发用 `asyncio.gather`；后台任务必须被持有引用并能取消，避免泄漏}}。

```python
# ❌ async def handler(): time.sleep(5)          # 阻塞 event loop
# ✅ async def handler(): await asyncio.sleep(5)
```

---

## 5. 错误处理与错误码体系

- {{捕获异常要具体，禁止裸 `except:`；不吞异常（至少记日志）}}。
- {{错误码集中在 `app/models/errors.py`（`ErrorCode` 枚举 + `ERROR_MESSAGES`），分段管理，新增按段}}。

| 范围 | 类别 | 示例 |
|------|------|------|
| 0 | 成功 | {{SUCCESS}} |
| {{1000-1099}} | 通用 | {{INVALID_REQUEST(1001), INTERNAL_ERROR(1002)}} |
| {{1100-1199}} | 认证 | {{UNAUTHORIZED(1101)}} |
| {{...}} | {{业务}} | {{...}} |

---

## 6. 日志规范

- {{统一用项目 logger，禁止裸 `print`}}。
- {{级别：{{debug/info/warning/error 各用于什么}}}}。
- {{结构化日志 + 敏感信息脱敏（token/密码/凭证禁止明文）——参见 LOGGING_STANDARD}}。

---

## 7. 配置规范

- {{所有配置走 Pydantic BaseSettings (`config/settings.py`) + `.env`，禁止硬编码}}。
- {{新增配置项必须加字段 + 默认值，并在架构文档配置表登记}}。
- {{声明式资源（模型/技能等）放 yaml，代码只读不写死}}。

---

## 8. 依赖管理

- {{用 {{uv / poetry / pip-tools}} 锁定依赖；改依赖必须更新锁文件}}。
- {{禁止在代码里 `pip install`；新依赖要说明用途}}。

---

## 9. 测试规范

- {{用 pytest，测试放 `tests/`，命名 `test_*.py`}}。
- {{async 测试用 `pytest-asyncio`；外部依赖用 fixture/mock 隔离}}。
- {{关键业务路径必须有用例}}。

---

## 10. 提交规范

- {{commit message 用英文，格式 `<type>: <subject>`}}。
- {{提交前跑 {{ruff / mypy / pytest}}}}。

---

## 11. 开发速查

| 场景 | 关键文件 |
|------|----------|
| 新增 endpoint | {{routes/ 加路由 → service 实现}} |
| 新增消息类型 | {{schemas.py MessageType + WS 模型}} |
| 新增错误码 | {{app/models/errors.py ErrorCode + ERROR_MESSAGES}} |
| 新增配置项 | {{config/settings.py 加字段 + .env}} |
| 新增 AI 供应商/模型 | {{config/models.yaml + settings API key}} |
| 修改 Prompt | {{app/prompts/...}} |
