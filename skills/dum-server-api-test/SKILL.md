---
name: dum-server-api-test
description: Use when 用户要给带服务端的项目做接口/API 功能测试、写 go test 接口用例、连真实服务端验证接口行为、按模块或优先级选跑接口测试。能力：按权威阶梯(需求>技术方案>代码)读懂每个接口 → 设计正常+异常用例(P0/P1/P2) → 生成可编译 Go 测试(goconvey，连真实服务端不 mock，优先复用项目已有 client SDK 否则裸 HTTP) → 命名约定+run.sh 按 --module/--priority 选跑。落点 testcase/<service>-api-test/ 与 docs/test-cases/<service>-api.md。Triggers - "写接口测试"/"API 功能测试"/"go test 测接口"/"生成接口测试用例并跑"/"按模块/优先级跑接口测试"/"服务端接口测试"。区别 dum-e2e-test：那个带 UI 端到端，本技能无 UI 纯服务端 API。
---

# dum-server-api-test（服务端 API 功能测试工作流）

## Overview

本技能把「带服务端的项目」的接口功能测试做成四阶段流水线：从需求/技术方案/代码里摄入并探测每个接口，设计正常+异常用例并分优先级，生成连真实服务端跑的 Go 测试（goconvey 断言，不 mock），最后按命名约定用 `run.sh` 按模块/优先级选跑。

```
① 摄入与探测  →  ② 用例设计  →  ③ 脚手架 + 生成  →  ④ 选择运行
```

**权威阶梯**（贯穿全流程）：需求 > 技术方案 > 代码。接口行为以最高可得权威为准，代码仅在需求/方案缺失时兜底。

**四阶段一览**：

| 阶段 | 产物 | 落点 |
|---|---|---|
| ① 摄入与探测 | 接口清单（入参/出参/鉴权/错误码/依赖/副作用） | 随 SKILL 产出，供②③消费 |
| ② 用例设计 | 正常+异常用例文档（P0/P1/P2 分层） | `docs/test-cases/<service>-api.md` |
| ③ 脚手架 + 生成 | 共享引擎(复用) + 可编译 Go 测试薄壳（goconvey） | 公共 `testcase/apitest-common/` + 本服务 `testcase/<service>-api-test/` |
| ④ 选择运行 | 编译产物 + 按 `--module`/`--priority` 选跑的结果 | `testcase/{build,run}.sh <服务目录> …`（脚本在 testcase/ 层，参数化） |

---

## When to Use

| 触发场景 | 例子 |
|---|---|
| 用户明确请求接口/API 功能测试 | "给用户服务写接口测试" / "API 功能测试" / "go test 测接口" |
| 要连真实服务端验证接口行为 | "起个测试环境，把这几个接口跑一遍" |
| 生成用例并要求可跑、可按范围选跑 | "生成接口测试用例并跑" / "按模块/优先级跑接口测试" |
| 需求/技术方案/代码三者对齐校验（无 UI） | "我改了这个接口的错误码，想跑用例确认" |

## When NOT to Use

| 场景 | 替代 |
|---|---|
| 带 UI 的端到端测试 | `dum-e2e-test`（本技能无 UI，纯服务端 API） |
| 纯单元测试，无网络调用 | 直接写 unit test，无需本技能 |
| 压测/性能测试 | 非本技能范围，用专门的压测工具 |
| mock/契约测试 | 非本技能范围（本技能连真实服务端，不 mock） |
| 只跑一次的临时验证 | 直接 `curl`，不必生成用例与工程 |

---

## 核心原则

1. **权威阶梯**：需求 > 技术方案 > 代码。接口的入参/出参/错误码/前置依赖以最高可得权威层为准；代码只在文档缺失时作为兜底来源，且需在接口清单中标注来源层级。
2. **连真实服务端，不 mock**：所有测试直连测试/beta 环境的真实服务端，验证的是接口真实行为，不允许用 mock server 替代。
3. **每接口多条 = 正常 + 异常**：每个接口至少 1 条正常流程用例，并按接口语义补齐适用的异常用例（鉴权/参数/幂等/依赖/状态机，见 `references/abnormal-catalog.md`）。
4. **优先级分层 P0/P1/P2**：P0 = 核心正常流程 + 关键异常（鉴权失败/关键参数非法）；P1 = 常规异常；P2 = 边界/极端场景。分层规则详见 `references/interface-inventory.md`。
5. **真实服务端护栏**：只连测试/beta 环境；敏感值占位不入库；产生资源的用例末尾必须有「清理数据」子 Convey；破坏性接口需先与用户确认再纳入。详见下方「真实服务端护栏」小节。

---

## 阶段① 摄入与探测

**目标**：从权威文档与代码里把每个待测接口的完整契约抽出来，产出接口清单。

**读入顺序（按权威阶梯）**：

