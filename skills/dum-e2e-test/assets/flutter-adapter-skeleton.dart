/// 参考模板，非即用；落地按目标项目调整。
///
/// Flutter 适配器骨架 —— integration_test + WidgetTester（白盒·进程内）统一驱动实现。
/// 实现来源：skills/dum-e2e-test/references/platform-adapters.md §1 统一驱动契约。
/// 数据网关来源：skills/dum-e2e-test/references/oracle-and-data.md §4 数据网关契约。
///
/// 重要数据约束：
///   integration_test 运行于设备/模拟器进程内，无法直连宿主机测试库。
///   持久化校验须走 API（ApiGateway，黑盒），DbGateway（白盒）在本适配器范围外，见下文。
///
/// 使用前须替换：
///   - app.main()：替换为被测应用的实际入口函数
///   - APP_API_BASE（--dart-define=APP_API_BASE=http://...）：后端 API 根地址
///   - ApiGateway 中的路由路径：按后端实际 seed/query/reset 端点调整
///   - Widget Key（ValueKey(...)）：按被测 Widget 实际 testid 替换
///
/// @module flutter-adapter-skeleton

// ignore_for_file: avoid_print

import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:http/http.dart' as http;

// 落地时替换为被测应用实际入口（含 WidgetsFlutterBinding / runApp）
// import 'package:your_app/main.dart' as app;

// ─────────────────────────────────────────────
// 类型定义
// ─────────────────────────────────────────────

/// launch() 的目标描述符
class LaunchTarget {
  /// 后端 API 根地址，通过 --dart-define=APP_API_BASE=http://... 注入。
  /// integration_test 运行于设备/模拟器，须通过网络访问宿主机后端。
  final String apiBase;

  /// 可选：被测 App 启动参数（如环境标识、feature flag 等）
  final Map<String, String> dartDefines;

  const LaunchTarget({
    required this.apiBase,
    this.dartDefines = const {},
  });
}

/// launch() 返回的会话句柄，供后续所有方法使用
class FlutterSession {
  /// WidgetTester 实例（由 testWidgets 回调注入，FlutterAdapter 持有引用）
  final WidgetTester tester;

  /// integration_test Binding（用于截图等进程内操作）
  final IntegrationTestWidgetsFlutterBinding binding;

  /// 后端 API 根地址（从 LaunchTarget 传入）
  final String apiBase;

  /// 进程内日志（通过 debugPrint 捕获；无 Playwright 那样的 browser console/network）
  final List<String> debugLogs;

  FlutterSession({
    required this.tester,
    required this.binding,
    required this.apiBase,
    List<String>? debugLogs,
  }) : debugLogs = debugLogs ?? [];
}

/// locate() 查询描述符
///
/// Flutter 无 DOM/CSS，定位优先级：
///   ValueKey（testid 类比）> SemanticsLabel > 可见文本
class LocateQuery {
  /// 首选：Widget 上打的 Key（ValueKey('...')），等价于 web 的 data-testid
  final String? key;

  /// 次选：Semantics label（ARIA label 类比），用于 find.bySemanticsLabel
  final String? semanticsLabel;

  /// 三选：可见文本精确匹配，用于 find.text
  final String? text;

  /// 可见文本包含匹配，用于 find.textContaining
  final String? textContaining;

  const LocateQuery({
    this.key,
    this.semanticsLabel,
    this.text,
    this.textContaining,
  }) : assert(
          key != null ||
              semanticsLabel != null ||
              text != null ||
              textContaining != null,
          'locate() 至少需提供 key / semanticsLabel / text / textContaining 之一',
        );
}

/// act() 语义动作描述符
class WidgetAction {
  /// 'tap' | 'enterText' | 'scroll' | 'drag' | 'longPress'
  final String type;

  /// enterText 时的输入内容
  final String? value;

  /// scroll 的偏移量（dx, dy）
  final Offset? scrollDelta;

