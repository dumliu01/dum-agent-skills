---
name: dum-e2e-test
description: 为带后端的 Web、Electron、Flutter 客户端设计、补充、修改、审计并运行端到端/UI 自动化测试。适用于“做 E2E”“生成或补齐完整用例”“修改用例及脚本”“检查脚本是否跳步骤或漏断言”“多账号多设备联调”“检查真实覆盖率”“运行后定责”等请求。结合需求、技术方案、客户端和服务端代码覆盖模块主流程与基础功能；强制模块单一权威用例、逐步骤操作与预期、UI 前门、三层断言、步骤级覆盖审计、稳定定位、状态机式等待、资源生命周期、失败安全清理和证据定责。Web/Electron 使用 Playwright；Flutter 使用 integration_test，可运行于桌面、Android/iOS 模拟器或真机；原生 Android/iOS Appium 适配器仍未内建。
---

# dum-e2e-test

把 E2E 工作组织为可续接闭环：

```text
0 项目发现与可行性审计
→ 1 用例派生/修订
→ 2 覆盖编译与脚本生成
→ 3 环境预检与实测
→ 4 证据定责与修复提案
→ 5 覆盖回写与残留审计
```

始终先判断用户要做哪一种工作：

- `design`：从权威材料设计新用例。
- `extend`：补充遗漏用例或把部分覆盖补成完整 UI E2E。
- `modify`：修改已有用例及对应脚本。
- `audit`：检查覆盖、可行性、稳定性或文档/脚本漂移。
- `run`：运行已有脚本并定责。

不要在 `modify/extend/audit/run` 模式下从零重建已有体系。

## 0. 项目发现与可行性审计

在写用例或脚本前完成以下检查。

### 0.1 读取项目约定

按仓库实际情况识别：

- AGENTS/CLAUDE/架构/规范文档；
- 权威需求、技术设计、现有用例和冲突清单；
- 对应模块客户端页面、路由、状态层、Service/SDK，以及服务端接口、校验、状态机、定时任务和事件投递代码；
- 现有 E2E 目录、唯一入口、Runner、Robot/Page Object、Gateway、环境清单；
- 包管理与工具链锁定方式（FVM、pnpm、npm 等）；
- 可用设备、账号、服务和外部能力。

禁止默认所有项目都使用 `tests/e2e/`。优先复用仓库现有约定；只有项目没有 E2E 结构时才使用本技能模板。

### 0.2 权威阶梯

使用：

```text
需求 > 技术方案 > 当前代码 > 已有用例
```

- 每条期望记录 `provenance`。
- 高低层冲突按高层派生，并记录低层漂移。
- 需求与技术方案自身冲突时标记 `BLOCKED/escalate`，不私自裁决。
- 历史用例状态不是当前实现事实；对 `未实现/API-partial/BLOCKED` 必须重新扫描当前代码。

### 0.3 建立模块功能清单

- 以产品导航和领域所有权确定顶级模块及子模块；邮箱、日历各是一份权威用例，多日历、会议室属于日历子模块。
- 每个顶级模块只维护一份当前权威 Markdown；脚本仍可按子模块/业务域拆分并由统一 Runner 调度。
- 从需求、技术方案、客户端、服务端和历史问题提取功能清单。
- 自动化必须覆盖全部主流程和基础功能，不要求穷举所有低价值异常组合；未覆盖项必须明确 P2、MANUAL、EXTERNAL 或缺口理由。

设计、补充或修改用例时必须读取 [用例设计与逐步骤覆盖规范](references/case-design-and-step-coverage.md)。

### 0.4 建立可行性表

逐条回答：

| 维度 | 必查问题 |
|---|---|
| UI 前门 | 入口是否真实可达？操作是否忠实于业务意图？ |
| 定位 | 是否有稳定 role/testid/ValueKey/Semantics？是否重复、遮挡、需滚动、不可 hit-test？ |
| 数据预言机 | 是否能通过独立 API 读回？何时必须 DB 白盒？ |
| 资源 | 是 ephemeral、suite 还是 persistent？如何创建、核验、恢复、清理？ |
| 角色与能力 | 需要哪些 actor/account/device？实际 role/capability 是否可验证？ |
| 外部依赖 | hard、soft 还是 optional？缺失时 fail、skip 还是降级？ |
| 动态约束 | 时间、时区、忙闲、营业时间、权限、推送和刷新语义是否明确？ |

