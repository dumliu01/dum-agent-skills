# 端到端测试报告模板

> 复制此文件到 `docs/test-report/YYYYMMDD-<feature>.md`，每次运行一份报告。  
> 字段定义来源：方案 §4.4 + references/triage-decision-tree.md。  
> **重要**：`proposal` 字段**仅文字修复方案，不含任何已改动的代码或文件**；实际改动等用户确认后再执行。

---

## 顶部汇总

**功能模块**: <feature 名称，如「用户登录」>  
**运行时间**: YYYY-MM-DD HH:MM  
**脚本目录**: `tests/e2e/<feature>/`  
**证据包目录**: `tests/e2e/.artifacts/<run-id>/`  
**环境清单**: 项目根 或 `docs/test-cases/` 同级（如 `env-manifest.yaml`）

| 类别 | 数量 | 备注 |
|---|---|---|
| 脚本问题（`verdict=script`） | X | 选择器 / 步骤 / 断言编写错误 |
| 用例问题（`verdict=test-case`） | Y | 期望与更高权威矛盾，需改用例 |
| 代码问题（`verdict=code`） | Z 前端 / Z 后端 | 应用行为违背需求或技术方案 |
| 不稳定 / 环境类（`verdict=flaky`） | N | 间歇失败或 seed / 环境残留 |
| 需升级裁决（`verdict=escalate`） | M | 权威互相矛盾，超出定责权威 |
| **总用例数** | **T** | 通过 P / 失败 F |

> **阅读提示**：  
> - `verdict=code` 时**必有** `layer` 子标（`frontend` / `backend` / `suspect-cache`），指向开发改动方向。  
> - `confidence=低` 或 `verdict=escalate` 时需用户裁决，勿自行修改。  
> - 证据包含截图 / DOM 快照 / 控制台日志 / 网络日志 / trace，路径见各条目 `evidence` 字段。

---

## 用例结果详情

每条用例一段，按「通过 → 失败（脚本）→ 失败（用例）→ 失败（代码）→ flaky → escalate」顺序排列。

---

### TC-FEATURE-001 ✅ 通过

**title**: <用例标题>  
**platform**: web  
**运行次数**: 1

**三层观测**:

| 层 | 结果 | 观测值 |
|---|---|---|
| 交互 | ✅ 通过 | toast「操作成功」出现，页面跳转至 `/dashboard` |
| 界面数据展示 | ✅ 通过 | 列表首行显示新增记录，标题字段值匹配「测试标题-abc123」（source=dom） |
| 持久化 | ✅ 通过 | `GET /api/items/abc123` 返回 200，title 字段值一致（gateway=api） |

**证据包**: `tests/e2e/.artifacts/<run-id>/TC-FEATURE-001/`

---

### TC-FEATURE-002 ❌ 失败

**title**: <用例标题>  
**platform**: web  
**运行次数**: 3（去抖重跑，每次均失败 → 稳定失败，进入语义定责）

**三层观测**:

| 层 | 结果 | 观测值 | 期望值 |
|---|---|---|---|
| 交互 | ✅ 通过 | toast「保存成功」出现，无跳转 | — |
| 界面数据展示 | ❌ 失败 | 列表行金额显示「0.00」（source=dom） | 「¥128.00」 |
| 持久化 | ✅ 通过 | `GET /api/orders/xyz` 返回 amount=12800（分），折算 ¥128.00（gateway=api） | — |

**定责结论**:

```
verdict:    code
layer:      frontend
confidence: 高
evidence:   tests/e2e/.artifacts/<run-id>/TC-FEATURE-002/screenshot-assert.png
            DOM 快照: tests/e2e/.artifacts/<run-id>/TC-FEATURE-002/dom-snapshot.html
            三层对照:
              交互    ✅ toast 正常
              展示    ❌ 金额渲染为「0.00」，DOM textContent = "0.00"
              持久化  ✅ API 返回 amount=12800 正确
            权威对照: 需求 docs/原始需求/订单.md#金额显示 要求以元展示两位小数
            交叉表定位: 展示✗ × 持久化✓ → 前端展示 bug（渲染/格式化错误）
proposal:   前端订单列表金额渲染函数未将「分」转换为「元」，建议检查
            src/components/OrderList/AmountCell 中的格式化逻辑（cents÷100，
            保留两位小数，加「¥」前缀）；不影响后端存储，仅前端展示层修复。
            【注：以上为文字方案，不含已改动代码，等用户确认后再执行修改】
```

---

### TC-FEATURE-003 ❌ 失败

**title**: <用例标题>  
**platform**: web  
**运行次数**: 1

**三层观测**:

| 层 | 结果 | 观测值 | 期望值 |
|---|---|---|---|
| 交互 | ❌ 失败 | 无 toast，脚本等待 `role=alert` 超时 | toast「提交成功」 |
| 界面数据展示 | 未执行 | — | — |
| 持久化 | 未执行 | — | — |

**定责结论**:

```
verdict:    script
layer:      —
confidence: 高
evidence:   tests/e2e/.artifacts/<run-id>/TC-FEATURE-003/screenshot-timeout.png
            控制台日志: tests/e2e/.artifacts/<run-id>/TC-FEATURE-003/console.log
            关键观察: page.getByRole('alert') 等待超时 5000ms；
                      截图显示 toast 实际已出现但使用了 class=.toast-msg 而非 role=alert
proposal:   脚本断言选择器写错——应改为 page.locator('[data-testid="toast"]')
            或按可访问属性定位；被测元素无 role=alert，建议同步在被测代码补
            aria-role="alert"（作为建议，不私自改业务代码）。
            【注：以上为文字方案，不含已改动代码，等用户确认后再执行修改】
```