  const WidgetAction.tap() : type = 'tap', value = null, scrollDelta = null;
  const WidgetAction.enterText(String text)
      : type = 'enterText',
        value = text,
        scrollDelta = null;
  const WidgetAction.scroll({Offset delta = const Offset(0, -300)})
      : type = 'scroll',
        value = null,
        scrollDelta = delta;
  const WidgetAction.longPress() : type = 'longPress', value = null, scrollDelta = null;
}

/// observe() 返回的快照
class WidgetSnapshot {
  /// Widget/Semantics 树的字符串描述（用于结构化分析）
  final String widgetTree;

  /// 截图 Buffer（PNG），供取证与可选视觉/OCR 兜底
  final Uint8List screenshot;

  const WidgetSnapshot({
    required this.widgetTree,
    required this.screenshot,
  });
}

/// collectEvidence() 返回的证据包
class EvidenceBundle {
  /// 截图字节（PNG）
  final Uint8List screenshot;

  /// Widget 树文本转储
  final String widgetTree;

  /// 进程内日志（debugPrint 输出；注：无 browser console/network tab，
  /// 因为 integration_test 进程内没有独立的网络拦截层）
  final List<String> debugLogs;

  const EvidenceBundle({
    required this.screenshot,
    required this.widgetTree,
    required this.debugLogs,
  });
}

/// assert() 支持的期望形式
class Expectation {
  /// 'equals' | 'contains' | 'visible' | 'hidden'
  final String type;

  /// equals / contains 时的期望值
  final String? value;

  const Expectation.equals(String v) : type = 'equals', value = v;
  const Expectation.contains(String v) : type = 'contains', value = v;
  const Expectation.visible() : type = 'visible', value = null;
  const Expectation.hidden() : type = 'hidden', value = null;
}

// ─────────────────────────────────────────────
// FlutterAdapter —— 统一驱动契约实现
// ─────────────────────────────────────────────

/// FlutterAdapter 实现统一驱动契约（platform-adapters.md §1）。
///
/// 驱动层：integration_test + WidgetTester（白盒·进程内）。
/// 特点：
///   - 可直接访问 Widget 树（`tester.widget<T>(finder)`），readDisplay 精确。
///   - 无法直连宿主机测试库；持久化校验走 ApiGateway（HTTP）。
///   - 日志通过 debugPrint 采集，无 Playwright-style browser console/network。
///
/// 使用方式：在 testWidgets() 回调内构造 FlutterAdapter(tester)，
/// 然后调用 launch → locate → act → observe/readDisplay → assert → collectEvidence → teardown。
class FlutterAdapter {
  final WidgetTester _tester;
  FlutterSession? _session;

  FlutterAdapter(this._tester);

  // ──────────────────────────────────────────
  // 1. launch —— 绑定 Binding、泵入 App、等待稳定
  // ──────────────────────────────────────────

  /// 启动被测应用，返回 FlutterSession 供后续调用。
  ///
  /// - 绑定 IntegrationTestWidgetsFlutterBinding（ensureInitialized）
  /// - pump 被测 App（app.main() 或 tester.pumpWidget(...)）
  /// - pumpAndSettle() 等待帧稳定
  /// - 后端 baseUrl 从 --dart-define=APP_API_BASE=... 注入，存入 session
  ///
  /// @param target LaunchTarget（含 apiBase）
  /// @returns FlutterSession
  Future<FlutterSession> launch(LaunchTarget target) async {
    final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

    // 进程内日志收集（替代 browser console）
    final debugLogs = <String>[];
    final originalDebugPrint = debugPrint;
    debugPrint = (String? message, {int? wrapWidth}) {
      if (message != null) debugLogs.add(message);
      originalDebugPrint(message, wrapWidth: wrapWidth);
    };

    // 泵入被测 App。
    // 落地时替换 app.main() 为被测应用实际入口，
    // 或直接用 tester.pumpWidget(MyApp()) 包裹根 Widget。
    // app.main();                          // ← 替换这行
    await _tester.pumpWidget(
      const Placeholder(), // ← 占位，落地时替换为 app 根 Widget
    );
    // 等待首帧稳定（动画/Future 全部完成）
    await _tester.pumpAndSettle();

    _session = FlutterSession(
      tester: _tester,
      binding: binding,
      apiBase: target.apiBase,
      debugLogs: debugLogs,
    );
    return _session!;
  }

