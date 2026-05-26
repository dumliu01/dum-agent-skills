# {{服务名}} — 开发规范

> 📏 本文档是**写代码必须遵守的约定**（规范性）。系统结构见 [`../architecture/{{service}}.md`](../architecture/{{service}}.md)。
> 🤖 项目入口：[`../../CLAUDE.md`](../../CLAUDE.md)
>
> 每条规范用祈使句（必须/禁止/应该）+ ✅Good / ❌Bad 例子。下方为模板，**请替换成本项目实际约定**。

---

## 1. 命名规范

| 对象 | 约定 | 例 |
|---|---|---|
| 组件文件 | {{PascalCase.tsx}} | `UserCard.tsx` |
| 普通模块 | {{camelCase.ts}} | `hostService.ts` |
| Hook | {{use 前缀 camelCase}} | `useAuth.ts` |
| 类型/接口 | {{PascalCase，不加 I 前缀 / 加 I 前缀}} | `SSHConfig` |
| 常量 | {{UPPER_SNAKE_CASE}} | `MAX_RETRY` |
| CSS 类 | {{kebab-case / CSS Modules}} | `.user-card` |

---

## 2. 注释语言

- {{**所有代码注释必须使用英文**}}（行内、块、JSDoc/TSDoc、TODO/FIXME）。
- commit message {{使用英文}}。
- `.md` 文档{{不受限，可中文}}。

```typescript
// ✅ Good — English, explains WHY
// Retry connection because the host may still be booting
const ws = new WebSocket(url);

// ❌ Bad
// 初始化连接
const ws = new WebSocket(url);
```

---

## 3. 组件编写规范

- {{一律用函数组件 + Hooks，禁止 class 组件}}。
- props {{必须有类型；超过 N 个或含分支语义时考虑拆组件}}。
- {{副作用放 useEffect / 不在渲染期触发；列表必须有稳定 key}}。
- {{弹窗/非首屏视图组件必须懒加载——见 §8}}。

---

## 4. TypeScript 类型规范

- {{禁止 `any`；不得已用 `unknown` + 收窄}}。
- {{仅类型引用必须 `import type`（避免把运行时模块拉进包）}}。
- {{与后端交互的 DTO 类型集中在 `types/`，不散落组件内}}。

```typescript
// ✅ import type { AIAgentConnection } from '../modules/ai-agent';
// ❌ import { AIAgentConnection } from '../modules/ai-agent';  // 把整个模块拉进主包
```

---

## 5. 状态管理规范

- {{全局状态只放确需跨组件共享的；组件局部状态用 useState/ref}}。
- {{store 更新必须不可变；禁止直接 mutate}}。
- {{派生数据用 selector/computed，不要冗余存储}}。

---

## 6. 样式规范

- {{用 {{CSS Modules / Tailwind}}；禁止内联魔法数值}}。
- {{颜色/间距/圆角必须用主题变量，不硬编码}}。
- {{响应式断点统一从 {{constants}} 取}}。

---

## 7. API 调用规范

- {{所有后端调用必须走统一封装 `api('/module/action', params)`，禁止散落 fetch/axios}}。
- {{错误处理统一在封装层；调用方只处理业务 code}}。

```typescript
// ✅ const data = await api('/host/list', { page: 1 });
// ❌ const r = await fetch('/api/v1/host/list', { ... });  // 绕过封装
```

---

## 8. 性能规范（前端重头，按项目实际填）

### 8.1 Bundle 分包

- {{新增 >30KB 第三方依赖时，必须在 `manualChunks` 分配独立 chunk}}。

### 8.2 懒加载边界

- {{弹窗类组件（Modal/Dialog）必须懒加载}}。
- {{非首屏视图必须懒加载}}。
- {{以下模块已配懒加载，禁止改为静态导入：{{列模块}}}}。

### 8.3 模块隔离

- {{宿主代码禁止直接 import 插件/重型模块，只从 `events.ts`/`import type` 引用}}（防止破坏懒加载）。

---

## 9. 国际化规范

- {{所有用户可见文案必须走 `t.xxx`，禁止硬编码字符串}}。
- {{新增文案同时加 `locales/zh.*` 和 `locales/en.*`，键名 {{命名约定}}}}。

---

## 10. 日志规范

- {{用统一 logger，禁止裸 `console.log` 进生产}}。
- {{级别：{{debug/info/warn/error 各用于什么}}}}。
- {{禁止打印 token / 密码 / 凭证等敏感信息}}。

---

## 11. 提交规范

- {{commit message 用英文，格式 `<type>: <subject>`（feat/fix/refactor/docs/...）}}。
- {{一次提交聚焦一件事}}。

---

## 12. 开发速查

| 场景 | 改哪些文件 |
|------|-----------|
| 新增页面视图 | {{...}} |
| 新增 API 调用 | {{services/ 用 api() 封装}} |
| 新增翻译键 | {{locales/zh + en + 组件 t.xxx}} |
| 新增弹窗组件 | {{建组件 + 懒加载注册}} |
| 新增全局状态 | {{...}} |