Flutter 任务必须读取 [Flutter E2E 稳定架构](references/flutter-e2e-stability.md)；完整覆盖或旧用例补齐任务必须读取 [覆盖与可行性](references/coverage-and-feasibility.md)。

## 1. 用例派生与修订

### 1.1 用例字段

使用项目现有格式并补足本技能的最低字段；无现有格式时复制 [测试用例模板](assets/test-case-template.md)。模块文件必须包含截图同等粒度的覆盖总览：

```text
域 / 用例数 / P0 / P1 / P2 / 主要运行层
UI+API / 部分覆盖 / 未实现或非自动化
```

每个子模块用例至少包含：

```text
ID、优先级、自动化状态和执行状态
provenance / 操作步骤
①交互与②展示预期 / ③数据预期
真实覆盖 / 证据或缺口
```

actor、capability、资源、刷新语义、时间窗口、清理和冲突编号按模块特性补充。

### 1.2 步骤与预期契约

- 操作步骤和预期使用相同编号，一步一预期；不得把多个业务阶段压成一句。
- 每一步明确 `actor + 页面/对象 + 真实 UI 动作 + 输入`，并写同编号的即时反馈、展示结果和必要数据状态。
- 多端用例逐步写 A/B，双方分别走 UI 前门；发起端成功不能替代接收端状态断言。
- 中间状态属于语义时必须断言；检查集合影响时检查目标、其它对象和母资源，不能抽查一条。
- 生成脚本前把每一步编译为 `actor + UI action + immediate assertion + display assertion + data oracle + cleanup`。

### 1.3 三层断言

数据变更场景必须校验：

1. 交互反馈：跳转、按钮态、Toast、弹窗状态。
2. UI 展示：列表、详情、计数、格式化值；Web 读 DOM，Flutter 读 widget/semantics。
3. 持久化：独立 API 黑盒优先，API 无法观测时才使用 DB 白盒。

API 正确不能替代 UI 断言。截图用于证据或视觉回归，不能替代结构化数值断言。详见 [三层校验与数据网关](references/oracle-and-data.md)。

### 1.4 UI 语义忠实

- Arrange 可走 API/DB 后门；被测 Act 必须走 UI 前门。
- “选择资源”必须打开真实选择器并验证持久化 ID，不能退化成填写名称。
- “加入/忽略/接受”等卡片场景必须执行按钮动作，不能停在“卡片可见”。
- 编辑场景至少覆盖标量变更、集合增加/删除/删最后一项、资源 A→B 替换，并断言 ID 不变。
- 展开型资源先核对主 ID、实例键、时间键，禁止猜字段名。
- 用例必须声明刷新语义：实时推送、自动轮询、重新进入、手动刷新或导航触发刷新。
- 不轻易判定功能不存在；先检查响应式导航、权限条件、懒构建、视口、客户端状态层、SDK 事件和服务端实现，并附代码证据。

### 1.5 动态时间、延迟与边界

- 默认在临近每个业务 Act 时构造可解释的未来时间窗；长套件不复用 suite 启动时计算的全局时间。
- Arrange 查询、UI 选择和 API 断言共用同一时钟基准。
- 普通、半小时槽、跨天/跨周、提醒/扫描等场景使用各自时间窗；跨午夜同步设置日期和时间。
- 邮件、scanner、push 等 1～3 分钟长延迟使用按业务 ID 的条件等待、独立超时和进度日志，禁止固定长 sleep 或 API 伪造被测事件。
- 时区场景分别断言 UTC instant、事件时区墙钟时间、设备时区展示。
- 至少使用两个 IANA 时区；不得假设开发机偏移或 `TZDateTime.toLocal()` 等于设备时区。

## 2. 覆盖编译与脚本生成

### 2.1 覆盖追踪闸门

从权威用例文档逐条反查脚本，禁止用测试函数数量推断覆盖率。每个 ID 必须分别记录自动化状态和执行状态：

```text
automation: UI+API | API-partial | implemented-unverified | MANUAL | BLOCKED | EXTERNAL | not-implemented
execution: passed | failed | skipped | not-run
```

区分三种事实：

- Markdown 用例是产品覆盖权威；
- 实际脚本声明是 Runner 执行事实；
- 日志、证据和退出码是本轮运行事实。