  // ──────────────────────────────────────────
  // 2. locate —— 语义定位，返回 Finder
  // ──────────────────────────────────────────

  /// 按优先级语义定位 Widget，返回 Finder。
  ///
  /// 优先级：ValueKey > SemanticsLabel > text > textContaining。
  /// Flutter 无 DOM/CSS/XPath，禁用任何基于像素坐标的硬编码定位。
  /// 约定：被测 Widget 须标注 Key(ValueKey('testid-xxx'))，等价于 web 的 data-testid。
  ///
  /// @param query LocateQuery
  /// @returns Finder
  Finder locate(LocateQuery query) {
    if (query.key != null) {
      // 首选：ValueKey —— Flutter testid 类比（platform-adapters.md §2 表格）
      return find.byKey(ValueKey(query.key));
    }
    if (query.semanticsLabel != null) {
      // 次选：Semantics label（ARIA label 类比），适用于图标按钮等无文本节点
      return find.bySemanticsLabel(query.semanticsLabel!);
    }
    if (query.text != null) {
      // 精确文本匹配
      return find.text(query.text!);
    }
    if (query.textContaining != null) {
      // 包含文本匹配
      return find.textContaining(query.textContaining!);
    }
    throw StateError('locate() 至少需提供 key / semanticsLabel / text / textContaining 之一');
  }

  // ──────────────────────────────────────────
  // 3. act —— 对 Widget 执行语义动作
  // ──────────────────────────────────────────

  /// 对 finder 定位的 Widget 执行语义动作，动作后自动 pumpAndSettle()。
  ///
  /// 支持 tap / enterText / scroll / longPress。
  /// pumpAndSettle 确保动画与 Future 在动作后全部完成。
  ///
  /// @param handle 由 locate() 返回的 Finder
  /// @param action WidgetAction 语义动作
  Future<void> act(Finder handle, WidgetAction action) async {
    switch (action.type) {
      case 'tap':
        await _tester.tap(handle);
        break;
      case 'enterText':
        // 先 tap 获取焦点，再输入文本
        await _tester.tap(handle);
        await _tester.pumpAndSettle();
        await _tester.enterText(handle, action.value ?? '');
        break;
      case 'scroll':
        await _tester.drag(handle, action.scrollDelta ?? const Offset(0, -300));
        break;
      case 'longPress':
        await _tester.longPress(handle);
        break;
      default:
        throw ArgumentError('未知动作类型：${action.type}');
    }
    // 等帧稳定（动画完成、FutureBuilder 刷新）
    await _tester.pumpAndSettle();
  }

  // ──────────────────────────────────────────
  // 4. observe —— Widget/Semantics 树快照 + 截图
  // ──────────────────────────────────────────

  /// 获取当前 Widget/Semantics 树快照与截图。
  ///
  /// - widgetTree（字符串描述）：展示预言机默认读树做结构化提取（§3 widget-tree）
  /// - screenshot（PNG）：供取证与可选 OCR 兜底
  ///   （CustomPaint / 图表等无文本节点 → 退截图+OCR 兜底，参见 platform-adapters.md §3）
  ///
  /// 注：integration_test 使用 binding.takeScreenshot()，
  ///     截图字节存于内存，落地时可写入文件系统（需平台文件权限）。
  ///
  /// @returns WidgetSnapshot
  Future<WidgetSnapshot> observe() async {
    final session = _requireSession();

    // Widget 树字符串描述（用于结构化分析，类比 Playwright 的 outerHTML）
    final treeBuffer = StringBuffer();
    _tester.binding.rootElement?.debugFillProperties(
      DiagnosticPropertiesBuilder(),
    );
    // 简化版：用 find.byType(Widget) 的 description 描述树结构
    treeBuffer.writeln('=== Widget Tree Snapshot ===');
    treeBuffer.writeln(_tester.binding.rootElement.toString());

    // 截图（integration_test 提供，返回 PNG 字节）
    final screenshotBytes = await session.binding.takeScreenshot('observe-snapshot');

    return WidgetSnapshot(
      widgetTree: treeBuffer.toString(),
      screenshot: Uint8List.fromList(screenshotBytes),
    );
  }

