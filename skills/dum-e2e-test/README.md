# dum-e2e-test

> 把「带后端的前端/客户端」端到端测试做成**四阶段闭环流水线**：用例派生 → 脚本生成 → agent 实测 → 三段定责 + 修复提案。全程**仅出方案**，实际改动须用户确认后再执行。

## 它做什么

端到端测试往往有三个难点：用例来源不清（哪层文档为准？）、断言不全（只验交互、漏了数据）、失败后不知道该改脚本还是改代码。本技能用**权威阶梯 + 三层校验 + 三段定责**把这三个难点都纳入流程：

**四阶段**：

| 阶段 | 做什么 | 产物落点 |
|---|---|---|
| ① 用例派生 | 按权威阶梯（需求 > 技术方案 > 代码 > 用例）读入文档，派生带溯源的用例；两层权威矛盾时记冲突、不私自裁决 | `docs/test-cases/<feature>.md` |
| ② 脚本生成 | 将确认后的用例翻译成可运行 Playwright 脚本，按三层断言编写，走后门 seed 前置数据 | `tests/e2e/<feature>/` |
| ③ agent 实测 | 起干净环境、跑脚本、收证据包（截图/DOM 快照/日志/trace）、去抖判 flaky | `tests/e2e/.artifacts/<run>/` |
| ④ 三段定责 + 提案 | 依证据按决策树定责，出文字修复方案，等用户确认后再改 | `docs/test-report/YYYYMMDD-<feature>.md` |

**三层校验**（每条含数据变更的用例必须同时断言）：

| 层 | 校验内容 | 意义 |
|---|---|---|
| ① 交互反馈 | toast / 跳转 / 按钮态 / 弹窗关闭 | 确认操作有无被响应 |
| ② 界面数据展示 | 列表/详情/计数器/格式化值在 DOM 中是否正确渲染（默认 `source=dom`） | 确认前端正确显示 |
| ③ 持久化状态 | 操作后后端/DB 中实际存的值（API 黑盒优先，DB 白盒兜底） | 确认数据真正写入 |

**三段定责**（失败时互斥可判）：

| 定责结论 | 含义 | 分层 |
|---|---|---|
| `script` | 脚本定位/步骤/断言编写错误 | — |
| `test-case` | 用例期望与权威文档不符 | — |
| `code` | 应用行为违背权威期望 | `frontend`（渲染 bug）/ `backend`（持久化 bug）/ `suspect-cache`（乐观更新掩盖持久化错误） |
| `flaky` | 去抖重跑后间歇失败，先排查等待策略/竞态/数据隔离 | — |
| `escalate` | 两层权威本身矛盾，停止定责，转交用户或 `dum-doc-reconcile` | — |

## 何时触发

- ✅ "给登录/订单/…功能做端到端测试"
- ✅ "写 UI 自动化" / "跑 e2e"
- ✅ "验证前端金额展示与后端是否一致"
- ✅ "验证订单创建后数据库是否正确写入"
- ✅ "我改了状态机逻辑，想用用例跑一遍确认"
- ✅ 需要同时产生用例文档 + 脚本 + 报告（而不只是手写脚本）
- ❌ 遇到 bug 需先定位根因 → 先用 `superpowers:systematic-debugging`（本技能定责只出方案，不做 debug）
- ❌ 纯单元测试 / 无 UI 的接口测试 → 直接写 unit/integration test，无需本技能
- ❌ 一次性脚本，不需要用例文档 → 直接写 Playwright 脚本手跑
- ❌ 移动端（Flutter/Android/iOS）——v1 未支持，占位适配器会抛 `not-implemented`

## 它交付什么

| 产物 | 落点 | 格式 |
|---|---|---|
| 测试用例 | `docs/test-cases/<feature>.md` | Markdown，按 `assets/test-case-template.md` 结构 |
| e2e 脚本 | `tests/e2e/<feature>/` | TypeScript（Playwright spec），参考 `assets/playwright-adapter-skeleton.ts` |
| 证据包 | `tests/e2e/.artifacts/<run>/TC-<feature>-<序号>/` | 截图 + DOM 快照 + console.log + network.json + trace.zip |
| 测试报告 | `docs/test-report/YYYYMMDD-<feature>.md` | Markdown，按 `assets/test-report-template.md` 结构，含定责字段与修复提案 |
| 环境清单 | 项目根 或 `docs/test-cases/` 同级 | YAML，按 `assets/env-manifest-template.yaml` 结构 |

## 跟其它技能怎么衔接

- **`webapp-testing`**：阶段 ③ 实测时复用——`webapp-testing` 提供真实 Playwright/Electron 执行能力，本技能在其上加用例派生 + 三段定责方法论。
- **[`dum-solution-design`](../dum-solution-design/)**：技术方案是权威阶梯第二层，`docs/tech-design/` 是用例期望的主要来源；通常先出方案，实现后再用本技能做 e2e 验收。
- **[`dum-doc-reconcile`](../dum-doc-reconcile/)**：`verdict=escalate`（两层权威互相矛盾）时转交——对账后更新权威文档，再重新派生受影响用例。
- **[`dum-session-summary`](../dum-session-summary/)**：用例/脚本/代码修复落地后，用本技能记录本次会话改动到 `docs/modify_history/`，方便下次续接。

## 完整工作流

四阶段详细步骤（权威阶梯裁决、脚本三层断言编写、去抖与证据收集、定责决策树与展示×持久化交叉表）、核心原则（仅出方案、走后门 seed、DOM 优先）、常见错误与 Red Flags，详见 [`SKILL.md`](SKILL.md)。

## 资源

**references/**（方法论文档）：

- `references/triage-decision-tree.md` — 三段定责决策树：稳定性闸 → 环境类闸 → 语义定责 → 展示×持久化交叉表定 layer
- `references/oracle-and-data.md` — 三层校验预言机实现：Arrange 走后门 / Act 走前门、展示值 DOM 提取规则、持久化网关接口
- `references/platform-adapters.md` — 统一驱动契约与平台适配器登记（Web/Electron 已实现，Flutter/Android/iOS 占位）

**assets/**（可用模板）：

- `assets/test-case-template.md` — 用例文件模板（`TC-<feature>-<序号>` 结构，含 provenance / 三层 expected 字段）
- `assets/test-report-template.md` — 测试报告模板（顶部汇总 + 每条定责字段 + proposal）
- `assets/playwright-adapter-skeleton.ts` — Playwright 适配器骨架（按统一驱动契约：launch / locate / act / readDisplay / assert / collectEvidence / teardown）
- `assets/env-manifest-template.yaml` — 环境清单模板（bring_up / test_db / seed / reset_hook / mocks / isolation 档位）

---

> **v1 平台范围**：Web 与 Electron 已做实（Playwright 驱动）；Flutter / Android / iOS 以统一驱动契约占位，v1 不可执行，运行会抛 `not-implemented`。
