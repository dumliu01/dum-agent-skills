# dum-server-api-test 技能设计（spec）

> 状态：已 brainstorm 定稿，待写实现计划。
> 日期：2026-07-20

## 1. 目标与定位

新增一个技能 `dum-server-api-test`：**给带服务端的项目生成并运行基于真实服务端 API 的功能测试用例**。

- 连**真实服务端**（不 mock），`go test` 驱动。
- 从 需求 / 技术方案 / 代码 读懂每个接口，给每个接口生成**多条**用例：正常流程 + 异常流程。
- 可按**功能模块**与**优先级**选择要跑哪些测试。

### 边界（与既有技能的分工）

- **补位 `dum-e2e-test`**：后者 SKILL.md 明确把「纯接口测试、无 UI」列为 When NOT to Use；本技能正好接这一块。`dum-e2e-test` 面向带 UI 的端到端；本技能面向无 UI 的服务端 API。
- **消费上游**：需求（`docs/原始需求`）、`dum-solution-design` 的技术方案（`docs/tech-design`）、代码。权威阶梯 需求 > 技术方案 > 代码。
- **交接下游**：失败结果原样透出；需定位根因转 `superpowers:systematic-debugging`，文档与代码冲突转 `dum-doc-reconcile`，改完记账用 `dum-session-summary`。

### 深度选择

**生成 + 运行为主**（不做 `dum-e2e-test` 那种脚本/用例/代码三段定责闭环）。失败即透出，并提示可转的下游技能。

### 参考项目

`/Users/dum/Vmware_Share/work_dev/aigc-agent/testcase/aigc-agent-manager` —— 本技能的脚手架与命名/注解约定对标该项目：
- Go + goconvey（`Convey`/`So`），连真实服务端。
- 配置驱动：`test.yml` → `config.go`（Config 结构 + yaml 加载）→ `A00_Main_test.go`（`TestMain` 初始化）。
- `tool.go`：随机串、配置转换、通用 helper。
- 命名：`<模块字母><NN>_<Module>_<Action>_test.go`，函数 `Test_<字母><NN>_<Name>`；字母分组即功能模块（A=Agent、B=Instance…）。
- 每个测试函数顶部注解 `@desc / @label / @interface / @dependent`。
- 每文件多条 `Convey` 子用例（正常 + 异常），末尾「清理数据」子 Convey。
- `build.sh` 编译成测试二进制，`run.sh <config> [-test.run <regex>]` 运行。

## 2. 已定决策（brainstorm 结论）

| 维度 | 决策 |
|---|---|
| 技能定位/深度 | 生成 + 运行为主，不做定责闭环 |
| 调用方式 | 自动探测：优先复用目标项目已有 Go client SDK；无则回退裸 HTTP（`net/http`，或项目已用的 resty） |
| 模块+优先级选择机制 | 命名约定 + `run.sh` 包装 |
| 断言风格 | 一律 goconvey（`Convey`/`So`） |
| 测试工程落点 | `testcase/<service>-api-test/` |
| 用例清单产物 | 轻量：测试文件顶部 `@desc/@label/@interface` 注解 + 一份 `docs/test-cases/<service>-api.md` 汇总表 |
| 技能命名 | `dum-server-api-test` |

## 3. 工作流（4 阶段）

### ① 摄入与探测（Ingest & Probe）

按权威阶梯 需求 > 技术方案 > 代码，逐接口抽取：入参 / 出参 / 鉴权 / 错误码 / 前置依赖 / 副作用。

探测目标项目：
- 有无现成 Go client SDK（grep `client` 包、`http_client`、`NewXxxClient`）→ 有则复用；无则回退裸 HTTP。
- `go.mod` module path（拼 import）。
- 鉴权方式（签名 / token / header）、baseURL、错误码表。

**产出**：接口清单（接口 × 优先级 × 依赖 × 是否有副作用）。

### ② 用例设计（Case Design）

每个接口 ≥ 正常流程（happy path，断言 `code==0` / 期望字段）+ 异常流程（按接口语义从异常 checklist 选：参数缺失/非法、鉴权失败、重复操作、限流/并发、越界、依赖不存在…）。

优先级分层：
- **P0** = 核心正常流程 + 关键异常
- **P1** = 常规异常
- **P2** = 边界 / 极端

**产出**：`docs/test-cases/<service>-api.md` 汇总表：接口 | 用例名 | 优先级 | 类型(正常/异常) | 期望 | 依赖 | 副作用/清理。