  // ──────────────────────────────────────────
  // 5. readDisplay —— 从 Widget 树精确提取呈现值
  // ──────────────────────────────────────────

  /// 从 Widget 树精确提取某处呈现的文本或值（展示预言机②主用）。
  ///
  /// 提取策略（优先级由高到低）：
  ///   1. Text Widget → tester.widget<Text>(finder).data
  ///   2. TextField / TextFormField → controller.text 或 tester.widget<EditableText>(finder).controller.text
  ///   3. 其他有 Semantics.label 的 Widget → semanticsLabel
  ///
  /// 注意：CustomPaint / 图表等无文本节点不在此路径内；
  ///       此类 Widget 须退到 observe() 截图 + OCR 兜底。
  ///
  /// @param finder 由 locate() 返回的 Finder
  /// @returns 提取到的字符串（trimmed）
  String readDisplay(Finder finder) {
    // 尝试读取 Text Widget 的 data 属性（最精确，直接取渲染值）
    try {
      final textWidget = _tester.widget<Text>(finder);
      return (textWidget.data ?? '').trim();
    } catch (_) {
      // 不是 Text Widget，继续尝试
    }

    // 尝试读取 EditableText（TextField 内部）的 controller 值
    try {
      final editableText = _tester.widget<EditableText>(finder);
      return editableText.controller.text.trim();
    } catch (_) {
      // 不是 EditableText，继续尝试
    }

    // 降级：从 Semantics 节点读取 label（适用于图标按钮等有语义标签的 Widget）
    try {
      final semantics = _tester.getSemantics(finder);
      final label = semantics.label;
      if (label.isNotEmpty) return label.trim();
    } catch (_) {
      // Semantics 不可用，继续
    }

    // 最终降级：返回空字符串，提示调用方退 observe()+OCR 兜底
    // CustomPaint/图表等无文本节点会走到这里
    // 落地时可在此处集成 OCR 方案（如 mlkit_text_recognition）
    return '';
  }

  // ──────────────────────────────────────────
  // 6. assert —— 对 Finder 或快照内容断言
  // ──────────────────────────────────────────

  /// 对 Finder 或快照内容进行断言。
  ///
  /// - visible / hidden：用 expect(finder, findsOneWidget) / findsNothing
  /// - equals / contains：先 readDisplay 提取文本，再比对
  ///
  /// @param target Finder 或 WidgetSnapshot
  /// @param expectation Expectation 期望描述符
  Future<void> assertWidget(
    Object target,
    Expectation expectation,
  ) async {
    if (target is WidgetSnapshot) {
      // 对快照（widgetTree 字符串）断言
      _assertString(target.widgetTree, expectation, 'Widget 树快照');
      return;
    }

    if (target is! Finder) {
      throw ArgumentError('assertWidget() 的 target 须为 Finder 或 WidgetSnapshot');
    }

    final finder = target;
    switch (expectation.type) {
      case 'visible':
        // 确认 Widget 存在且可见
        expect(finder, findsOneWidget);
        break;
      case 'hidden':
        // 确认 Widget 不存在或不可见
        expect(finder, findsNothing);
        break;
      default:
        // 读取显示文本再断言
        final text = readDisplay(finder);
        _assertString(text, expectation, '元素文本');
    }
  }

  // ──────────────────────────────────────────
  // 7. collectEvidence —— 收集证据包
  // ──────────────────────────────────────────

