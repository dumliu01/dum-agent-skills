# 各端适配映射 Reference

> 本文件是 `dum-e2e-test` 的多端驱动层参考，供 `assets/playwright-adapter-skeleton.ts`（Web/Electron）与 `assets/flutter-adapter-skeleton.dart`（Flutter）按此实现，并供 SKILL.md 脚本生成器选择适配器时查阅。
> 正文中文；不含实现代码——只有签名/表格/契约描述。

---

## 1. 统一驱动契约

> 主流程只对此契约编程；换端 = 换适配器（来自方案 §3.5）。

所有平台适配器须实现以下 8 个签名：

```
launch(target) -> session
```
起/连被测应用。`target` 可为 web URL、Electron 二进制路径、或移动端设备+应用包描述符。返回 `session` 供后续调用使用。

```
locate(query) -> handle
```
语义定位元素。优先按可访问角色 / 可见文本 / `testid` 定位（各端 testid 类比见 §2），禁用脆性 CSS 路径或绝对 XPath。

```
act(handle, action)
```
对定位到的元素执行操作。`action` 包含 click / fill / scroll / key 等语义动作。

```
observe() -> snapshot
```
获取当前 DOM/widget 树快照 + 截图。展示预言机**默认读树（结构化提取）**断言数据值；截图供取证与可选视觉回归/OCR 兜底（方案 §3.11）。

```
readDisplay(locator) -> string
```
从树语义提取某处呈现的文本或值，供展示预言机（②）主用。各端提取方式见 §2「展示取值」列。

```
assert(handle | snapshot, expectation)
```
对元素句柄或快照内容进行断言，支持相等、正则、可见性等期望形式。

```
collectEvidence() -> bundle
```
收集证据包：截图 + 树快照 + 控制台日志 + 网络请求日志 + trace 文件。失败时必须调用，供三段定责取证。

```
teardown(session)
```
清理会话，包含关闭浏览器/应用进程与触发测试数据回滚。

---

## 2. 各端适配映射表

> 来自方案 §4.5。主流程（用例派生 / 三层校验 / 三段定责 / 数据网关 / 环境清单）全端共用；本表只列「怎么点、怎么读屏、怎么起」这层的差异。数据层（seed/API/DB 断言）各端一致。

| 端 | 驱动 | 定位（testid 类比） | 展示取值（§3.11） | 起测/环境 | v1 状态 |
|---|---|---|---|---|---|
| Web | Playwright | role / text / `data-testid` | DOM 提取（`textContent` / `inputValue` / ARIA 文本） | 起前后端 / 连 URL | **实** |
| Electron | Playwright（原生支持） | 同 Web | DOM 提取 | 起 Electron 二进制 | **实** |
| Flutter | **`integration_test` + WidgetTester（白盒·主）**；`flutter_driver` / `appium-flutter-driver`（黑盒·备） | `ValueKey` / `Semantics` label，Finder | **widget/semantics 树**提取；`CustomPaint`/图表退截图+OCR | 模拟器/设备 + `--dart-define` 指测试后端 | **实**（integration_test） |
| Android | Appium（UiAutomator2） | `resource-id` / `content-desc` | 原生元素树提取 | 模拟器/真机 + 装 apk | 占位（`not-implemented`） |
| iOS | Appium（XCUITest） | `accessibilityIdentifier` | 原生元素树提取 | 模拟器/真机 + 装 app | 占位（`not-implemented`） |

### 适配器登记（v1）

| 端 | 适配器实现 | v1 可跑 |
|---|---|---|
| Web | `PlaywrightAdapter`（`assets/playwright-adapter-skeleton.ts`） | 是 |
| Electron | `PlaywrightAdapter`（同上，Playwright 原生支持 Electron） | 是 |
| Flutter | `FlutterAdapter`（`assets/flutter-adapter-skeleton.dart`，integration_test 白盒） | 是 |
| Android | 占位适配器 `AndroidAdapter`（`not-implemented`） | 否 |
| iOS | 占位适配器 `IosAdapter`（`not-implemented`） | 否 |

---

## 3. 各端实现说明（Flutter 已实现 · Android/iOS 占位）

### Flutter 适配器（`integration_test` 白盒为主）

Flutter 在 v1 **已做实**，骨架见 `assets/flutter-adapter-skeleton.dart`。8 个契约方法到 Flutter 的映射：

| 契约方法 | Flutter（integration_test + WidgetTester）实现 |
|---|---|
| `launch` | `IntegrationTestWidgetsFlutterBinding.ensureInitialized()` → 启动 app → `pumpAndSettle()`；后端地址用 `--dart-define` 注入 |
| `locate` | 返回 `Finder`：`find.byKey(ValueKey('...'))`（testid 类比，首选）/ `find.bySemanticsLabel(...)` / `find.text(...)`，非 CSS/XPath |
| `act` | `tester.tap` / `enterText` / `drag` 后 `pumpAndSettle()` |
| `observe` | widget/semantics 树描述 + 截图（截图供取证/视觉回归/OCR 兜底） |
| `readDisplay` | **结构化提取**：直接读 widget 属性（如 `tester.widget<Text>(finder).data`），展示预言机主路径 |
| `assert` | `expect(finder, findsOneWidget)` / `expect(readDisplay(...), matcher)` |
| `collectEvidence` | 截图 + widget 树转储（进程内日志经 `debugPrint`；无浏览器 console/network） |
| `teardown` | 复位 binding 状态 + 经数据网关回滚 |

**结构化提取特殊性**：Flutter render-to-canvas、无 DOM，所以读树而非找原生控件；`CustomPaint`/图表等无文本节点的 canvas 渲染退到截图 + OCR（精度有限，仅兜底）。

**数据网关注意（白盒 DB 限制）**：integration_test 跑在设备/模拟器上，**设备难直连测试库**，故 Flutter 的持久化校验**走 API 黑盒为主**（设备经网络访问宿主后端，base URL 由 `--dart-define` 注入）。若确需 DB 白盒兜底，需改用宿主侧 runner（`flutter_driver` / `appium-flutter-driver`），不在本进程内适配器范围。这是 Flutter 端相对 Web/Electron 的唯一数据层差异；三层校验的①交互②展示仍完整。

### Android / iOS 的原生树（占位）

Android/iOS 仍为 v1 占位：适配器骨架 8 个契约方法均标 `not-implemented`，抛「当前版本未实现」明确错误，防止误触发。其原生壳走 Appium 原生树（非 WebView 内嵌页面）：

Android/iOS 原生壳走 Appium 原生树（非 WebView 内嵌页面）：

- Android：UiAutomator2，`resource-id`（如 `com.example:id/submit_button`）/ `content-desc`（ARIA 类比）
- iOS：XCUITest，`accessibilityIdentifier`

`readDisplay` 提取原生元素的文本属性（`text` 属性 / `label` 属性），不依赖 DOM。

---

> **与其它 reference 的衔接**：
> - 契约中 `observe() / readDisplay()` 的「展示预言机」语义 → `oracle-and-data.md §2②`
> - 契约中 `collectEvidence()` 证据包用途 → `triage-decision-tree.md`（三段定责取证）
> - 占位适配器 `not-implemented` 仅 Android/iOS；Flutter 已按本契约实现。后续扩展 Android/iOS 时同样按本契约补实现，SKILL.md 主流程零改动（方案 §3.5）