1. 需求文档（`docs/product-design/`、原始需求）——若存在，接口行为以此为准。
2. 技术方案（`docs/tech-design/`）——接口契约（path/method/schema/错误码）的主要来源。
3. 代码实现——需求/方案缺失或含糊时兜底，直接读 handler/router/DTO 确认真实行为。

**探测目标项目**（用 `Grep`/`Glob`/`Read`）：

- 找项目是否已有 Go client SDK：`Grep` 搜 `NewXxxClient` / `type.*Client struct` / `pkg/client`、`sdk/` 等目录。有则优先复用；无则走裸 HTTP。
- 读 `go.mod` 确认 module path，供测试工程 `import` 目标包或复用其类型。
- 确认鉴权方式（token/签名/session）、baseURL 配置来源、统一错误码结构（是否有 `code`/`message` 包裹）。

**每接口抽取的字段**：method+path、鉴权方式、请求体字段（必填/可选/类型/约束）、响应体结构+错误码、前置依赖（需要先创建的资源）、副作用（是否产生/删除资源、是否扣费/发通知等）。

**产出**：接口清单（见 `references/interface-inventory.md` 的清单表模板），标注每个接口的模块字母与初步优先级建议，供阶段②消费。

详见 `references/interface-inventory.md`。

---

## 阶段② 用例设计

**目标**：把接口清单转成带溯源的正常+异常用例文档，并分好优先级。

**步骤**：

1. 每个接口先写 1 条核心正常流程用例（P0）。
2. 按接口语义从 `references/abnormal-catalog.md` 的异常 checklist 里勾选适用项（鉴权类/参数类/幂等冲突类/依赖类/状态机类），每类给出预期断言要点（`code != 0` / 特定错误码 / `err != nil`）。
3. 按核心原则第 4 条给每条用例定优先级 P0/P1/P2。
4. 用 `assets/test-cases.md.tmpl` 为蓝本写出用例文档，落到 `docs/test-cases/<service>-api.md`。

**落点**：`docs/test-cases/<service>-api.md`

**模板**：`assets/test-cases.md.tmpl`

详见 `references/abnormal-catalog.md`。

---

## 阶段③ 脚手架 + 生成

**目标**：把用户确认后的用例翻译成可编译的 Go 测试工程。

> **公共脚手架复用优先**：HTTP 引擎 / 配置加载 / 登录换 JWT 引导 / 依赖版本 / 构建脚本是**跨服务共用**的，抽成 `testcase/apitest-common/`（独立 Go module `apitest-common`，包名 `apitesting`）+ `testcase/` 层参数化 `build.sh`/`run.sh`，**每个 testcase/ 只建一次，后续每个待测服务只生成薄壳、复用公共引擎**——不要每个服务重复生成整套引擎。

**步骤**：

1. **建/复用公共脚手架（每个 `testcase/` 一次）**：
   - `testcase/apitest-common/`：若不存在，从 `assets/scaffold/apitest-common/` 复制过去（`client.go` HTTP 引擎 + `config.go` 泛型 yaml 加载 + `bootstrap.go` 双登录引导 + `envelope.go` 统一封套 + `go.mod`）；已存在则直接复用，**不重复生成**。
   - `testcase/build.sh`、`testcase/run.sh`：若不存在，从 `assets/scaffold/testcase-scripts/` 复制过去（参数化：第一位置参数是服务目录）；已存在则复用。
2. **生成本服务薄壳**：复制 `assets/scaffold/service/*` 到 `testcase/<service>-api-test/`，按目标服务改：
   - `config.go`：`Config` 的字段（`baseURL`/`loginBaseURL`/`loginPath`、内部密钥、`CapabilitiesConfig` 开关）。
   - `tool.go`：便捷方法名与 baseURL/鉴权语义（示例 `Do/DoAdmin/DoToken/DoH/DoRaw` → 按服务改成 `Mail*`/`Server*` 等）；`Envelope`/`Credential` 是共享类型的**别名**，测试文件直接用不变。
   - `test.yml.example`、`.gitignore` 按需微调。
   - `go.mod` 已带 `require apitest-common` + `replace apitest-common => ../apitest-common`；改完跑 `go mod tidy`（自动补 require/go.sum，`yaml.v3` 转 indirect，`goconvey` 保持直接依赖）。
3. **选调用策略**：
   - **优先复用项目已有 client SDK**：若阶段①探测到目标项目暴露了 Go client SDK，在 `A00_Main_test.go` 中 new 该 SDK 的 client 并直接调用其方法。
   - **否则走共享引擎**（薄壳默认）：用 `tool.go` 的便捷方法（内部调 `cli.EnvDo`/`cli.RawDo`）发请求；`{code,message,data}` 封套用 `EnvDo` 取 `Envelope`，非此封套用 `RawDo` 取原始字节；签名类鉴权把 token 传 `""`、在 headers 里放签名头。