  /// 收集测试证据包：截图 + Widget 树转储 + 进程内日志。
  ///
  /// 失败时必须调用（oracle-and-data.md §3 "角色一：永远取证"）。
  ///
  /// 注：与 Playwright 适配器不同，integration_test 进程内：
  ///   - 无独立的 browser console/network 拦截层（日志走 debugPrint）
  ///   - 截图通过 binding.takeScreenshot()（返回字节，须自行写文件）
  ///   - 无 Playwright trace 格式；如需 trace，可接 dart:developer 的 Timeline
  ///
  /// @param label 证据标签（如 'TC-xxx-001-fail'）
  /// @returns EvidenceBundle
  Future<EvidenceBundle> collectEvidence(String label) async {
    final session = _requireSession();

    // ① 截图
    final screenshotBytes = await session.binding.takeScreenshot('evidence-$label');

    // ② Widget 树转储
    final treeBuffer = StringBuffer();
    treeBuffer.writeln('=== Widget Tree Dump: $label ===');
    treeBuffer.writeln(_tester.binding.rootElement.toString());

    // ③ 进程内日志（已在 launch() 中通过 debugPrint 钩子收集）
    final logs = List<String>.unmodifiable(session.debugLogs);

    // 落地时可将证据写入设备文件系统，示例：
    // final dir = await getTemporaryDirectory();
    // File('${dir.path}/$label-screenshot.png').writeAsBytesSync(screenshotBytes);
    // File('${dir.path}/$label-widget-tree.txt').writeAsStringSync(treeBuffer.toString());

    return EvidenceBundle(
      screenshot: Uint8List.fromList(screenshotBytes),
      widgetTree: treeBuffer.toString(),
      debugLogs: logs,
    );
  }

  // ──────────────────────────────────────────
  // 8. teardown —— 重置 Binding 状态，触发数据回滚
  // ──────────────────────────────────────────

  /// 清理会话：重置 Binding 测试状态，并触发数据回滚。
  ///
  /// 应在 tearDown() 回调中调用，确保不留残余 Widget 状态与测试数据。
  ///
  /// 注：integration_test 进程内无"关闭浏览器"操作；
  ///     每个 testWidgets() 用例结束后 Flutter 框架会自动清理 Widget 树。
  ///     teardown 主要职责是：① 触发 gateway.rollback 精确回收造数；
  ///                           ② 通知 binding 本测试已结束（如有需要）。
  ///
  /// @param session 由 launch() 返回的 FlutterSession
  /// @param gateway 可选：数据网关实例（传入则自动调用 rollback）
  /// @param seedHandle 可选：seed() 返回的 handle，供 rollback 精确回收
  Future<void> teardown(
    FlutterSession session, {
    DataGateway? gateway,
    SeedHandle? seedHandle,
  }) async {
    // 数据回滚（精确回收本用例所造数据，避免污染其他用例）
    if (gateway != null && seedHandle != null) {
      await gateway.rollback(seedHandle);
    }

    // integration_test binding 状态重置
    // （binding 本身的 framePolicy 等由 testWidgets 框架自动恢复，
    //   此处仅做业务层日志清理）
    session.debugLogs.clear();

    _session = null;
  }

  // ──────────────────────────────────────────
  // 私有工具
  // ──────────────────────────────────────────

  FlutterSession _requireSession() {
    if (_session == null) {
      throw StateError('Session 未初始化，请先调用 launch()');
    }
    return _session!;
  }

  void _assertString(String actual, Expectation expectation, String label) {
    switch (expectation.type) {
      case 'equals':
        if (actual != expectation.value) {
          throw TestFailure(
            '断言失败（$label equals）\n期望：${expectation.value}\n实际：$actual',
          );
        }
        break;
      case 'contains':
        if (!actual.contains(expectation.value ?? '')) {
          throw TestFailure(
            '断言失败（$label contains）\n期望包含：${expectation.value}\n实际：$actual',
          );
        }
        break;
      default:
        throw ArgumentError('assertWidget 不支持对字符串使用 ${expectation.type} 类型');
    }
  }
}

// ─────────────────────────────────────────────
// 数据网关契约类型（oracle-and-data.md §4）
// ─────────────────────────────────────────────

/// seed() 返回的句柄，供 rollback 精确回收
class SeedHandle {
  final Object id;
  final String type;
  final Map<String, dynamic>? meta;

  const SeedHandle({required this.id, required this.type, this.meta});
}

/// seed() 的数据规格
class SeedSpec {
  /// 资源类型，如 'user' / 'order' / 'product'
  final String type;

  /// 字段值
  final Map<String, dynamic> data;

  const SeedSpec({required this.type, required this.data});
}

/// query() 的查询描述符
class QuerySelector {
  /// 资源类型或 API 路径
  final String type;