### ③ 脚手架 + 生成（Scaffold & Generate）

脚手架（asset 模板，对标参考项目），落 `testcase/<service>-api-test/`：
- `config.go`（Config 结构 + yaml 加载）
- `test.yml.example`（baseURL / appId / secret / 超时 / 各模块参数，敏感值占位）
- `tool.go`（随机串、签名、`doRequest(method, path, body, headers)` HTTP helper、断言 helper）
- `A00_Main_test.go`（`TestMain`：加载配置、初始化 client/HTTP、可选日志/清理钩子）
- `build.sh` · `run.sh` · `.gitignore`

复用已有 SDK 时：`TestMain` new 项目 client；否则用 `tool.go` 的 HTTP helper。

测试文件：
- 命名 `<模块字母><NN>_<Interface>_test.go`，函数 `Test_<字母><NN>_<P0|P1|P2>_<Case>`（如 `Test_A01_P0_Register_Normal`）。
- 顶部块注释 `@desc / @label(优先级) / @interface / @dependent`。
- goconvey：外层 `Convey(接口名)`，内层逐条正常/异常子 `Convey` + 末尾「清理数据」。
- 模块字母（A/B/C…）自动分配（一个功能模块一个字母），映射记入汇总表与 `run.sh` 注释。

### ④ 选择运行（Select & Run）

命名约定 + `run.sh` 包装：

```
run.sh <config> [--module A,B] [--priority p0,p1] [--interface RegisterAgent] [--list] [--run <regex>]
```

- module → 字母前缀、priority → `_P0_` 片段，拼成 `-test.run` 正则（如 `^Test_(A|B)\d+_P0_`）。
- 无参跑全部；`--list` grep 注解列出可选模块/优先级。
- `build.sh` 编译；`run.sh` 支持源码直跑（`go test`）或跑二进制。
- 透出 `go test -v` 结果，失败原样呈现，并提示可转下游技能。

## 4. 真实服务端护栏（贯穿全流程）

- 只连测试/beta 环境，`config` 里 baseURL 显式。
- 敏感值（secret/apiKey/token）占位 + `.gitignore` 真实 config，只提交 `test.yml.example`。
- **每条产生资源的用例末尾必须「清理数据」子 Convey**（对标参考项目）。
- 破坏性/不可逆接口（删除、扣费、发送）汇总表标注，默认需用户确认纳入。
- id/名字随机化避免脏数据；并发用例隔离 AppId/资源。

## 5. 技能包结构（对标 dum-e2e-test 的 assets/references）

```
skills/dum-server-api-test/
  SKILL.md                       # 正文工作流（4 阶段 + 护栏 + When to / NOT to Use + 跨 agent 工具名说明）
  README.md                      # 安装/触发说明
  assets/
    config.go.tmpl               # Config 结构 + yaml 加载
    tool.go.tmpl                 # 随机串/签名/doRequest/断言 helper（裸 HTTP 回退）
    main_test.go.tmpl            # TestMain
    api_test.go.tmpl             # 单接口测试文件模板（goconvey，正常+异常+清理）
    test.yml.example             # 配置示例（敏感值占位）
    build.sh                     # 编译测试二进制
    run.sh                       # --module/--priority/--interface/--list 选择器
    test-cases.md.tmpl           # 汇总表模板
  references/
    interface-inventory.md       # 从需求/方案/代码抽接口清单 + 优先级分层规则
    abnormal-catalog.md          # 异常流程用例 checklist（按接口语义：鉴权/参数/重复/限流/越界/依赖…）
    naming-and-selection.md      # 命名约定 ↔ run.sh 选择正则的完整规则
```

## 6. 收尾同步（发布为多 agent 插件）

- `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` 版本号 bump（1.2.0 → 1.3.0，新技能）。
- 根 `CLAUDE.md` 技能清单加一行 + 衔接段补 `dum-server-api-test` 与 `dum-e2e-test`/`dum-solution-design` 的关系。
- `README.md` 技能列表。
- `CHANGELOG.md` 新条目。
- 各 agent manifest（`.codex-plugin/`、`.cursor-plugin/`、`gemini-extension.json`）如各有薄 manifest 指向 `skills/`，按现有模式同步（实现时逐一核对具体文件）。

## 7. 非目标（YAGNI）

- 不做失败三段定责闭环（那是 `dum-e2e-test` 的范畴）。
- 不做非 Go 语言的测试生成（本技能锁定 `go test`）。
- 不做压测/性能测试（功能测试为主）。
- 不做 mock / 契约测试。