4. 按 `references/naming-and-selection.md` 的规则命名测试文件与函数：文件 `<字母><NN>_<Interface>_test.go`，函数 `Test_<字母><NN>_<P0|P1|P2>_<Case>`。
5. 每个测试函数头部写 `@desc / @label / @interface / @dependent` 注解（语义见 `references/naming-and-selection.md`），供 `run.sh` 与 `--list` 解析。
6. goconvey 结构：外层一个接口一个 `Convey`，内层按正常/异常场景拆子 `Convey`，用 `So` 断言；**每条产生资源的用例末尾必须加「清理数据」子 Convey**，删除/回收本用例产生的资源。

**落点**：公共引擎 `testcase/apitest-common/` + 脚本 `testcase/{build,run}.sh`（各一次）；本服务薄壳 `testcase/<service>-api-test/`。

**脚手架**：`assets/scaffold/apitest-common/`（共享引擎）、`assets/scaffold/testcase-scripts/`（脚本）、`assets/scaffold/service/`（每服务薄壳）。

详见 `references/naming-and-selection.md`。

---

## 阶段④ 选择运行

**目标**：编译测试工程，按模块/优先级/接口选跑，失败时按定责路径转出。

**步骤**（脚本在 `testcase/` 层，第一位置参数是服务目录）：

1. `testcase/build.sh <service>-api-test` 编译测试工程为 `apitest.test`，确认可编译通过。
2. `testcase/run.sh <service>-api-test <config.yml> [flags]` 选跑，flag 支持 `--module`（字母，逗号分隔）、`--priority`（p0/p1/p2，逗号分隔）、`--interface`（按 `@interface` 注解匹配）、`--list`（列出全部可选项）、`--run`（直接给正则）。参数会被拼成 `-test.run` 正则去选跑，映射规则与 worked example 见 `references/naming-and-selection.md`。`<config.yml>` 相对/绝对路径均可（脚本内部会在切目录前解析为绝对路径）。
3. 跑之前先用 `testcase/run.sh <service>-api-test <config> --list` 核对将要跑的范围（模块/优先级/接口是否符合预期），再去掉 `--list` 真正执行。
4. **失败处理**：把失败原始日志/断言输出透出给用户；若怀疑是代码 bug，需要先定位根因，提示转 `superpowers:systematic-debugging`；若怀疑是需求/方案与代码不一致，提示转 `dum-doc-reconcile`；测试工程/用例文档改动完成后，提示用 `dum-session-summary` 记账。

**落点**：`testcase/<service>-api-test/`（`apitest.test` 编译产物就地产出）；脚本与运行入口在 `testcase/{build,run}.sh`。

---

## 真实服务端护栏

本技能所有测试直连真实服务端（测试/beta 环境），因此必须遵守以下护栏：

- **只连测试/beta 环境**：`test.yml`/配置文件里的目标地址必须显式指向测试或 beta 环境，禁止指向生产环境；生成脚手架时向用户确认目标环境。
- **敏感值占位**：账号、密钥、token 等敏感配置在测试工程内用占位符，不写入真实值到会被提交的文件；真实配置放本地未纳入版本控制的文件。
- **`.gitignore` 真实 config**：脚手架自带的 `.gitignore` 须排除包含真实敏感值的配置文件（如 `test.yml` 的本地覆盖版本），避免误提交。
- **清理数据**：每条产生资源（创建/写入）的用例，末尾必须有「清理数据」子 Convey，把本用例产生的资源删除/回收干净，避免测试环境脏数据累积。
- **破坏性接口需确认**：涉及不可逆或高影响的破坏性接口（如批量删除、清空、不可逆状态迁移），生成对应用例前必须先与用户确认是否纳入测试范围。

---

## 跨 agent 工具名

本技能正文使用 Claude Code 工具名（Read/Write/Edit/Bash/Grep/Glob）；其它 agent 用等价工具替换即可，完整对照表见根 `CLAUDE.md`「跨 agent 工具名对照」。

---

## 产物落点

| 产物 | 落点（强制） | 格式 |
|---|---|---|
| 测试用例文档 | `docs/test-cases/<service>-api.md` | Markdown，按 `assets/test-cases.md.tmpl` |
| 公共引擎（每 testcase/ 一次） | `testcase/apitest-common/` | 独立 module `apitest-common`(pkg `apitesting`)，按 `assets/scaffold/apitest-common/` |
| 参数化脚本（每 testcase/ 一次） | `testcase/build.sh`、`testcase/run.sh` | Bash，第一参数为服务目录，按 `assets/scaffold/testcase-scripts/` |
| 本服务测试薄壳 | `testcase/<service>-api-test/` | Go + goconvey，`require+replace ../apitest-common`，按 `assets/scaffold/service/` |
