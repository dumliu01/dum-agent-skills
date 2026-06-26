# 测试用例模板

> 复制此文件到 `docs/test-cases/<feature>.md`，每个场景一个二级标题块。  
> 字段定义来源：方案 §4.1 + references/oracle-and-data.md。  
> **必填字段**：id / title / platform / provenance / steps / expected_interaction / expected_display / expected_data / authority。  
> 可选字段：preconditions / data_setup / cleanup / conflicts（无则填 `无`）。

---

## 字段说明

| 字段 | 说明 |
|---|---|
| `id` | 用例唯一编号，格式 `TC-<feature>-<序号>`，如 `TC-login-001` |
| `title` | 一句话描述场景 |
| `platform` | `web` / `electron` / `flutter` / `android` / `ios` |
| `provenance` | **溯源链接**：格式 `<权威层>:<文件路径>#<章节>`，指向此用例期望所依据的最高权威条款 |
| `preconditions` | 前置状态（登录态 / 角色 / 后端 mock / 依赖数据） |
| `data_setup` | **走后门**布置的前置数据：走 API 还是 DB、造哪些记录（见 references/oracle-and-data.md §1） |
| `steps` | 操作步骤（语义动作，非脚本代码） |
| `expected_interaction` | **交互预言机**：操作后的即时 UI 反馈（toast / 页面跳转 / 按钮态 / 弹窗关闭） |
| `expected_display` | **展示预言机**：界面上呈现的数据值应符合预期；附 `source`：`dom`（默认结构化提取）/ `visual`（视觉回归）/ `ocr`（无 DOM 文本兜底） |
| `expected_data` | **数据预言机**：持久化状态断言；附 `gateway`：`api`（默认黑盒）/ `db`（白盒兜底，须说明原因） |
| `cleanup` | 清理方式（可写 `继承环境清单默认` 或具体方式：truncate / 回滚 / 销毁） |
| `authority` | 期望所依据的最高权威层级：`需求` / `技术方案` / `代码` |
| `conflicts` | 相关冲突点（指向冲突报告条目；无则填 `无`） |

---

## 用例模板块

复制以下块，每个场景一份，放在本文件对应 feature 章节下。

---

### TC-FEATURE-001: <一句话场景标题>

**id**: `TC-FEATURE-001`  
**title**: <一句话场景，如「用户提交错误密码，登录失败并显示错误提示」>  
**platform**: `web`  

**provenance**:  
`需求:docs/原始需求/<需求文件>.md#<章节锚点>`

**preconditions**:
- 用户未登录
- 测试用户账号已存在（由 data_setup 造）
- 无外部服务依赖（或 mock 已配置）

**data_setup**:
```
方式: api
操作: POST /api/test/users/factory { email: "tc001@test.local", password: "correct-pwd" }
说明: 走后门 API 造测试用户；无 factory API 时降级 DB 直插 users 表
```

**steps**:
1. 打开登录页 `/login`
2. 在「邮箱」字段输入 `tc001@test.local`
3. 在「密码」字段输入 `wrong-password`
4. 点击「登录」按钮

**expected_interaction**:
- 按钮进入加载态（文字变为「登录中…」或 spinner 出现）
- 请求返回后，页面不跳转，停留在 `/login`
- 出现错误 toast，文本包含「密码错误」或「账号或密码不正确」

**expected_display**:
```
source: dom
断言:
  - 错误提示元素（role=alert 或 data-testid=login-error）textContent 包含「密码错误」
  - 密码字段未被清空（可选：按产品设计）
  - 「登录」按钮恢复可点击状态
```

**expected_data**:
```
gateway: api
断言: GET /api/me 返回 401（用户未登录态）
说明: 登录失败不应产生有效 session；API 黑盒验证即可
```

**cleanup**: 继承环境清单默认（truncate users 或容器销毁）

**authority**: `需求`

**conflicts**: 无

---

## 补充说明

### 三层校验要求

每条含数据变更的用例**必须同时断言三层**（缺层须说明原因）：

| 层 | 字段 | 说明 |
|---|---|---|
| 交互 | `expected_interaction` | 操作即时反馈（toast / 跳转 / 状态） |
| 界面数据展示 | `expected_display` | 页面渲染的数据值（dom / visual / ocr） |
| 持久化 | `expected_data` | 后端状态（api 优先 / db 兜底） |

### data_setup 走后门原则

- 前置数据**不走 UI 点击**造，避免耦合被测场景。
- 优先调后端 **factory API**（`gateway: api`）；无 API 时 **DB 直插**（`gateway: db`）并说明原因。
- `data_setup` 的 seed 句柄须在 `cleanup` 或环境清单 reset_hook 中回收。

### provenance 格式

```
需求:docs/原始需求/xxx.md#章节锚点
技术方案:docs/tech-design/xxx.md#章节锚点
代码:src/xxx/yyy.ts#行号或函数名
```

溯源层级优先选最高权威；多条款时列多行，用换行分隔。
