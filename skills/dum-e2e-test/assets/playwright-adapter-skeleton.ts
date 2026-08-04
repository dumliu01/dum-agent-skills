/**
 * 参考模板，非即用；落地按目标项目调整。
 *
 * Playwright 适配器骨架 —— Web / Electron 双端统一驱动实现。
 * 仅用于项目没有现成 E2E 基础设施时；已有 config、fixture、
 * Page Object、Gateway 和 Runner 时必须复用，不得用本文件覆盖。
 * 实现来源：skills/dum-e2e-test/references/platform-adapters.md §1 统一驱动契约。
 * 数据网关来源：skills/dum-e2e-test/references/oracle-and-data.md §4 数据网关契约。
 *
 * 使用前须替换：
 *   - BASE_URL：被测应用的 Web URL 或 Electron 二进制路径
 *   - API_BASE：后端 API 根地址（apiGateway 使用）
 *   - dbGateway 中的 TODO 行：接入项目的 ORM / SQL 客户端与测试库 DSN
 *
 * @module playwright-adapter-skeleton
 */

import {
  chromium,
  _electron as electron,
  type Browser,
  type BrowserContext,
  type Page,
  type Locator,
  type APIRequestContext,
  request as pwRequest,
} from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

// ─────────────────────────────────────────────
// 类型定义
// ─────────────────────────────────────────────

/** launch() 的目标描述符 */
export interface LaunchTarget {
  /** 'web' | 'electron' */
  mode: 'web' | 'electron';
  /** Web 模式：被测 URL；Electron 模式：二进制可执行路径 */
  url?: string;
  executablePath?: string;
  /** Electron 启动参数（可选） */
  args?: string[];
}

/** launch() 返回的会话句柄，供后续所有方法使用 */
export interface Session {
  page: Page;
  context: BrowserContext;
  browser?: Browser;
  /** 控制台日志（teardown 前可读） */
  consoleLogs: string[];
  /** 网络请求日志（teardown 前可读） */
  networkLogs: Array<{ url: string; status: number; method: string }>;
}

/** locate() 的查询描述符 */
export interface LocateQuery {
  /** 定位策略优先级：role > testId > text > css（不推荐 css） */
  role?: string;           // ARIA role，如 'button' / 'textbox'
  name?: string;           // role 对应的 accessible name
  testId?: string;         // data-testid 属性
  text?: string;           // 可见文本（精确匹配）
  textContains?: string;   // 可见文本（包含匹配）
}

/** act() 的语义动作 */
export interface Action {
  type: 'click' | 'fill' | 'press' | 'scroll' | 'selectOption' | 'check' | 'uncheck';
  value?: string;          // fill / press / selectOption 时使用
  key?: string;            // press 时的按键，如 'Enter'
}

/** observe() 返回的快照 */
export interface Snapshot {
  /** 当前页面 URL */
  url: string;
  /** 页面 outerHTML 截断版（DOM 快照，用于结构化分析） */
  html: string;
  /** 截图 Buffer（PNG），供取证与可选视觉回归/OCR 兜底 */
  screenshot: Buffer;
}

/** collectEvidence() 返回的证据包 */
export interface EvidenceBundle {
  screenshotPath: string;
  html: string;
  consoleLogs: string[];
  networkLogs: Array<{ url: string; status: number; method: string }>;
  /** Playwright trace 文件路径（如已开启 tracing） */
  tracePath?: string;
}

/** assert() 支持的期望形式 */
export interface Expectation {
  /** 'equals' | 'contains' | 'matches' | 'visible' | 'hidden' */
  type: 'equals' | 'contains' | 'matches' | 'visible' | 'hidden';
  /** 期望值（equals / contains / matches 时使用） */
  value?: string | RegExp;
}

// ─────────────────────────────────────────────
// PlaywrightAdapter —— 统一驱动契约实现
// ─────────────────────────────────────────────

/**
 * PlaywrightAdapter 实现统一驱动契约（platform-adapters.md §1）。
 * Web 与 Electron 共用同一适配器——Playwright 原生支持 Electron。
 */
export class PlaywrightAdapter {
  private session: Session | null = null;
  /** 证据输出目录（落地时按项目配置） */
  private evidenceDir: string;

  constructor(evidenceDir = './test-evidence') {
    this.evidenceDir = evidenceDir;
    fs.mkdirSync(this.evidenceDir, { recursive: true });
  }

  // ──────────────────────────────────────────
  // 1. launch —— 起 / 连被测应用
  // ──────────────────────────────────────────

