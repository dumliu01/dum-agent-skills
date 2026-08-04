# <模块> E2E 测试报告

## 结论

- 总体：PASS / FAIL / PARTIAL / BLOCKED / NOT-RUN
- runId：`<run-id>`
- 选择范围：`<module/file/case>`
- 命中用例：`<数量和 ID>`
- 通过/失败/跳过/未运行：`x/x/x/x`
- 残留审计：`0` / `<数量>`
- persistent 恢复：成功 / 失败 / 不适用

> 选择为 0 或出现 `No tests ran` 时，总体必须是 FAIL，失败阶段为 `selection`，不能报告业务通过。

## 环境与预检

| 项目 | 结果 | 证据 |
|---|---|---|
| 工具链和真实路径 | PASS/FAIL | <版本、入口> |
| SDK authority/actual/package_config | PASS/FAIL | <三者版本> |
| lockfile 副作用 | PASS/FAIL | <验证前后 diff> |
| workspace/build 租约 | PASS/FAIL | <startup lock/build.db/进程> |
| Docker daemon | PASS/FAIL/N/A | <摘要> |
| hard dependencies | PASS/FAIL | <健康检查> |
| soft dependencies | PASS/WARN | <旁路噪声> |
| 账号 role/capability | PASS/FAIL | <脱敏摘要> |
| 设备与租约 | PASS/FAIL | <设备 ID> |
| Secret 存在性 | PASS/FAIL/N/A | 只写 present/missing |
| fixture verify/bootstrap | PASS/FAIL | <摘要> |
| fixture 生产约束 | PASS/FAIL | <ID 格式/存在性/成员/用途> |
| 选择非空 | PASS/FAIL | <文件、用例 ID> |

## Actor 与进程

| Actor | 设备 | 用例 | 退出码 | 结果 | 日志 |
|---|---|---|---:|---|---|
| A | <设备> | <ID> | 0 | PASS | <链接> |
| B | <设备或 N/A> | <ID> | 0 | PASS/N/A | <链接> |

聚合退出码：`<code>`。单个 Actor 的 `All tests passed` 不代表批次通过。

## 用例结果

| ID | 自动化状态 | 执行状态 | 三层断言 | 证据或缺口 |
|---|---|---|---|---|
| MOD-001 | UI+API | passed | 交互/UI/API | <截图、树、API 摘要> |

## 逐步骤覆盖

| TC | Step | Actor | UI action | 即时断言 | 展示断言 | 数据 oracle | 清理 | 结果/缺口 |
|---|---:|---|---|---|---|---|---|---|
| MOD-001 | 1 | A | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL/N/A | PASS/FAIL | <证据或缺口> |

任一步缺动作、缺必要断言或由错误 actor 代做，整条用例只能标记部分覆盖，不能写 `UI+API/passed`。

## 失败定责

### <用例 ID>

- 首个失败：`<原始错误和时间>`
- failure_phase：`preflight/build/selection/launch/coordination/ui/display/persistence/cleanup/teardown`
- verdict：`script/test-case/code/flaky/escalate`
- subtype：`runner/finder/gesture/frontend/backend/suspect-cache/environment/contract/...`
- 复现次数：`x/y`
- 预期依据：`<provenance>`
- 实际证据：`<截图/UI tree/API 摘要/日志>`
- 后续噪声：`<pending-frame/late network/dispose；不得覆盖首因>`
- peer 次生退出：`<actor/exit code，例如 143；或无>`
- 局部链路证据：`<已观察到但不足以证明整条 case 通过的事件>`
- 结论：`<为什么归到该层>`

## 三层断言

| ID | 交互反馈 | UI 展示 | 持久化 | 刷新语义 |
|---|---|---|---|---|
| MOD-001 | PASS/FAIL | PASS/FAIL | PASS/FAIL | 推送/轮询/重进/刷新 |

若持久化为新值但 UI 为旧值，记录实际刷新语义和缓存证据，不用任意延长等待掩盖问题。

## 资源与清理

| 资源 | 生命周期 | 创建/解析 ID | 清理或恢复 | 残留 |
|---|---|---|---|---:|
| <资源> | ephemeral | <ID> | PASS/FAIL | 0 |
| <资源> | persistent | <ID> | restored/unchanged | 0 |

## 稳定性复跑

| 模式 | 结果 | 说明 |
|---|---|---|
| clean run | PASS/FAIL/NOT-RUN | 首次添加/空状态 |
| dirty rerun | PASS/FAIL/NOT-RUN | 非首次添加/已有数据 |
| failure rerun | PASS/FAIL/NOT-RUN | 中途失败后的恢复 |
| module composition | PASS/FAIL/NOT-RUN | 单文件后模块串跑 |

## 产品代码改动账本

| 文件 | 类型 | 理由 | 功能/交互影响 | 权威依据 | 授权状态 |
|---|---|---|---|---|---|
| <file> | test-metadata/fixture-boundary/business-logic | <原因> | 无/具体影响 | <文档> | approved/pending |

## 证据索引

- 截图：<路径>
- DOM/Widget/Semantics tree：<路径>
- 客户端日志：<路径>
- API 脱敏摘要：<路径>
- Actor 日志与协调事件：<路径>
- 构建/安装日志：<路径>
- cleanup/residual audit：<路径>

## 修复提案

| 优先级 | 归属 | 建议 | 影响范围 | 验证方式 |
|---|---|---|---|---|
| P0 | script/test-case/frontend/backend/environment | <方案> | <范围> | <回归用例> |

默认仅提供提案；只有用户明确要求修改时才实施授权范围内的变更。

## 覆盖回写

- 已把真实自动化状态和运行证据写回权威用例：是/否
- 未运行、跳过、MANUAL、BLOCKED、EXTERNAL 均已如实标记：是/否
- 未使用测试函数数量冒充覆盖率：是/否