真实覆盖和证据/缺口应直接写回权威用例行，不另建平行覆盖矩阵或无人消费的手工 registry。详见 [覆盖与可行性](references/coverage-and-feasibility.md)。

逐 TC、逐 Step 反查脚本。每一步必须有 actor、真实 UI 动作、即时/展示断言和必要数据预言机；仅日志、注释、case 声明、Provider/Service/SDK 调用或最终状态断言不算完整。覆盖状态由最弱步骤决定，缺一步即为部分覆盖并记录步骤号。

### 2.2 复用项目架构

- Web/Electron：优先复用现有 Playwright config、fixture、Page Object。
- Flutter：优先复用现有唯一入口、Runner、Robot、Gateway、环境和协调器。
- 实际 `*_e2e` 文件应让执行元数据与动作同源；路径统一规范化。
- 范围选择至少支持项目已有的 module/file/case；选择 0 条必须失败并回显条件。
- 不保留新旧两套入口，不手工维护与用例重复的第三份目录。

### 2.3 稳定定位

- Web：role > testid > 可见文本；禁用绝对 XPath 和脆弱 CSS 链。
- Flutter：稳定实体 Key/ValueKey > Semantics > 文本。
- Flutter 还必须检查重复响应式实例、`hitTestable`、滚动/懒加载、遮挡层和点击后状态。
- Robot/Page Object 只封装业务动作，不封装用例期望。
- 缺测试钩子时一次性列出最小钩子清单；只加元数据可作为脚本前置提案，业务逻辑修改仍需用户确认。

### 2.4 产品代码改动账本

修改客户端前列出文件、改动类型、理由、功能/交互影响、权威依据和授权状态：

- `test-metadata`：Key/Semantics/testid，只做不改变布局、焦点和手势的最小改动；
- `fixture-boundary`：仅测试环境生效的夹具入口；
- `business-logic`：真实导航、状态、缓存或事件链变化，必须有产品/技术依据并获得用户明确授权。

不得让 Robot 绕过真实用户同样会遇到的视口/交互 Bug，也不得为了测试通过偷偷修改业务语义。

## 3. 环境预检与实测

### 3.1 Preflight

在昂贵构建前依次检查：

1. 项目 SDK 权威文件、实际 Flutter/Dart 与 `.dart_tool/package_config.json` 三者一致；使用项目 Runner/`--no-pub`，验证前后检查 lockfile；
2. 真实测试文件路径、唯一入口、选择范围及 TC 声明；
3. fixture 值满足生产代码参数校验、资源存在性、成员关系和用途，禁止按业务名称自行发明 ID；
4. Docker daemon、所需基础容器和镜像仓库；
5. hard dependency 业务服务健康；
6. 账号登录及实际 role/capability；
7. 设备存在、已 boot、可被工具精确识别；
8. workspace/build、Flutter startup lock、Xcode `build.db` 和设备/Bundle 租约；同一 workspace 只运行一个统一 E2E 命令；
9. 外部能力的 Secret 仅检查存在性，不回显值；
10. fixture verify；首次缺失才执行幂等 bootstrap；
11. 最终选择的用例数、文件、actor 和 capability 非空。

soft dependency 的 404/502 记录为旁路噪声，不直接判被测模块失败。

### 3.2 资源生命周期

| 类型 | 规则 |
|---|---|
| ephemeral | 每轮带 `runId/caseId` 命名；首个 Act 前注册 teardown；结束后残留审计 |
| suite | 套件内复用；套件结束统一清理 |
| persistent | 账号、普通群、组织级资源等；只 verify，必要变更先注册恢复，不默认删除 |

bootstrap 与 verify 分开且幂等。按稳定语义名称解析运行时 ID，不硬编码环境 ID。

### 3.3 多 Actor 与 Flutter

- 一个 Flutter `integration_test` 进程只控制一个设备/Widget 树。
- 多设备需要多个 Flutter 进程，但用户可只运行一个宿主命令。
- Flutter 可以在 macOS、Windows、Linux、Android/iOS 模拟器或真机运行；“iOS 原生 Appium 适配器未内建”不等于 Flutter+iOS 不支持。
- 多 Actor 场景使用 `runId/batchId/caseId/actor/stage` 事件协调；阶段不可互相覆盖；对端失败立即传播。
- A-only 场景是否仍启动 B 由项目 Runner 的批次复用策略决定，不在用例里硬编码。
- 宿主必须聚合所有进程退出码；单个进程的 `All tests passed` 不是批次结论。