  /**
   * 启动被测应用，返回 Session 供后续调用。
   * - Web 模式：启动 Chromium 并导航到目标 URL
   * - Electron 模式：通过 _electron.launch 启动 Electron 二进制
   *
   * @param target LaunchTarget 描述符
   * @returns Session
   */
  async launch(target: LaunchTarget): Promise<Session> {
    const consoleLogs: string[] = [];
    const networkLogs: Array<{ url: string; status: number; method: string }> = [];

    if (target.mode === 'electron') {
      // ── Electron 路径：Playwright 原生支持 ──
      // _electron.launch 返回 ElectronApplication，getFirstWindow() 获取主窗口 Page
      const executablePath = target.executablePath ?? '';
      if (!executablePath) throw new Error('Electron 模式需提供 executablePath');

      const electronApp = await electron.launch({
        executablePath,
        args: target.args ?? [],
      });

      const page = await electronApp.firstWindow();
      const context = page.context();

      // 监听控制台与网络（同 Web 路径）
      page.on('console', (msg) => consoleLogs.push(`[${msg.type()}] ${msg.text()}`));
      page.on('response', (resp) =>
        networkLogs.push({ url: resp.url(), status: resp.status(), method: resp.request().method() }),
      );

      this.session = { page, context, consoleLogs, networkLogs };
      return this.session;
    }

    // ── Web 路径：Chromium ──
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      // 落地时按需开启 tracing
      // recordVideo: { dir: this.evidenceDir },
    });

    // 可选：开启 Playwright trace 供 collectEvidence
    // await context.tracing.start({ screenshots: true, snapshots: true });

    const page = await context.newPage();

    // 监听控制台日志
    page.on('console', (msg) => consoleLogs.push(`[${msg.type()}] ${msg.text()}`));
    // 监听网络响应
    page.on('response', (resp) =>
      networkLogs.push({ url: resp.url(), status: resp.status(), method: resp.request().method() }),
    );

    const url = target.url ?? 'http://localhost:3000';
    await page.goto(url, { waitUntil: 'networkidle' });

    this.session = { page, context, browser, consoleLogs, networkLogs };
    return this.session;
  }

  // ──────────────────────────────────────────
  // 2. locate —— 语义定位元素
  // ──────────────────────────────────────────

  /**
   * 按优先级语义定位：role > testId > text > textContains。
   * 禁用脆性 CSS 路径或绝对 XPath（参见 platform-adapters.md §1）。
   *
   * @param query LocateQuery
   * @returns Playwright Locator
   */
  locate(query: LocateQuery): Locator {
    const page = this._requireSession().page;

    if (query.role) {
      // 优先：ARIA role + accessible name
      return page.getByRole(query.role as Parameters<Page['getByRole']>[0], {
        name: query.name,
      });
    }
    if (query.testId) {
      // 次优：data-testid（平台类比 §2 表格中 Web/Electron 均为 data-testid）
      return page.getByTestId(query.testId);
    }
    if (query.text) {
      // 精确文本匹配
      return page.getByText(query.text, { exact: true });
    }
    if (query.textContains) {
      // 包含文本匹配
      return page.getByText(query.textContains, { exact: false });
    }
    throw new Error('locate() 至少需提供 role / testId / text / textContains 之一');
  }

  // ──────────────────────────────────────────
  // 3. act —— 对元素执行语义动作
  // ──────────────────────────────────────────

  /**
   * 对 locator 执行语义动作（click / fill / press / scroll / selectOption 等）。
   *
   * @param handle 由 locate() 返回的 Locator
   * @param action Action 动作描述符
   */
  async act(handle: Locator, action: Action): Promise<void> {
    switch (action.type) {
      case 'click':
        await handle.click();
        break;
      case 'fill':
        await handle.fill(action.value ?? '');
        break;
      case 'press':
        await handle.press(action.key ?? 'Enter');
        break;
      case 'scroll':
        await handle.scrollIntoViewIfNeeded();
        break;
      case 'selectOption':
        await handle.selectOption(action.value ?? '');
        break;
      case 'check':
        await handle.check();
        break;
      case 'uncheck':
        await handle.uncheck();
        break;
      default:
        throw new Error(`未知动作类型：${(action as Action).type}`);
    }
  }

  // ──────────────────────────────────────────
  // 4. observe —— 获取 DOM 快照 + 截图
  // ──────────────────────────────────────────

  /**
   * 获取当前页面的 DOM 快照与截图。
   * - DOM 快照（html）用于结构化提取（展示预言机默认，oracle-and-data.md §3 dom）
   * - 截图（screenshot）供取证与可选视觉回归/OCR 兜底（§3 visual / ocr）
   *
   * @returns Snapshot
   */
  async observe(): Promise<Snapshot> {
    const page = this._requireSession().page;
    const url = page.url();
    // DOM 快照：取 outerHTML 供结构化分析
    const html = await page.evaluate(() => document.documentElement.outerHTML);
    // 截图 Buffer（PNG）
    const screenshot = await page.screenshot({ type: 'png', fullPage: false });
    return { url, html, screenshot };
  }

  // ──────────────────────────────────────────
  // 5. readDisplay —— 从 DOM 语义树提取呈现值
  // ──────────────────────────────────────────

  /**
   * 从树语义提取某处呈现的文本或值（展示预言机②主用，oracle-and-data.md §3）。
   * - 普通文本节点 → locator.textContent()
   * - 表单输入（input / textarea）→ locator.inputValue()
   *
   * @param locator 由 locate() 返回的 Locator（或 page.locator() 直接构造）
   * @returns 提取到的字符串，trimmed
   */
  async readDisplay(locator: Locator): Promise<string> {
    // 先尝试 inputValue（表单元素），不适用时回退到 textContent
    try {
      const val = await locator.inputValue({ timeout: 2000 });
      return val.trim();
    } catch {
      // 非 input/textarea 时 inputValue 会抛错，fallback 到 textContent
      const text = await locator.textContent({ timeout: 5000 });
      return (text ?? '').trim();
    }
  }

  // ──────────────────────────────────────────
  // 6. assert —— 对元素句柄或快照内容断言
  // ──────────────────────────────────────────

  /**
   * 对元素句柄或快照内容进行断言。
   * 支持 equals / contains / matches / visible / hidden。
   *
   * 注：落地时可替换为 Playwright 的 expect() API，
   * 此处用 Node assert 保持骨架无 test-runner 依赖。
   *
   * @param target Locator 或 Snapshot
   * @param expectation Expectation 期望描述符
   */
  async assert(target: Locator | Snapshot, expectation: Expectation): Promise<void> {
    if (this._isSnapshot(target)) {
      // 对快照（html 字符串）断言
      const content = target.html;
      this._assertString(content, expectation, 'DOM 快照');
      return;
    }

    // 对 Locator 断言
    const locator = target as Locator;
    switch (expectation.type) {
      case 'visible':
        await locator.waitFor({ state: 'visible', timeout: 5000 });
        break;
      case 'hidden':
        await locator.waitFor({ state: 'hidden', timeout: 5000 });
        break;
      default: {
        // 读取文本再断言
        const text = await this.readDisplay(locator);
        this._assertString(text, expectation, '元素文本');
      }
    }
  }

  // ──────────────────────────────────────────
  // 7. collectEvidence —— 收集证据包
  // ──────────────────────────────────────────

  /**
   * 收集测试证据包：截图 + DOM 快照 + 控制台日志 + 网络请求日志 + trace 文件。
   * 失败时必须调用（oracle-and-data.md §3 "角色一：永远取证"）。
   * 成功时可选保留。
   *
   * @param label 证据文件名前缀（如 'TC-login-001-fail'）
   * @returns EvidenceBundle
   */
  async collectEvidence(label: string): Promise<EvidenceBundle> {
    const session = this._requireSession();
    const page = session.page;
    const ts = Date.now();
    const base = path.join(this.evidenceDir, `${label}-${ts}`);

    // ① 截图
    const screenshotPath = `${base}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });

    // ② DOM 快照
    const html = await page.evaluate(() => document.documentElement.outerHTML);
    fs.writeFileSync(`${base}.html`, html, 'utf8');

    // ③ 控制台日志（已在 launch() 中收集）
    const consoleLogs = [...session.consoleLogs];
    fs.writeFileSync(`${base}-console.log`, consoleLogs.join('\n'), 'utf8');

    // ④ 网络请求日志（已在 launch() 中收集）
    const networkLogs = [...session.networkLogs];
    fs.writeFileSync(`${base}-network.json`, JSON.stringify(networkLogs, null, 2), 'utf8');

    // ⑤ Playwright trace（需在 launch() 中预先开启 context.tracing.start）
    let tracePath: string | undefined;
    try {
      const traceOut = `${base}.zip`;
      await session.context.tracing.stop({ path: traceOut });
      tracePath = traceOut;
    } catch {
      // tracing 未开启时忽略
    }

    return { screenshotPath, html, consoleLogs, networkLogs, tracePath };
  }

  // ──────────────────────────────────────────
  // 8. teardown —— 清理会话
  // ──────────────────────────────────────────

  /**
   * 清理会话：关闭浏览器 / 应用进程，并触发测试数据回滚。
   * 应在 afterEach / afterAll 中调用，确保不留残余进程与数据。
   *
   * @param session 由 launch() 返回的 Session
   * @param gateway 可选：数据网关实例（传入则自动调用 rollback）
   * @param seedHandle 可选：seed() 返回的 handle，供 rollback 精确回收
   */
  async teardown(
    session: Session,
    gateway?: DataGateway,
    seedHandle?: SeedHandle,
  ): Promise<void> {
    // 数据回滚（精确回收本用例所造数据，避免污染其他用例）
    if (gateway && seedHandle) {
      await gateway.rollback(seedHandle);
    }

    // 关闭浏览器 / Electron 进程
    try {
      await session.context.close();
    } catch {
      /* 已关闭则忽略 */
    }
    try {
      await session.browser?.close();
    } catch {
      /* Electron 无 browser 对象，忽略 */
    }

    this.session = null;
  }

  // ──────────────────────────────────────────
  // 私有工具
  // ──────────────────────────────────────────

  private _requireSession(): Session {
    if (!this.session) throw new Error('Session 未初始化，请先调用 launch()');
    return this.session;
  }

  private _isSnapshot(target: Locator | Snapshot): target is Snapshot {
    return typeof (target as Snapshot).html === 'string';
  }

  private _assertString(actual: string, expectation: Expectation, label: string): void {
    switch (expectation.type) {
      case 'equals':
        if (actual !== String(expectation.value)) {
          throw new Error(`断言失败（${label} equals）\n期望：${expectation.value}\n实际：${actual}`);
        }
        break;
      case 'contains':
        if (!actual.includes(String(expectation.value))) {
          throw new Error(`断言失败（${label} contains）\n期望包含：${expectation.value}\n实际：${actual}`);
        }
        break;
      case 'matches':
        if (!String(actual).match(expectation.value as RegExp)) {
          throw new Error(`断言失败（${label} matches）\n期望匹配：${expectation.value}\n实际：${actual}`);
        }
        break;
      default:
        throw new Error(`assert 不支持对字符串使用 ${expectation.type} 类型`);
    }
  }
}

// ─────────────────────────────────────────────
// 数据网关契约类型（oracle-and-data.md §4）
// ─────────────────────────────────────────────

/** seed() 返回的句柄，供 rollback 精确回收 */
export interface SeedHandle {
  id: string | number;
  type: string;
  meta?: Record<string, unknown>;
}

/** seed() 的数据规格 */
export interface SeedSpec {
  /** 资源类型，如 'user' / 'order' / 'product' */
  type: string;
  /** 字段值 */
  data: Record<string, unknown>;
}

/** query() 的查询描述符 */
export interface QuerySelector {
  /** 资源类型或 API 路径 */
  type: string;
  /** 过滤条件 */
  filter?: Record<string, unknown>;
}

/** reset() 的作用域 */
export interface ResetScope {
  /** 'all' | 资源类型名 | 表名 */
  target: string;
}

/** 数据网关统一接口（两套实现共享此契约） */
export interface DataGateway {
  seed(spec: SeedSpec): Promise<SeedHandle>;
  query(selector: QuerySelector): Promise<unknown[]>;
  reset(scope: ResetScope): Promise<void>;
  rollback(handle: SeedHandle): Promise<void>;
}

// ─────────────────────────────────────────────
// API 网关实现（黑盒·默认）
// oracle-and-data.md §4 —— gateway = api
// ─────────────────────────────────────────────

/**
 * apiGateway：通过 Playwright request fixture 调后端 seed/query/reset 端点。
 * 适用于后端有 factory / seed API 的项目（默认选择，不耦合表结构）。
 *
 * 落地时替换 API_BASE 为实际后端地址，并按后端路由调整路径。
 */
export function createApiGateway(apiBase: string): DataGateway {
  let apiContext: APIRequestContext | null = null;

  async function getContext(): Promise<APIRequestContext> {
    if (!apiContext) {
      // 复用 Playwright 的 request API，自动处理 cookie/session
      apiContext = await pwRequest.newContext({ baseURL: apiBase });
    }
    return apiContext;
  }

  return {
    /**
     * 走后门造前置数据：POST /test/seed
     * 后端按 spec.type 路由到对应的 factory，返回 { id, type }。
     */
    async seed(spec: SeedSpec): Promise<SeedHandle> {
      const ctx = await getContext();
      const resp = await ctx.post('/test/seed', { data: spec });
      if (!resp.ok()) {
        throw new Error(`apiGateway.seed 失败：${resp.status()} ${await resp.text()}`);
      }
      const body = await resp.json();
      return { id: body.id, type: spec.type, meta: body };
    },

    /**
     * 读持久化状态供断言：GET /test/query?type=...&filter=...
     * 用于持久化预言机③（默认 gateway=api）。
     */
    async query(selector: QuerySelector): Promise<unknown[]> {
      const ctx = await getContext();
      const params = new URLSearchParams({ type: selector.type });
      if (selector.filter) {
        params.set('filter', JSON.stringify(selector.filter));
      }
      const resp = await ctx.get(`/test/query?${params.toString()}`);
      if (!resp.ok()) {
        throw new Error(`apiGateway.query 失败：${resp.status()} ${await resp.text()}`);
      }
      return resp.json();
    },

    /**
     * 复位指定范围数据：POST /test/reset
     * 对应隔离档 app-reset-endpoint（oracle-and-data.md §5）。
     */
    async reset(scope: ResetScope): Promise<void> {
      const ctx = await getContext();
      const resp = await ctx.post('/test/reset', { data: scope });
      if (!resp.ok()) {
        throw new Error(`apiGateway.reset 失败：${resp.status()} ${await resp.text()}`);
      }
    },

    /**
     * 精确回滚本用例所造数据：DELETE /test/seed/:type/:id
     * 避免污染其他用例（teardown 中调用）。
     */
    async rollback(handle: SeedHandle): Promise<void> {
      const ctx = await getContext();
      const resp = await ctx.delete(`/test/seed/${handle.type}/${handle.id}`);
      if (!resp.ok()) {
        // rollback 失败不应掩盖测试结果，记录警告即可
        console.warn(`apiGateway.rollback 失败：${resp.status()}，handle=${JSON.stringify(handle)}`);
      }
    },
  };
}

// ─────────────────────────────────────────────
// DB 网关占位（白盒·兜底）
// oracle-and-data.md §4 —— gateway = db
// ─────────────────────────────────────────────

/**
 * dbGateway：直连测试库，用于 API 观测不到的副作用断言。
 * 适用场景：审计日志 / 软删除标记 / 旁表副作用 / 异步计数器
 * （oracle-and-data.md §2③ 降级条件）。
 *
 * 落地时：
 *   1. 替换此占位为项目实际 ORM / SQL 客户端（Prisma / TypeORM / pg / better-sqlite3 等）。
 *   2. 从环境清单（env-manifest-template.yaml 的 test_db 字段）读取 DSN。
 *   3. 删除 NOT_IMPLEMENTED 抛错，实现各方法体。
 */
export function createDbGateway(): DataGateway {
  // TODO 接项目测试库 DSN（从环境清单 test_db 字段读取，或直接注入 process.env.TEST_DB_DSN）
  // const db = new YourOrmClient(process.env.TEST_DB_DSN);

  function NOT_IMPLEMENTED(method: string): never {
    throw new Error(
      `dbGateway.${method} 未实现——落地时请接入项目 ORM/SQL 客户端并配置 TEST_DB_DSN。`,
    );
  }

  return {
    async seed(_spec: SeedSpec): Promise<SeedHandle> {
      // TODO: 用 ORM/SQL 直插测试数据，返回主键 id
      // 示例（Prisma）：
      //   const record = await db.user.create({ data: _spec.data });
      //   return { id: record.id, type: _spec.type };
      NOT_IMPLEMENTED('seed');
    },

    async query(_selector: QuerySelector): Promise<unknown[]> {
      // TODO: 用 ORM/SQL 直查，返回行数组
      // 示例（Prisma）：
      //   return db[_selector.type].findMany({ where: _selector.filter });
      NOT_IMPLEMENTED('query');
    },

    async reset(_scope: ResetScope): Promise<void> {
      // TODO: truncate 表 / 删命名空间数据
      // 示例（Prisma）：
      //   await db.$executeRawUnsafe(`TRUNCATE TABLE "${_scope.target}" CASCADE`);
      NOT_IMPLEMENTED('reset');
    },

    async rollback(_handle: SeedHandle): Promise<void> {
      // TODO: 按主键精确删除
      // 示例（Prisma）：
      //   await db[_handle.type].delete({ where: { id: _handle.id } });
      NOT_IMPLEMENTED('rollback');
    },
  };
}

// ─────────────────────────────────────────────
// 示范 Spec —— 完整三层断言用例
// 走后门 seed → 走前门 UI 操作 → 三层校验断言
// ─────────────────────────────────────────────

/**
 * @case TC-xxx-001
 *
 * 场景：用户新增订单后，列表展示正确，持久化状态确认。
 *
 * 三层断言：
 *   ① 交互预言机：操作后出现成功 Toast
 *   ② 展示预言机：订单列表中新增行的名称 readDisplay 正确
 *   ③ 持久化预言机：apiGateway.query 返回对应记录（gateway=api 默认）
 *
 * 用法（落地时在 Playwright test 文件中调用此函数，或直接复制改写）：
 *   await runDemoSpec('http://localhost:3000', 'http://localhost:4000');
 */
export async function runDemoSpec(webUrl: string, apiBase: string): Promise<void> {
  const adapter = new PlaywrightAdapter('./test-evidence/TC-xxx-001');
  const gateway = createApiGateway(apiBase);
  let seedHandle: SeedHandle | undefined;
  let session: Session | undefined;

  try {
    // ── Arrange：走后门 seed 前置数据 ──────────────
    // 通过 apiGateway 造一条订单，不经 UI
    seedHandle = await gateway.seed({
      type: 'order',
      data: { productName: '测试商品-TC-xxx-001', quantity: 2, status: 'pending' },
    });

    // ── 起测应用（Web 模式示范；换 Electron 只需 mode: 'electron'）──
    session = await adapter.launch({ mode: 'web', url: webUrl });

    // ── Act：走前门 UI 操作 ─────────────────────────
    // 导航到订单创建页（根据实际路由替换）
    await session.page.goto(`${webUrl}/orders/new`);

    // 定位商品名输入框（优先 role/testId，禁用脆性 CSS）
    const productInput = adapter.locate({ role: 'textbox', name: '商品名称' });
    await adapter.act(productInput, { type: 'fill', value: '前门商品-TC-xxx-001' });

    // 定位数量输入框
    const qtyInput = adapter.locate({ testId: 'order-quantity-input' });
    await adapter.act(qtyInput, { type: 'fill', value: '3' });

    // 点击提交
    const submitBtn = adapter.locate({ role: 'button', name: '提交订单' });
    await adapter.act(submitBtn, { type: 'click' });

    // ── Assert ① 交互预言机：成功 Toast ────────────
    const toast = adapter.locate({ role: 'alert', name: '提交成功' });
    await adapter.assert(toast, { type: 'visible' });

    // ── Assert ② 展示预言机：列表行显示正确商品名 ──
    // 导航到订单列表页
    await session.page.goto(`${webUrl}/orders`);
    const firstRowName = adapter.locate({ testId: 'order-row-product-name-1' });
    const displayedName = await adapter.readDisplay(firstRowName);
    // readDisplay 从 DOM textContent 提取（oracle-and-data.md §3 dom）
    await adapter.assert(firstRowName, { type: 'contains', value: '前门商品' });

    // 附加验证：readDisplay 返回值与期望一致
    if (!displayedName.includes('前门商品')) {
      throw new Error(`展示预言机②断言失败：期望包含"前门商品"，实际：${displayedName}`);
    }

    // ── Assert ③ 持久化预言机：apiGateway.query 确认持久化 ──
    // gateway = api（默认，不耦合表结构；oracle-and-data.md §2③）
    const rows = await gateway.query({
      type: 'order',
      filter: { productName: '前门商品-TC-xxx-001' },
    });
    if (rows.length === 0) {
      throw new Error('持久化预言机③断言失败：apiGateway.query 未返回对应订单记录');
    }

    console.log('[TC-xxx-001] 三层断言全部通过 ✓');
  } catch (err) {
    // 失败时收集完整证据包（截图+console+network+trace）
    if (session) {
      const evidence = await adapter.collectEvidence('TC-xxx-001-fail');
      console.error('[TC-xxx-001] 测试失败，证据包：', evidence.screenshotPath);
    }
    throw err;
  } finally {
    // teardown：关闭会话 + 精确回滚 seed 数据
    if (session) {
      await adapter.teardown(session, gateway, seedHandle);
    }
  }
}
