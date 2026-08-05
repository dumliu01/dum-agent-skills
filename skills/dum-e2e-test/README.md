# dum-e2e-test

`dum-e2e-test` 用于为带后端的 Web、Electron、Flutter 客户端设计、补充、修改、审计并运行端到端/UI 自动化测试。

> 本 README 面向维护者快速阅读；技能执行规则以 [`SKILL.md`](SKILL.md) 为准。

## 工作闭环

```text
项目发现与可行性审计
→ 用例派生或修订
→ 覆盖编译与脚本生成
→ 环境预检与实测
→ 证据定责与修复提案
→ 覆盖回写与残留审计
```

技能优先复用项目已有的 E2E 目录、Runner、Robot/Page Object、Gateway、环境清单和工具链约定，不默认使用固定目录，也不会在修改或补充任务中从零重建已有体系。

## 用例设计目标

- 结合需求、技术方案、客户端和服务端代码，覆盖顶级模块的全部主流程与基础功能。
- 每个顶级模块只维护一份当前权威用例文件；子模块在文件内分节，自动化脚本可以按业务域拆分。
- 覆盖总览记录域、用例数、P0/P1/P2、主要运行层、UI+API、部分覆盖和未实现/非自动化。
- 每条用例按相同编号写操作步骤和预期；多端步骤明确 A/B，不能省略中间动作和断言。
- 每个步骤编译为 actor、真实 UI 动作、即时断言、展示断言、数据预言机和清理；最弱步骤决定覆盖状态。

## 核心规范

### 权威顺序

```text
需求 > 技术方案 > 当前代码 > 已有用例
```

每条期望记录来源；权威材料自身冲突时标记阻塞并请求裁决。

### 三层校验

含数据变更的用例必须同时断言：

| 层 | 校验内容 |
|---|---|
| 交互反馈 | 跳转、按钮状态、Toast、弹窗状态 |
| UI 展示 | 列表、详情、计数、格式化值 |
| 持久化 | 独立 API 黑盒优先，必要时 DB 白盒 |

Arrange 可以使用 API/DB 后门，被测 Act 必须通过真实 UI 前门。截图是证据或视觉回归手段，不能替代结构化数据断言。

### 三段定责

稳定失败按以下语义定责：

| verdict | 含义 |
|---|---|
| `script` | Runner、定位、步骤、等待、断言或网关编码错误 |
| `test-case` | 用例期望与更高权威不一致 |
| `code` | 应用行为违背权威期望 |
| `flaky` | 间歇失败、设备竞争、脏数据或环境波动 |
| `escalate` | 权威材料自身冲突，需要用户裁决 |

`code` 进一步区分 `frontend / backend / suspect-cache`。报告同时记录 `failure_phase`、首个失败和后续次生错误，避免 pending-frame、late network 或 dispose 异常覆盖首因。

## 稳定性约束

- 用例文档、脚本声明和运行证据是三类不同事实，不用测试函数数量推断覆盖率。
- 自动化状态和执行状态分开；脚本存在不等于测试通过。
- 选择结果为 0 或 `No tests ran` 属于 Runner/selection 失败。
- 临时资源使用 `runId/caseId` 命名并按精确 ID 清理。
- persistent 资源只核验或恢复，不默认删除。
- 用例明确刷新语义，避免用固定等待掩盖缓存问题。
- 时间数据使用统一 Clock 和未来窗口；时区分别校验 UTC、事件墙钟和设备展示。
- Flutter Finder 需要检查重复实例、hit-test、滚动、遮挡和点击后状态。
- 所有异步 teardown 都要完成；测试结束后的异步异常仍使本轮失败。
- fixture 必须满足生产代码的 ID、存在性、成员关系和用途约束，不能自行猜测环境 ID。
- Flutter 运行前比较项目 SDK、实际 SDK 和 package_config，使用项目 Runner/`--no-pub` 并保护 lockfile。
- clean run、dirty rerun、失败后重跑和模块串跑分别验证，覆盖第一次与非第一次添加路径。
- 异步表单、搜索、多选、MouseRegion 子菜单、懒加载列表和响应式导航按状态机操作。
- 邮件、scanner、push 等长延迟结果按业务 ID 条件等待，不使用固定 1～2 分钟 sleep。
- 跨天、跨周、提醒等场景使用独立的逐步骤动态时间窗。

为可测性修改客户端时先输出改动账本。Key/Semantics/testid 只能做不改变功能和交互的最小修改；真实业务逻辑变化必须提供产品/技术依据并获得明确授权。

## Flutter 与多 Actor

Flutter 使用 `integration_test`，可运行在桌面、Android/iOS 模拟器或真机。

一个 Flutter 测试进程只能控制一个设备和一棵 Widget 树。双端协作使用多个 Flutter 进程，由一个宿主 Runner 启动和聚合，并通过以下复合键协调：

```text
runId / batchId / caseId / actor / stage
```

原生 Android/iOS Appium 适配器仍未内建；这不影响 Flutter 应用在 Android/iOS 设备上运行。

## 目录

| 路径 | 用途 |
|---|---|
| [`SKILL.md`](SKILL.md) | 技能主流程和强制规则 |
| [`references/case-design-and-step-coverage.md`](references/case-design-and-step-coverage.md) | 模块结构、逐步骤用例和脚本覆盖规范 |
| [`references/coverage-and-feasibility.md`](references/coverage-and-feasibility.md) | 覆盖追踪、状态定义和旧用例复核 |
| [`references/flutter-e2e-stability.md`](references/flutter-e2e-stability.md) | Flutter、多设备、定位、等待和清理 |
| [`references/oracle-and-data.md`](references/oracle-and-data.md) | 三层预言机和数据网关 |
| [`references/triage-decision-tree.md`](references/triage-decision-tree.md) | 三段定责决策树 |
| [`references/platform-adapters.md`](references/platform-adapters.md) | 各端适配映射 |
| [`assets/test-case-template.md`](assets/test-case-template.md) | 用例模板 |
| [`assets/env-manifest-template.yaml`](assets/env-manifest-template.yaml) | 环境清单模板 |
| [`assets/test-report-template.md`](assets/test-report-template.md) | 报告模板 |

适配器骨架只用于没有现成 E2E 基础设施的新项目，不应覆盖成熟项目的 Runner。
