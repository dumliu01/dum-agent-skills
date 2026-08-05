# Flutter E2E 稳定架构

## 目录

1. [项目优先](#一项目优先)
2. [进程、Actor 与设备](#二进程actor-与设备)
3. [事件协调](#三事件协调)
4. [Runner 预检](#四runner-预检)
5. [定位与手势](#五定位与手势)
6. [导航与组件状态机](#六导航与组件状态机)
7. [等待、刷新与时间边界](#七等待刷新与时间边界)
8. [资源、重跑与清理](#八资源重跑与清理)
9. [退出码和证据](#九退出码和证据)

## 一、项目优先

先识别仓库已有的：

- `integration_test/e2e` 或其他真实目录；
- 唯一入口和范围选择参数；
- FVM/Flutter 版本固定方式；
- Robot、Gateway、环境清单和 fixture；
- 多设备协调器、日志目录和证据格式。

成熟项目不应被通用骨架覆盖。技能附带的 Flutter skeleton 只用于没有基础设施的新项目。

## 二、进程、Actor 与设备

一个 Flutter `integration_test` 进程只能控制一个设备和一棵 Widget 树。双端协作必须使用两个进程：

```text
宿主 Runner
├── Actor A → Flutter process → macOS/Android/iOS
└── Actor B → Flutter process → macOS/Android/iOS
```

用户仍可只执行一个宿主命令。Runner 负责启动、协调和聚合两个进程。

推荐批次模型：

- 同一批次中 A/B 进程常驻，避免每条用例重复 build/install/login。
- A-only 用例中 B 可在批次屏障空闲等待。
- A+B 用例按 stage 协作。
- 仅在需要变更设备、Bundle、账号隔离或发生不可恢复故障时重启进程。

Flutter 应用可运行在 iOS 模拟器或真机；这与“技能没有原生 iOS Appium 适配器”是两个概念。

## 三、事件协调

不要用一份“最新状态 JSON”互相覆盖。协调事件至少包含：

```text
runId / batchId / caseId / actor / stage
status / sequence / timestamp / payload
```

规则：

- 事件追加或按复合键存储，不能由不同 stage 覆盖。
- 等待条件必须同时匹配 runId、caseId、actor、stage。
- 一端失败立即发布 failure，另一端解除等待并失败。
- 超时时输出最近事件、缺少的事件和当前 actor 状态。
- 旧 runId 事件不得满足当前等待。
- payload 只传必要 ID，不携带 Secret。

最终清理会向对端产生推送时，使用：

```text
cleanup_requested
→ peer_ready
→ cleanup_completed
→ peer_settled
```

## 四、Runner 预检

昂贵构建前按顺序执行：

1. 读取 `.fvmrc` 或项目 SDK 权威，比较实际 Flutter/Dart 和 `.dart_tool/package_config.json` 生成版本；任一不一致立即失败。
2. 复用项目 Runner 和依赖状态；依赖已就绪时使用 `--no-pub`，验证前后检查 `pubspec.lock`，不能由 analyze/test 静默改写依赖图。
3. 校验真实测试文件、唯一入口和 TC 声明。
4. 校验 workspace/build 单实例租约、Flutter startup lock、Xcode `build.db` 和残留 `flutter test/xcodebuild`；语言服务器和 daemon 不等于正在构建。
5. 校验 Docker daemon，再校验 hard dependency 服务。
6. 解析并规范化 module/file/case 选择；选择为 0 立即失败。
7. 校验 actor 账号实际 role/capability。
8. 校验设备存在、已 boot、设备 ID 精确匹配并获取设备/Bundle 租约。
9. 把 fixture 值代入生产构造函数、Service 和服务端校验，检查 ID 格式、资源存在性、成员关系和用途，禁止根据业务名称猜 ID。
10. 检查外部 Secret 仅返回 present/missing。
11. verify persistent fixture；缺失时才幂等 bootstrap。
12. 输出最终计划、用例数、actor/device、构建租约和分阶段超时预算。

Docker daemon 可用不等于业务服务健康。soft dependency 的 404/502 需单独标记，不覆盖首个业务失败。

## 五、定位与手势

### Finder 优先级

```text
稳定实体 ValueKey/Key
> Semantics label/action
> 稳定文本
```

每个 Finder 都要检查：

- 响应式布局是否产生重复实例；
- `evaluate().length` 是否符合预期；
- 是否存在 `hitTestable` 实例；
- 是否需要 `ensureVisible` 或滚动；
- 是否被 dialog、drawer、loading、tooltip 遮挡；
- 点击后的页面状态是否真正变化。

不要在不加约束时直接 `find.text(...).first`。

Finder 失败时按顺序诊断：

1. 数据是否存在；
2. Widget 是否因懒构建尚未进入树；
3. Widget 是否已构建但在屏外；
4. 是否可见但被遮挡或不命中 hit-test；
5. 当前角色/状态是否根本不渲染它。

不得把这五种状态合并为“功能未实现”。懒加载列表先识别正确 Scrollable，从稳定起点有界滚动或 `scrollUntilVisible`，再 `ensureVisible` 并检查 `hitTestable`。

### 画布和手势

对 `Stack`、时间网格、画布类交互做 gesture preflight：

1. 识别可点击区域边界和滚动偏移。
2. 区分“点击已有项”和“点击空白区域”。
3. 证明两种命中条件互斥。
4. 手势后先断言目标弹层/详情出现，再继续。

### 异步表单

`enterText` 后不要立即点击旧按钮状态：

1. pump/条件等待 `onChanged` 引起的 rebuild；
2. 读回 controller/EditableText 值；
3. 检查按钮 callback 已启用；
4. 只点击 `hitTestable` 的当前按钮；
5. 等待表单关闭或业务状态改变。

### MouseRegion 与异步子菜单

- 使用 `TestGesture(kind: PointerDeviceKind.mouse)`，从菜单外移动到当前节点中心触发真实 `onEnter`。
- 异步加载替换节点后重新执行 Finder，不能复用旧 RenderObject 或同坐标 hover。
- 通过子菜单稳定 Key 的 `hitTestable` 实例证明展开。
- 操作期间保持 pointer 存活，并在 `finally` 释放。
- 在窗口四角和小窗口检查主菜单 clamp、子菜单左右翻转/向上平移及内容内部滚动。
- 将目标滚到中间只能用于诊断；若真实用户路径稳定越界，修复产品并保留回归测试。

### 等待

优先：

- 等 Finder 状态；
- 等 API/协调事件；
- 等语义属性或 loading 消失；
- 有界轮询并输出最后状态。

`pumpAndSettle` 只适用于确定会稳定的局部动画；持续 timer/stream 页面可能永不 settle。固定 sleep 仅用于短动画或消息泵送，不能解决缓存和刷新语义错误。

## 六、导航与组件状态机

### Navigator context

通过代码入口 push 页面时，从确认位于 Navigator 子树中的真实业务 Widget 获取 context；禁止从 `MaterialApp` 或任意顶层 context 直接调用 `Navigator.of`。push 前验证 widget 已挂载，push 后等待目标页面 ready Key。

### 响应式导航

把导航写成页面状态机：

1. 若目标列表/页面已存在，直接继续；
2. 若移动端位于嵌套详情且有稳定返回按钮，先返回；
3. 仅在既不在目标页面也不可返回时切一级模块；
4. 等待列表 ready，揭示目标并点击；
5. 断言 active ID/路由/详情对象正确。

不能把桌面分栏假设直接套到移动端 push 页面。

### 搜索、筛选和多选

每个查询/选择循环写成小状态机：

```text
clear → assert empty → input → assert query
→ wait result → tap result → assert selected
```

- 搜索框、清除按钮、候选项、已选项使用不同稳定 Key。
- 连续搜索时等待上一次异步查询和选中区刷新。
- 真实 IME 清除后若 TextInputClient 抖动，基于当前活动 `EditableTextState` 注入值，并继续读回验证；不得只打印“已输入”。
- 每选择一个对象立即断言已选区恰好出现一次，再处理下一个。

## 七、等待、刷新与时间边界

用例必须声明列表/详情如何看到更新：

- 实时推送；
- 自动轮询；
- 重新进入；
- 手动刷新；
- 导航触发刷新。

若 API 已是新值、UI 仍是旧值，先验证刷新语义和缓存失效，不要先延长等待。

动态时间由统一 Clock 在每个业务步骤临近 Act 时构造未来窗口，并贯穿：

- Arrange 请求；
- UI 控件输入；
- API 读回断言；
- 多 actor 协调 payload。

长套件不能在 suite 开头只算一个 `future`。按业务类型分别提供普通未来窗口、半小时槽、跨天/跨周窗口和提醒/扫描窗口。跨午夜时同步设置开始/结束日期；周六跨天后需要真实切换下一周检查结束日片段。

邮件、服务端 scanner、ZIM/push 等长延迟事件：

- 按 messageId/eventId/resourceId 条件等待；
- 使用独立的外部事件超时和周期性进度日志；
- 超时输出最后一次服务/API/UI 状态；
- 不固定 sleep 60/90/120 秒，不直接调用 scanner 或 API 插入结果绕过被测链路。

时区测试分别比较：

1. 后端 UTC instant；
2. 事件 IANA 时区的墙钟时间；
3. 设备 IANA 时区的 UI 展示。

至少测试两个 IANA 时区和跨日边界。不要把开发机 `DateTime.toLocal()` 当成设备时区预言机。

## 八、资源、重跑与清理

所有临时名称包含 `runId/caseId`，所有创建接口返回的 ID 立即登记。第一个业务 Act 前注册 teardown，保证中途失败也能清理。

| 生命周期 | 行为 |
|---|---|
| ephemeral | 创建后登记；按精确 ID 删除；runId 残留审计 |
| suite | 批次内复用；批次结束统一删除 |
| persistent | verify；需要修改时先登记恢复快照；禁止默认删除 |

ephemeral 资源在当前用例断言完成后优先通过真实 UI 删除，验证删除交互、UI 消失和 API 不再召回；teardown 只按登记的精确 ID/当前 runId 兜底，禁止模糊标题批量删除。suite 资源明确创建、使用和最终删除顺序。

至少验证：

- clean run：首次添加/空状态路径；
- dirty rerun：已有标签、已有数据、非首次入口路径；
- failure rerun：中途失败后的资源、页面和协调状态可恢复；
- file → module：单文件通过后按真实顺序串跑，检查弹窗、Tab、选中日期、登录态和 stage 泄漏。

展开型日程或实例资源不可猜 `instanceDate`。先通过契约或响应确定主 ID、实例键、时间键，再执行查询和清理。

teardown 要求：

- 所有 Future/轮询/pump 都 `await`；
- 取消 Timer、Stream subscription 和未完成 request；
- client 在最后一个请求完成后再关闭；
- widget dispose 后不再调度新工作；
- cleanup 失败和残留非零会使本轮失败；
- 测试结束后捕获到的异步异常不得降级为 warning。

## 九、退出码和证据

宿主 Runner 必须聚合：

- A/B 各进程退出码；
- build/install/launch 状态；
- 协调器失败；
- cleanup/residual audit；
- 测试结束后的异步错误。

单个 actor 打印 `All tests passed` 不代表批次通过。

失败证据至少包括：

- actor 独立日志；
- 最近协调事件；
- 截图和 Widget/Semantics tree；
- 脱敏 API 摘要；
- build/install 日志；
- 清理登记、恢复结果和 runId 残留审计。

首个业务失败必须单独保留。pending frame、late Dio、dispose error 等后续异常作为附加证据，不得覆盖首因。

Runner 日志同时保留：

```text
batch → runnable case/sourceFile → document TC/Step → actor/stage
```

`A=1, B=143` 时先读最早失败 actor；143 通常是 peer-terminated/secondary。启动期其它模块离线通知和 soft dependency 日志单列为旁路事件。静态/Widget 测试或局部 SDK 回调只算局部证据，不能替代完整双端 E2E 结论。