### 3.4 等待与清理

- 使用条件等待和可观察屏障；固定 sleep 仅限短动画/消息泵送。
- build/install/login/ready/business/cleanup 可分别配置超时。
- teardown 中所有 Future、轮询、pump、client、stream、timer、microtask 必须 await/释放。
- 跨端删除会触发最终推送时，使用 requested→ready→completed→settled 清理屏障。
- ephemeral 数据在当前用例断言完成后通过真实 UI 删除并验证，teardown 再按精确 ID 兜底；suite/persistent 按声明的依赖顺序处理。
- 至少验证 clean run、dirty rerun 和失败后重跑；第一次添加与非第一次添加路径不同时均需处理。
- 测试结束后仍有异步异常，本轮不得判通过。

### 3.5 证据

失败至少保存：

- 截图；
- DOM 或 Widget/Semantics tree；
- 客户端结构化日志；
- API 请求/响应脱敏摘要；
- Runner 选择、actor 日志与协调事件；
- 构建/安装日志；
- 清理和残留审计结果。

## 4. 失败定责与提案

先读取 [定责决策树](references/triage-decision-tree.md)。

1. 保留第一条业务/断言失败；pending-frame、late network、dispose 异常是后续证据，不能覆盖首因。
2. 先判失败阶段：preflight/build/selection/launch/coordination/ui/display/persistence/cleanup/teardown。
3. `No tests ran`、选择为 0、文件未登记属于入口/选择脚本问题，不是业务失败。
4. 间歇失败先重跑；设备竞争、脏数据和环境缺失先归环境子类。
5. 脚本忠实且期望正确后，才判代码问题。
6. 持久化正确、UI 旧值通常是 `frontend` 或 `suspect-cache`；必须核对刷新语义，不能只延长等待。
7. 角色状态变化可能改变资源可读性；为每个角色选择正确数据预言机。
8. Finder 失败依次区分未构建、不可见、不可点击和权限/状态不渲染；稳定复现真实用户不可操作时判产品可用性问题，不能让脚本移动目标长期绕过。
9. 局部事件日志只能记录局部链路证据；只有全部步骤、所有 actor、三层断言和清理完成才能标记整条用例 passed。

报告使用 [测试报告模板](assets/test-report-template.md)。默认只输出修复提案；用户明确要求修改用例/脚本/代码时，才实施对应已确认范围。

## 5. 收尾闸门

- 从用例 ID 反向完成覆盖审计；
- 更新同一权威用例中的真实覆盖与证据/缺口；
- 校验 runId 临时数据残留为 0；
- 校验 persistent 资源恢复到基线；
- 校验所有 actor 退出码；
- 校验没有测试结束后的异步异常；
- 单文件通过后执行模块组合性审计，检查页面、弹窗、登录态、资源和协调 stage 是否泄漏；
- 对相关状态执行 clean/dirty rerun，确认首次与非首次路径均稳定；
- 报告未实跑、跳过、外部阻塞和真实通过，不把“脚本存在”写成“已通过”。

## 资源导航

- 模块用例结构、逐步骤写法和脚本覆盖：[references/case-design-and-step-coverage.md](references/case-design-and-step-coverage.md)
- 覆盖、状态与旧用例复核：[references/coverage-and-feasibility.md](references/coverage-and-feasibility.md)
- Flutter、多设备、定位和生命周期：[references/flutter-e2e-stability.md](references/flutter-e2e-stability.md)
- 三层断言、网关和资源清理：[references/oracle-and-data.md](references/oracle-and-data.md)
- 平台选择：[references/platform-adapters.md](references/platform-adapters.md)
- 失败定责：[references/triage-decision-tree.md](references/triage-decision-tree.md)
- 新项目模板：[assets/test-case-template.md](assets/test-case-template.md)、[assets/env-manifest-template.yaml](assets/env-manifest-template.yaml)、[assets/test-report-template.md](assets/test-report-template.md)
- 适配器参考骨架仅在项目没有现成基础设施时使用；不要覆盖成熟项目 Runner。