  /// 过滤条件
  final Map<String, dynamic>? filter;

  const QuerySelector({required this.type, this.filter});
}

/// reset() 的作用域
class ResetScope {
  /// 'all' | 资源类型名 | 表名
  final String target;

  const ResetScope({required this.target});
}

/// 数据网关统一接口（两套实现共享此契约）
abstract interface class DataGateway {
  Future<SeedHandle> seed(SeedSpec spec);
  Future<List<dynamic>> query(QuerySelector selector);
  Future<void> reset(ResetScope scope);
  Future<void> rollback(SeedHandle handle);
}

// ─────────────────────────────────────────────
// ApiGateway 实现（黑盒·默认）
// oracle-and-data.md §4 —— gateway = api
// ─────────────────────────────────────────────

/// ApiGateway：通过 Dart http 包调后端 seed/query/reset 端点。
///
/// integration_test 运行于设备/模拟器，通过网络访问宿主机后端（--dart-define=APP_API_BASE=...）。
/// 这是 Flutter 适配器的默认/首选数据网关（黑盒·不耦合表结构）。
///
/// 落地时替换：
///   - apiBase 从 const String.fromEnvironment('APP_API_BASE') 读取
///   - 路径（/test/seed 等）按后端实际路由调整
///   - 如需认证，在 _headers 中添加 Authorization 头
class ApiGateway implements DataGateway {
  final String _baseUrl;
  final Map<String, String> _headers;
  final http.Client _client;

  ApiGateway({
    required String baseUrl,
    Map<String, String>? headers,
    http.Client? client,
  })  : _baseUrl = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl,
        _headers = {'Content-Type': 'application/json', ...?headers},
        _client = client ?? http.Client();

  /// 走后门造前置数据：POST /test/seed
  /// 后端按 spec.type 路由到对应 factory，返回 { id, type }。
  @override
  Future<SeedHandle> seed(SeedSpec spec) async {
    final resp = await _client.post(
      Uri.parse('$_baseUrl/test/seed'),
      headers: _headers,
      body: jsonEncode({'type': spec.type, 'data': spec.data}),
    );
    _assertOk(resp, 'seed');
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    return SeedHandle(
      id: body['id'] as Object,
      type: spec.type,
      meta: body,
    );
  }

  /// 读持久化状态供断言：GET /test/query?type=...&filter=...
  /// 用于持久化预言机③（默认 gateway=api）。
  @override
  Future<List<dynamic>> query(QuerySelector selector) async {
    final params = <String, String>{'type': selector.type};
    if (selector.filter != null) {
      params['filter'] = jsonEncode(selector.filter);
    }
    final resp = await _client.get(
      Uri.parse('$_baseUrl/test/query').replace(queryParameters: params),
      headers: _headers,
    );
    _assertOk(resp, 'query');
    return jsonDecode(resp.body) as List<dynamic>;
  }

  /// 复位指定范围数据：POST /test/reset
  @override
  Future<void> reset(ResetScope scope) async {
    final resp = await _client.post(
      Uri.parse('$_baseUrl/test/reset'),
      headers: _headers,
      body: jsonEncode({'target': scope.target}),
    );
    _assertOk(resp, 'reset');
  }

  /// 精确回滚本用例所造数据：DELETE /test/seed/:type/:id
  /// 避免污染其他用例（teardown 中调用）。
  @override
  Future<void> rollback(SeedHandle handle) async {
    final resp = await _client.delete(
      Uri.parse('$_baseUrl/test/seed/${handle.type}/${handle.id}'),
      headers: _headers,
    );
    if (resp.statusCode >= 400) {
      // rollback 失败不应掩盖测试结果，记录警告即可
      debugPrint(
        '[ApiGateway] rollback 警告：${resp.statusCode}，handle={id:${handle.id}, type:${handle.type}}',
      );
    }
  }

  void _assertOk(http.Response resp, String method) {
    if (resp.statusCode >= 400) {
      throw StateError('ApiGateway.$method 失败：${resp.statusCode} ${resp.body}');
    }
  }