---

### TC-FEATURE-004 ❌ 失败

**title**: <用例标题>  
**platform**: web  
**运行次数**: 3（去抖重跑）

**三层观测**:

| 层 | 结果 | 观测值 | 期望值 |
|---|---|---|---|
| 交互 | ✅ 通过 | 成功 toast，页面跳转 | — |
| 界面数据展示 | ✅ 通过 | 列表正确渲染新记录（source=dom） | — |
| 持久化 | ❌ 失败 | `GET /api/items/new-id` 返回 200，但 status 字段值为 `draft`（gateway=api） | status=`active` |

**定责结论**:

```
verdict:    test-case
layer:      —
confidence: 中
evidence:   tests/e2e/.artifacts/<run-id>/TC-FEATURE-004/
            三层对照:
              交互    ✅
              展示    ✅
              持久化  ❌ status=draft，期望 status=active
            权威对照: 技术方案 docs/tech-design/xxx.md#状态机 规定「新建记录默认
                      status=draft，需显式激活操作后变 active」；
                      用例期望「提交即 active」与技术方案矛盾
            阶梯裁决: 技术方案 > 用例，用例期望有误
proposal:   用例 TC-FEATURE-004 的 expected_data.status 应改为 draft，对齐技术方案
            §状态机 的默认状态规定；或确认需求文档是否要求提交后自动激活（如需求高于
            技术方案，则应修技术方案，不应改用例）。建议先确认权威来源再修改。
            【注：以上为文字方案，不含已改动代码或文件，等用户确认后再执行修改】
```

---

### TC-FEATURE-005 ⚠️ Flaky（不稳定）

**title**: <用例标题>  
**platform**: web  
**运行次数**: 3（1 次通过 / 2 次失败 → 间歇失败）

**三层观测**:

```
失败时表现: 提交按钮点击后，断言 toast 出现超时（2/3 次）；通过时 toast 正常出现（1/3 次）
推断原因:   提交按钮点击后有异步请求，脚本未等待网络响应即开始断言 toast
```

**定责结论**:

```
verdict:    flaky
layer:      —
confidence: 中
evidence:   tests/e2e/.artifacts/<run-id>/TC-FEATURE-005/
            运行 1: 通过（截图 pass-1.png）
            运行 2: 失败，toast 等待超时（截图 fail-2.png）
            运行 3: 失败，toast 等待超时（截图 fail-3.png）
proposal:   等待策略不足——建议脚本在点击提交后先等待网络请求完成（如
            waitForResponse('/api/submit')），再断言 toast；
            或使用更宽松的 timeout（当前 3000ms，建议提至 8000ms）。
            如多次调整后仍间歇失败，排查数据隔离（是否存在跨用例残留数据导致请求慢）。
            【注：以上为文字方案，不含已改动代码，等用户确认后再执行修改】
```

---

### TC-FEATURE-006 🚨 升级裁决（escalate）

**title**: <用例标题>  
**platform**: web  
**运行次数**: 3（稳定失败）

**三层观测**:

| 层 | 结果 | 观测值 | 期望值 |
|---|---|---|---|
| 交互 | ✅ 通过 | — | — |
| 界面数据展示 | ❌ 失败 | 显示「审批中」 | 「已完成」 |
| 持久化 | ❌ 失败 | status=pending（gateway=api） | status=completed |

**定责结论**:

```
verdict:    escalate
layer:      —
confidence: 低
evidence:   tests/e2e/.artifacts/<run-id>/TC-FEATURE-006/
            矛盾点:
              需求 docs/原始需求/审批.md#完成条件 规定「三方签字后即为 completed」
              技术方案 docs/tech-design/xxx.md#状态机 规定「须经后台人工审核，才能
              变为 completed」
              两者不一致：需求说自动完成，技术方案说需人工；用例无法裁定以哪个为准
proposal:   当前需求与技术方案在「审批完成条件」上存在矛盾，超出本技能定责权威。
            建议：
            1. 将矛盾点提交 dum-doc-reconcile 进行文档对账
            2. 或由产品/开发确认以哪份文档为准后，再更新另一份并重新派生用例
            在矛盾解决前，本用例结论暂挂起，不计入代码/用例问题统计。
            【需用户裁决：请确认以需求还是技术方案为准】
```

---

## 附：定责字段速查

| 字段 | 取值范围 | 说明 |
|---|---|---|
| `verdict` | `script` / `test-case` / `code` / `flaky` / `escalate` | 定责类别 |
| `layer` | `frontend` / `backend` / `suspect-cache` | 仅 `verdict=code` 时填写 |
| `confidence` | `高` / `中` / `低` | 低时必须请用户裁决 |
| `evidence` | 路径 + 关键观察 | 证据包路径 + 三层观测摘要 + 权威对照 |
| `proposal` | 文字方案 | 仅文字描述，**不含已改动代码或文件**，等用户确认后执行 |

**展示×持久化交叉表（verdict=code 时定 layer）**：

| 界面数据展示 | 持久化 | layer |
|---|---|---|
| ✅ | ✅ | — 通过 |
| ❌ | ✅ | `frontend`（渲染 / 绑定 / 格式化 bug） |
| ✅ | ❌ | `suspect-cache`（乐观更新或缓存掩盖持久化错误） |
| ❌ | ❌ | `backend`（持久化 bug 传导到界面） |
