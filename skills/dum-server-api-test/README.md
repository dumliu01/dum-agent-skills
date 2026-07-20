# dum-server-api-test

> 给带服务端的项目做接口/API 功能测试：**4 阶段流水线**（摄入探测 / 用例设计 / 脚手架生成 / 选择运行）+ 连真实服务端不 mock + goconvey 断言 + 命名约定驱动的 `run.sh` 选跑。

## 它做什么

接口测试容易有三类问题：（1）用例只覆盖正常流程，异常边界靠临时想；（2）测试连不上真实服务端，靠 mock 掩盖了真实联调问题；（3）用例一多就没法按范围选跑，只能全量跑。本技能把接口测试做成固定四阶段流水线，产出可编译、连真实服务端、按模块/优先级可选跑的 Go 测试工程。

**四阶段**：

1. **摄入与探测** — 按权威阶梯（需求 > 技术方案 > 代码）抽取每个接口的入参/出参/鉴权/错误码/依赖/副作用，探测目标项目是否已有 client SDK。
2. **用例设计** — 每接口至少 1 正常 + 按语义选异常（鉴权/参数/幂等/依赖/状态机），分 P0/P1/P2 优先级。
3. **脚手架 + 生成** — 复制脚手架生成 Go 测试工程，goconvey 断言，优先复用目标项目已有 client SDK，否则裸 HTTP。
4. **选择运行** — `build.sh` 编译，`run.sh` 按 `--module`/`--priority`/`--interface`/`--list` 选跑。

## 何时触发

- "写接口测试" / "API 功能测试" / "go test 测接口"
- "生成接口测试用例并跑"
- "按模块/优先级跑接口测试"
- "服务端接口测试" / "连真实服务端验证接口行为"

## 与 dum-e2e-test 的分工

两者按**有无 UI**分工：

| | `dum-server-api-test`（本技能） | `dum-e2e-test` |
|---|---|---|
| 测试对象 | 纯服务端 API，无 UI | 带 UI 的前端/客户端（Web/Electron/Flutter） |
| 断言方式 | goconvey（`Convey`/`So`） | 三层校验（交互/界面数据展示/持久化） |
| 环境 | 连真实测试/beta 服务端，不 mock | 起前后端，走后门 seed + 走前门操作 |
| 产物 | Go 测试工程 | Playwright/Flutter integration_test 脚本 |

若功能既有 UI 又要测后端接口，UI 部分走 `dum-e2e-test`，纯接口部分可单独用本技能覆盖。

## 它交付什么

| | |
|---|---|
| 测试用例文档 | `docs/test-cases/<service>-api.md`（按 `assets/test-cases.md.tmpl`） |
| 接口测试工程 | `testcase/<service>-api-test/`（Go + goconvey，按 `assets/scaffold/` 落地） |

## 跨 agent 工具名

本技能正文使用 Claude Code 工具名（Read/Write/Edit/Bash/Grep/Glob），其它 agent 用等价工具替换即可，完整对照表见根 `CLAUDE.md`。

## 快速上手

1. 复制 `assets/scaffold/` 到 `testcase/<service>-api-test/`。
2. 填 `test.yml`：目标环境地址（只填测试/beta）、鉴权配置（敏感值占位，真实值放本地未纳入版本控制的文件）。
3. `./build.sh` 编译测试工程，确认可编译通过。
4. `./run.sh --list` 核对可选的模块/优先级/接口范围，再用 `./run.sh --module A --priority p0 --run` 之类的组合按需选跑。

## 跟其它技能怎么衔接

- 消费 `dum-solution-design` 产出的技术方案（`docs/tech-design/`）+ 需求文档 + 代码，作为接口契约的权威来源。
- 失败怀疑是代码 bug → 转 `superpowers:systematic-debugging`；怀疑是需求/方案与代码不一致 → 转 `dum-doc-reconcile`。
- 测试工程/用例文档改动落地后，用 `dum-session-summary` 把改动记进 `docs/modify_history/`。

## 完整工作流

四阶段详细步骤、核心原则、真实服务端护栏、命名约定与 `run.sh` 选择正则，详见 [`SKILL.md`](SKILL.md) 与 `references/` 下三份参考文档。