  /// 释放 http.Client 资源（测试结束后调用）
  void dispose() => _client.close();
}

// ─────────────────────────────────────────────
// DbGateway 占位（白盒·兜底）
// oracle-and-data.md §4 —— gateway = db
// ─────────────────────────────────────────────

/// DbGateway 占位：直连测试库的白盒网关。
///
/// ⚠️ 重要：integration_test 运行于设备/模拟器进程内，
///    无法直接连接宿主机测试数据库（TCP 端口不可达，驱动包不可用）。
///    因此 Flutter 的持久化校验优先走 ApiGateway（黑盒，通过 HTTP 访问后端）。
///
/// 若确实需要 DB 白盒兜底（如审计日志、旁表副作用校验），须改用：
///   - appium-flutter-driver（黑盒进程外）+ 宿主机侧 DB 客户端
///   - flutter_driver（同上）
///   - 自定义宿主机 runner，完全在 JVM/Node 侧驱动并直连 DB
///   以上方案均超出本进程内适配器的范围。
///
/// 落地时如需实现：
///   TODO 1. 改用进程外驱动（见上文说明）
///   TODO 2. 在宿主机侧接入项目 DB 客户端（Prisma / TypeORM / go-pg 等）
///   TODO 3. 从环境清单（env-manifest-template.yaml 的 test_db 字段）读取 DSN
///   TODO 4. 删除 UnimplementedError，实现各方法体
class DbGateway implements DataGateway {
  // TODO: 宿主机侧 DB 客户端配置（本适配器无法直连，见上文）
  // final YourDbClient _db = YourDbClient(dsn: Platform.environment['TEST_DB_DSN']!);

  @override
  Future<SeedHandle> seed(SeedSpec spec) {
    // TODO: 进程外驱动方案中用 ORM/SQL 直插测试数据，返回主键 id
    throw UnimplementedError(
      'DbGateway.seed 未实现——integration_test 进程内无法直连宿主机 DB。'
      '请使用 ApiGateway（黑盒），或改用进程外驱动（见类注释）。',
    );
  }

  @override
  Future<List<dynamic>> query(QuerySelector selector) {
    // TODO: 进程外驱动方案中用 ORM/SQL 直查，返回行数组
    throw UnimplementedError(
      'DbGateway.query 未实现——integration_test 进程内无法直连宿主机 DB。'
      '请使用 ApiGateway，或改用进程外驱动。',
    );
  }

  @override
  Future<void> reset(ResetScope scope) {
    // TODO: 进程外驱动方案中 truncate 表 / 删命名空间数据
    throw UnimplementedError(
      'DbGateway.reset 未实现——integration_test 进程内无法直连宿主机 DB。',
    );
  }

  @override
  Future<void> rollback(SeedHandle handle) {
    // TODO: 进程外驱动方案中按主键精确删除
    throw UnimplementedError(
      'DbGateway.rollback 未实现——integration_test 进程内无法直连宿主机 DB。',
    );
  }
}

// ─────────────────────────────────────────────
// 示范 Spec —— 完整三层断言用例
// 走后门 seed → 走前门 UI 操作 → 三层校验断言
// ─────────────────────────────────────────────

/// 示范 integration_test 用例：展示 FlutterAdapter 完整用法与三层断言。
///
/// 落地时：
///   1. 将此函数移入 integration_test/ 目录的测试文件中
///   2. 替换 app.main()、Widget Key、路由逻辑
///   3. 按实际场景修改 seed 数据与 assert 期望

