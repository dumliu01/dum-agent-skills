# <顶级模块> 完整 E2E 测试用例

> 权威来源：<需求、技术方案、客户端/服务端代码链接>
> 一个顶级模块只维护这一份当前权威用例；脚本可按子模块分文件。

## 1. 覆盖总览

| 域 | 用例数 | P0 | P1 | P2 | 主要运行层 | UI+API | 部分覆盖 | 未实现/非自动化 |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| SUB 子模块名称 | 0 | 0 | 0 | 0 | local | 0 | 0 | 0 |
| 合计 | 0 | 0 | 0 | 0 | — | 0 | 0 | 0 |

- 完整覆盖率：`UI+API / 用例数`
- 脚本触达率：`(UI+API + 部分覆盖) / 用例数`
- 自动化状态：`UI+API / API-partial / implemented-unverified / MANUAL / BLOCKED / EXTERNAL / not-implemented`
- 执行状态：`passed / failed / skipped / not-run`

## 2. 功能清单与覆盖取舍

| 子模块 | 主流程/基础功能 | 已覆盖 TC | 未自动化项及理由 |
|---|---|---|---|
| SUB | <创建、查看、编辑、删除等> | <ID> | <MANUAL/EXTERNAL/P2> |

## 3. 冲突与环境约束

| 编号 | 冲突/约束 | 权威依据 | 处理状态 |
|---|---|---|---|
| C-01 | <无或具体内容> | <文档/代码> | resolved/BLOCKED |

## 4. SUB｜<子模块名称>

| ID / 优先级 / 状态 | provenance | 操作步骤 | ①交互与②展示预期 | ③数据预期 | 真实覆盖 | 证据 / 缺口 |
|---|---|---|---|---|---|---|
| TC-MOD-SUB-001<br>P0 / not-implemented / not-run | 产品：<章节><br>技术：<章节><br>代码：<文件/符号> | 1. [A] <真实 UI 动作><br>2. [B] <真实 UI 动作或 A 后续检查> | 1. <与步骤 1 同编号的反馈和展示><br>2. <与步骤 2 同编号的反馈和展示> | 1. <步骤 1 后的数据状态><br>2. <步骤 2 后的数据状态> | not-implemented | 缺 Step 1/2 脚本；或 `<source_file>` + runId |

### TC-MOD-SUB-001 补充约束

| 字段 | 内容 |
|---|---|
| actors / capabilities | A；或 A+B；<角色/权限> |
| preconditions | <页面、账号、服务、既有状态> |
| resources | `<名称>: ephemeral/suite/persistent` |
| refresh_semantics | 推送/轮询/重进/手动刷新/导航 |
| time_window | 即时/每步骤动态未来时间/跨天跨周/长延迟事件 |
| cleanup | <成功路径 UI 删除；失败路径精确 ID 兜底；恢复项> |
| source_file | <真实脚本路径> |

### 逐步骤脚本映射

| TC | Step | Actor | UI action | 即时断言 | 展示断言 | 数据 oracle | 清理 | 代码位置 |
|---|---:|---|---|---|---|---|---|---|
| TC-MOD-SUB-001 | 1 | A | <Robot/Page Object 方法> | <断言> | <断言> | <API/DB> | <登记> | <file:line/symbol> |

## 编辑类最小矩阵

| 变更类型 | 覆盖项 | ID 约束 |
|---|---|---|
| 标量 | 旧值 → 新值 | 主 ID 不变 |
| 集合 | 增加、删除、删除最后一项 | 主 ID 不变 |
| 资源引用 | A → B | 主 ID 不变、引用 ID 改变 |

## 多 Actor 补充

- 每一步明确 actor，A/B 分别走真实 UI 前门。
- 中间状态与最终状态分别断言，不能只由发起端自证。
- 协调键使用 `runId/batchId/caseId/actor/stage`。
- 记录所有 actor 的退出码；任一端失败均不得写 `passed`。