// @case TC-xxx-001
void runDemoIntegrationTest() {
  // integration_test binding 初始化（每个测试文件 main() 中调用一次）
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('TC-xxx-001 用户新增订单', () {
    // 从 --dart-define 读取后端地址（落地时按 CI/本地环境配置）
    const apiBase = String.fromEnvironment(
      'APP_API_BASE',
      defaultValue: 'http://10.0.2.2:4000', // Android 模拟器访问宿主机
    );

    late FlutterAdapter adapter;
    late ApiGateway apiGateway;
    SeedHandle? seedHandle;

    setUp(() {
      // ApiGateway 是 Flutter 适配器的默认数据网关（HTTP，不依赖直连 DB）
      apiGateway = ApiGateway(baseUrl: apiBase);
    });

    tearDown(() async {
      // teardown：精确回滚 seed 数据，防止污染其他用例
      if (seedHandle != null) {
        await adapter.teardown(
          adapter._session!, // 实际项目中可将 session 存为局部变量传入
          gateway: apiGateway,
          seedHandle: seedHandle,
        );
        seedHandle = null;
      }
      apiGateway.dispose();
    });

    testWidgets(
      'TC-xxx-001: 新增订单后列表展示正确，持久化确认',
      (WidgetTester tester) async {
        // ── 构造适配器（WidgetTester 由 testWidgets 注入）──────────
        adapter = FlutterAdapter(tester);

        // ── Arrange：走后门 seed 前置数据 ──────────────────────────
        // 通过 ApiGateway 造一条订单，不经 UI（走后门）
        seedHandle = await apiGateway.seed(
          const SeedSpec(
            type: 'order',
            data: {
              'productName': '测试商品-TC-xxx-001',
              'quantity': 2,
              'status': 'pending',
            },
          ),
        );

        // ── 起测应用 ────────────────────────────────────────────────
        await adapter.launch(LaunchTarget(apiBase: apiBase));
        // 注：launch() 内会调用 app.main() + pumpAndSettle()
        //     落地时确保 app.main() 已替换为被测应用入口

        // ── Act：走前门 UI 操作 ─────────────────────────────────────
        // 定位商品名输入框（ValueKey = testid，落地时按实际 Widget Key 替换）
        final productInput = adapter.locate(
          const LocateQuery(key: 'order-product-name-input'),
        );
        await adapter.act(productInput, const WidgetAction.tap());
        await adapter.act(
          productInput,
          const WidgetAction.enterText('前门商品-TC-xxx-001'),
        );

        // 定位数量输入框
        final qtyInput = adapter.locate(
          const LocateQuery(key: 'order-quantity-input'),
        );
        await adapter.act(
          qtyInput,
          const WidgetAction.enterText('3'),
        );

        // 点击提交按钮
        final submitBtn = adapter.locate(
          const LocateQuery(semanticsLabel: '提交订单'),
        );
        await adapter.act(submitBtn, const WidgetAction.tap());

        // ── Assert ① 交互预言机：操作后出现成功 SnackBar/Toast ──────
        // 通过文本定位 SnackBar 内容（integration_test 中 SnackBar 是普通 Widget）
        final successToast = adapter.locate(
          const LocateQuery(text: '提交成功'),
        );
        await adapter.assertWidget(successToast, const Expectation.visible());

        // ── Assert ② 展示预言机：列表中新增行显示正确商品名 ──────────
        // pumpAndSettle 确保列表刷新完成
        await tester.pumpAndSettle();

        // 定位列表中第一行的商品名（ValueKey 由被测 Widget 打 key）
        final firstRowName = adapter.locate(
          const LocateQuery(key: 'order-row-product-name-0'),
        );
        // readDisplay 从 Widget 树精确读取 Text.data（非截图，非 OCR）
        final displayedName = adapter.readDisplay(firstRowName);
        await adapter.assertWidget(
          firstRowName,
          const Expectation.contains('前门商品'),
        );

        // 附加验证：readDisplay 返回值与期望一致
        if (!displayedName.contains('前门商品')) {
          throw TestFailure(
            '展示预言机②断言失败：期望包含"前门商品"，实际：$displayedName',
          );
        }

        // ── Assert ③ 持久化预言机：apiGateway.query 确认持久化 ──────
        // gateway = api（默认，不耦合表结构；oracle-and-data.md §2③）
        // 走 HTTP 查后端，确认订单已写入持久层
        final rows = await apiGateway.query(
          const QuerySelector(
            type: 'order',
            filter: {'productName': '前门商品-TC-xxx-001'},
          ),
        );
        expect(rows, isNotEmpty, reason: '持久化预言机③断言失败：apiGateway.query 未返回对应订单记录');

        debugPrint('[TC-xxx-001] 三层断言全部通过 ✓');
      },
    );
  });
}
