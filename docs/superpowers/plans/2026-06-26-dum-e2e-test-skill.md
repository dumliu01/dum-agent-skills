# dum-e2e-test 技能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增工作流技能 `dum-e2e-test`——把「带后端的前端/客户端端到端测试」做成闭环：依据文档派生用例 → 生成可运行脚本 → agent 实测 → 失败三段定责（脚本/用例/代码）→ 仅出修复方案。

**Architecture:** 这是一个 **markdown 工作流技能**（SKILL.md 指挥 agent 的规则集 + references 方法论 + assets 模板），不是可执行框架，**没有 pytest/单测**。"验收"用结构化校验命令（文件存在、必含章节、Mermaid 配对、跨链解析、JSON 合法、版本一致）。技能落在 `skills/dum-e2e-test/`，各 agent（Claude Code / Codex / Cursor / Gemini）从 `skills/` 自动发现，**无需改 manifest 的技能列表**；只需更新人面向索引表与版本号。

**Tech Stack:** Markdown + YAML frontmatter；Mermaid 画图；Playwright（Web/Electron 实测，复用 `webapp-testing`）；数据访问走 API（黑盒）/ DB（白盒）；移动端 Appium / flutter_driver 仅占位规格。

## Global Constraints

- **技能名（slug）**：`dum-e2e-test`，目录 `skills/dum-e2e-test/`。
- **内容唯一真源**：`docs/tech-design/20260626-E2eTestSkill.md`（已审核通过的方案）。所有 references/assets 的实质内容从该文档对应小节转写，不得新增与方案冲突的设计。
- **房屋风格**：正文中文；工具名用 Claude Code 名（Read/Write/Edit/Bash/Grep/Glob）；图一律 **Mermaid 代码块**（` ```mermaid `），不用 ASCII art / PlantUML。
- **文档/代码分离**：SKILL.md 与 references 不写实现代码（仅签名/schema/伪代码/决策树）；可运行代码骨架只能放 `assets/`，且标注「参考模板，非即用」。
- **v1 平台范围**：Web + Electron **做实**（Playwright）；Flutter / Android / iOS **仅占位规格**，标 `not-implemented`，不在 v1 跑。
- **修复权限**：**仅出方案**——定责后只产「问题归属 + 建议修复」，对脚本/用例/代码的任何实际改动都需用户确认。
- **核心方法论（须贯穿全技能，措辞与方案一致）**：
  - 权威阶梯 **需求 > 技术方案 > 代码 > 用例**（派生与定责共用一套）。
  - 三层校验 **①交互 ②界面数据展示 ③持久化**；持久化 **API 优先(黑盒) + DB 直查兜底(白盒)**；展示值默认 **DOM/语义树结构化提取**，截图仅取证 + 可选视觉回归/OCR 兜底。
  - 走后门布置、走前门操作、双轴（展示×持久化）交叉定位前端/后端。
  - flaky / 环境类前置闸：稳定复现前不进语义定责。
- **版本号**：`1.1.5 → 1.1.6`，须在 6 处一致：`package.json`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`.codex-plugin/plugin.json`、`.cursor-plugin/plugin.json`、`gemini-extension.json`；另 `README.md` 版本行当前是 stale 的 `v1.1.4`，一并改成 `v1.1.6`。
- **落点约定（技能产物，写进 SKILL.md）**：用例 `docs/test-cases/<feature>.md`；脚本 `tests/e2e/<feature>/`；证据包 `tests/e2e/.artifacts/<run>/`；报告 `docs/test-report/YYYYMMDD-<feature>.md`；环境清单项目根或 `docs/test-cases/` 同级。

---

## File Structure

新建技能目录（9 个文件）：

```
skills/dum-e2e-test/
├── SKILL.md                              # agent 视角执行指令（spine，串起 references/assets）
├── README.md                            # 人类视角：它做什么/何时触发/交付什么/衔接/资源
├── references/
│   ├── triage-decision-tree.md          # 三段定责决策树 + 展示×持久化交叉表（可执行 checklist）
│   ├── oracle-and-data.md               # 三层校验 + 走后门 + 数据网关 + 取值方式
│   └── platform-adapters.md             # 各端适配映射（Web/Electron 实，移动端占位规格）
└── assets/
    ├── test-case-template.md            # 用例 schema 模板（§4.1 字段）
    ├── env-manifest-template.yaml        # 环境清单模板（§4.7 字段）
    ├── test-report-template.md          # 运行+定责+提案报告模板（§4.4 字段）
    └── playwright-adapter-skeleton.ts   # Playwright 驱动 + 数据网关 参考骨架（仅 Web/Electron）
```

仓库级人面向更新（不新建文件，只改）：
`CLAUDE.md`（技能清单表 + 衔接段）、`README.md`（技能一览表 + 仓库结构树 + 版本行）、`GEMINI.md`（技能索引表）、`CHANGELOG.md`（新增条目）、6 个 manifest + `package.json`（版本）。

构建顺序：先做叶子（references/assets，可独立 review），再做 SKILL.md（spine，末尾校验所有跨链解析），再 README，最后仓库级 wiring。

---

## Task 1: 三段定责决策树 reference

**Files:**
- Create: `skills/dum-e2e-test/references/triage-decision-tree.md`

**Interfaces:**
- Produces: 供 SKILL.md「三段定责」段引用的 checklist 文件；定义 verdict 取值 `script / test-case / code / flaky / escalate` 与 `layer = frontend / backend / suspect-cache`（被 `assets/test-report-template.md` 的字段复用）。

- [ ] **Step 1: 确认验收点当前失败**

Run: `test -f skills/dum-e2e-test/references/triage-decision-tree.md && echo EXISTS || echo MISSING`
Expected: `MISSING`

- [ ] **Step 2: 写决策树 reference**

转写自方案 §2.2 / §3.3 / §3.9 / §3.10。文件须含且仅含（无实现代码）：

1. 顶部一句话用途 + 「定责前置闸」小节：去抖重跑判 flaky；seed/起环境/脏数据 → 归**环境类**，先修不进语义定责。
2. 一个 Mermaid `flowchart` 决策树（照搬方案 §2.2）：失败 → 是否稳定复现 → 脚本是否忠实复现用例 → 应用行为 vs 用例期望 → 用例期望是否符合更高权威 →（用例问题 / 代码问题 / 升级）。
3. 「展示×持久化交叉表」小节（照搬方案 §3.10 的 2×2 表）：✓/✓ 通过、✗/✓ 前端展示 bug、✓/✗ suspect-cache、✗/✗ 后端 bug；并说明 `verdict=code` 时补 `layer` 子标。
4. 「定责结论字段」小节：列 `case_id / verdict / layer / confidence / evidence / proposal`（与方案 §4.4 一致），强调 `confidence=低` 或 `escalate` 必须请用户裁决。
5. 「仅出方案」边界声明：定责器只写报告、不改任何源文件。

- [ ] **Step 3: 校验结构**

Run（全部应为 OK）：
```bash
f=skills/dum-e2e-test/references/triage-decision-tree.md
test -f "$f" && echo OK-exists
grep -q '```mermaid' "$f" && echo OK-mermaid
python3 -c "import sys;t=open('$f').read();sys.exit(0 if t.count('\`\`\`')%2==0 else 1)" && echo OK-fences-balanced
grep -qE 'flaky|环境类' "$f" && echo OK-pregate
grep -q 'suspect-cache' "$f" && echo OK-crosstable
grep -q 'escalate' "$f" && echo OK-escalate
```
Expected: 6 行 OK-*

- [ ] **Step 4: Commit**

```bash
git add skills/dum-e2e-test/references/triage-decision-tree.md
git commit -m "feat(e2e-test): 三段定责决策树 reference（含展示×持久化交叉表）"
```

---

## Task 2: 三层校验与数据 reference

**Files:**
- Create: `skills/dum-e2e-test/references/oracle-and-data.md`

**Interfaces:**
- Produces: 定义三层预言机与数据网关方法论；为 `assets/test-case-template.md` 的 `expected_interaction / expected_display(source) / expected_data(gateway)` 与 `assets/env-manifest-template.yaml` 提供语义依据。

- [ ] **Step 1: 确认验收点当前失败**

Run: `test -f skills/dum-e2e-test/references/oracle-and-data.md && echo EXISTS || echo MISSING`
Expected: `MISSING`

- [ ] **Step 2: 写 reference**

转写自方案 §3.7 / §3.8 / §3.11 / §4.6 / §4.7。须含小节：

1. **走后门布置、走前门操作、三层校验断言** 总原则（Arrange 用数据网关 / Act 走 UI / Assert 三层）。一个 Mermaid `flowchart`（照搬方案 §1.3 环境与数据子系统图）。
2. **三层预言机**：①交互（toast/跳转/态）②界面数据展示（呈现的数据值）③持久化（API 黑盒优先 / DB 白盒兜底，列何时降级到白盒：审计/软删/旁表/计数器）。
3. **展示值怎么取**（§3.11）：默认结构化提取（DOM/语义树，`textContent/inputValue/单元格/ARIA`）；截图两个角色（永远取证 + 可选视觉回归/OCR 兜底无 DOM 文本渲染）；`source = dom|visual|ocr`。
4. **数据访问网关契约**（§4.6，描述签名非实现）：`seed(spec) / query(selector) / reset(scope) / rollback(handle)`；网关选择 `api`(默认)/`db`(兜底)。
5. **环境与隔离阶梯**（§3.8）：容器化临时栈 > 专用 `*_test` 库 + truncate&seed / 唯一命名空间并行 > app test-only reset 端点；强调「可插拔环境清单」+ 项目就高填。

- [ ] **Step 3: 校验结构**

Run（全部应为 OK）：
```bash
f=skills/dum-e2e-test/references/oracle-and-data.md
test -f "$f" && echo OK-exists
grep -q '```mermaid' "$f" && echo OK-mermaid
python3 -c "import sys;t=open('$f').read();sys.exit(0 if t.count('\`\`\`')%2==0 else 1)" && echo OK-fences
grep -qE '交互' "$f" && grep -qE '展示' "$f" && grep -qE '持久化' "$f" && echo OK-three-oracles
grep -qE 'seed|query|reset|rollback' "$f" && echo OK-gateway
grep -qE 'dom|ocr|visual' "$f" && echo OK-source
```
Expected: 6 行 OK-*

- [ ] **Step 4: Commit**

```bash
git add skills/dum-e2e-test/references/oracle-and-data.md
git commit -m "feat(e2e-test): 三层校验/走后门/数据网关 reference"
```

---

## Task 3: 各端适配映射 reference

**Files:**
- Create: `skills/dum-e2e-test/references/platform-adapters.md`

**Interfaces:**
- Consumes: 无。
- Produces: 统一驱动契约 `launch/locate/act/observe/readDisplay/assert/collectEvidence/teardown`（被 `assets/playwright-adapter-skeleton.ts` 实现）；各端适配映射表（v1 标注哪端实、哪端占位）。

- [ ] **Step 1: 确认验收点当前失败**

Run: `test -f skills/dum-e2e-test/references/platform-adapters.md && echo EXISTS || echo MISSING`
Expected: `MISSING`

- [ ] **Step 2: 写 reference**

转写自方案 §3.5 / §4.3 / §4.5。须含：

1. **统一驱动契约**（§4.3，描述签名非实现）：`launch(target) / locate(query) / act(handle,action) / observe()->snapshot / readDisplay(locator)->string / assert(...) / collectEvidence()->bundle / teardown(session)`；附「主流程只对契约编程，换端=换适配器」。
2. **各端适配映射表**（照搬方案 §4.5，markdown 表）：列 端 / 驱动 / 定位(testid 类比) / 展示取值 / 起测环境 / v1 状态：
   - Web → Playwright / `data-testid` / DOM 提取 / 起前后端 / **实**
   - Electron → Playwright(原生) / 同 Web / DOM 提取 / 起二进制 / **实**
   - Flutter → `integration_test`+WidgetTester(白盒) 或 `flutter_driver`/`appium-flutter-driver`(黑盒) / `ValueKey`+`Semantics` / widget/semantics 树（CustomPaint 退截图+OCR）/ 模拟器+`--dart-define` / 占位
   - Android → Appium(UiAutomator2) / `resource-id`+`content-desc` / 原生树 / 模拟器+装 apk / 占位
   - iOS → Appium(XCUITest) / `accessibilityIdentifier` / 原生树 / 模拟器+装 app / 占位
3. **占位说明**：Flutter render-to-canvas 无 DOM，结构化提取走 widget/semantics 树；移动端原生壳走 Appium 原生树。占位适配器须标 `not-implemented`。

- [ ] **Step 3: 校验结构**

Run（全部应为 OK）：
```bash
f=skills/dum-e2e-test/references/platform-adapters.md
test -f "$f" && echo OK-exists
for k in launch locate observe readDisplay collectEvidence teardown; do grep -q "$k" "$f" && echo "OK-$k"; done
for p in Web Electron Flutter Android iOS; do grep -q "$p" "$f" && echo "OK-$p"; done
grep -q 'not-implemented' "$f" && echo OK-placeholder
```
Expected: OK-exists + 6 契约 + 5 平台 + OK-placeholder

- [ ] **Step 4: Commit**

```bash
git add skills/dum-e2e-test/references/platform-adapters.md
git commit -m "feat(e2e-test): 各端适配映射 + 统一驱动契约 reference"
```

---

## Task 4: 产物模板（用例 / 环境清单 / 报告）

**Files:**
- Create: `skills/dum-e2e-test/assets/test-case-template.md`
- Create: `skills/dum-e2e-test/assets/env-manifest-template.yaml`
- Create: `skills/dum-e2e-test/assets/test-report-template.md`

**Interfaces:**
- Consumes: 字段语义来自 references（Task 1/2）。
- Produces: 三份可复制模板，字段与方案 §4.1 / §4.7 / §4.4 一致。

- [ ] **Step 1: 确认验收点当前失败**

Run: `ls skills/dum-e2e-test/assets/ 2>/dev/null || echo MISSING`
Expected: `MISSING`

- [ ] **Step 2a: 写用例模板** `test-case-template.md`

字段（§4.1）：`id / title / platform / provenance(溯源链接) / preconditions / data_setup(走后门:api|db) / steps / expected_interaction / expected_display(+source=dom|visual|ocr) / expected_data(+gateway=api|db) / cleanup / authority(需求|技术方案|代码) / conflicts`。给一个填好的示例用例（如 `TC-login-001`），溯源指向 `需求:docs/原始需求/xxx.md#章节`。

- [ ] **Step 2b: 写环境清单模板** `env-manifest-template.yaml`

字段（§4.7）：`bring_up`(compose/命令/连URL) / `test_db`(DSN，可空=纯黑盒) / `seed` / `reset_hook`(truncate&seed|test-only端点|容器销毁) / `mocks`(支付/邮件/三方 + 冻结时间/固定随机种子) / `isolation`(ephemeral-container|test-db-reset|app-reset-endpoint) / `parallel`(bool)。每字段带注释说明，给 Web+Postgres 的样例值。

- [ ] **Step 2c: 写报告模板** `test-report-template.md`

结构（§4.4）：每条用例一段——通过/失败 + 证据包路径 + 三层观测（交互/展示/持久化）+ `verdict / layer / confidence / evidence / proposal`；顶部汇总「X 脚本 / Y 用例 / Z 代码（前端/后端）/ flaky / escalate」。强调 proposal 仅文字方案、不含已改动。

- [ ] **Step 3: 校验结构**

Run（全部应为 OK）：
```bash
a=skills/dum-e2e-test/assets
test -f "$a/test-case-template.md" && test -f "$a/env-manifest-template.yaml" && test -f "$a/test-report-template.md" && echo OK-exists
for k in provenance expected_display expected_data data_setup authority; do grep -q "$k" "$a/test-case-template.md" && echo "OK-tc-$k"; done
for k in bring_up test_db reset_hook isolation mocks; do grep -q "$k" "$a/env-manifest-template.yaml" && echo "OK-env-$k"; done
for k in verdict layer confidence proposal; do grep -q "$k" "$a/test-report-template.md" && echo "OK-rp-$k"; done
python3 -c "import yaml;yaml.safe_load(open('$a/env-manifest-template.yaml'))" 2>/dev/null && echo OK-yaml-valid || echo "WARN-yaml(注释/示例可接受,人工确认)"
```
Expected: OK-exists + 5 tc + 5 env + 4 rp（YAML 行非严格门槛）

- [ ] **Step 4: Commit**

```bash
git add skills/dum-e2e-test/assets/test-case-template.md skills/dum-e2e-test/assets/env-manifest-template.yaml skills/dum-e2e-test/assets/test-report-template.md
git commit -m "feat(e2e-test): 用例/环境清单/报告 三份产物模板"
```

---

## Task 5: Playwright 驱动 + 数据网关 参考骨架

**Files:**
- Create: `skills/dum-e2e-test/assets/playwright-adapter-skeleton.ts`

**Interfaces:**
- Consumes: 统一驱动契约（Task 3）+ 数据网关契约（Task 2）。
- Produces: Web/Electron 唯一「做实」端的参考实现骨架（仅 assets，标注非即用）。

- [ ] **Step 1: 确认验收点当前失败**

Run: `test -f skills/dum-e2e-test/assets/playwright-adapter-skeleton.ts && echo EXISTS || echo MISSING`
Expected: `MISSING`

- [ ] **Step 2: 写参考骨架**

顶部注释声明「参考模板，非即用；落地按目标项目调整」。内容：
1. 实现统一驱动契约的 Playwright 适配器骨架：`launch`(chromium / `_electron.launch`)、`locate`(getByRole/getByTestId/getByText)、`act`、`observe`(返回 DOM 快照 + `screenshot`)、`readDisplay`(`locator.textContent()`/`inputValue()`)、`collectEvidence`(截图+console+network+trace)、`teardown`。
2. 数据网关骨架两实现：`apiGateway`（用 Playwright `request` fixture 调后端 seed/query/reset）+ `dbGateway`（占位：注释指明用项目 ORM/SQL 客户端，留 `// TODO 接项目测试库 DSN`）。
3. 一个示范 spec：走后门 seed → UI 操作 → 三层断言（交互 + `readDisplay` 展示 + apiGateway.query 持久化），顶部 `// @case TC-xxx-001`。

> 注：本文件是 assets 参考代码，**不违反**文档/代码分离（分离规则约束 SKILL.md / references，不约束 assets 模板）。

- [ ] **Step 3: 校验结构**

Run（全部应为 OK）：
```bash
f=skills/dum-e2e-test/assets/playwright-adapter-skeleton.ts
test -f "$f" && echo OK-exists
grep -qE '参考模板|非即用' "$f" && echo OK-disclaimer
for k in launch readDisplay collectEvidence apiGateway dbGateway '@case'; do grep -q "$k" "$f" && echo "OK-$k"; done
grep -qiE '_electron|electron' "$f" && echo OK-electron
```
Expected: OK-exists + OK-disclaimer + 6 + OK-electron

- [ ] **Step 4: Commit**

```bash
git add skills/dum-e2e-test/assets/playwright-adapter-skeleton.ts
git commit -m "feat(e2e-test): Playwright 驱动 + 数据网关 参考骨架（Web/Electron）"
```

---

## Task 6: SKILL.md（技能 spine）

**Files:**
- Create: `skills/dum-e2e-test/SKILL.md`

**Interfaces:**
- Consumes: 全部 references（Task 1-3）+ assets（Task 4-5），通过 `references/...` `assets/...` 相对链接引用。
- Produces: agent 触发后读取的执行指令；frontmatter `name: dum-e2e-test` + `description`（含触发词）。

- [ ] **Step 1: 确认验收点当前失败**

Run: `test -f skills/dum-e2e-test/SKILL.md && echo EXISTS || echo MISSING`
Expected: `MISSING`

- [ ] **Step 2: 写 SKILL.md**

结构（对齐 `dum-solution-design/SKILL.md` 的章法）：

1. **Frontmatter**（YAML）：
```yaml
---
name: dum-e2e-test
description: Use when the user asks 给某功能/服务做端到端测试、e2e 测试、UI 自动化测试、生成测试用例并跑、验证带后端的前端/客户端（网页/Electron；Flutter/Android/iOS 占位）行为是否符合需求。能力：按权威阶梯(需求>技术方案>代码>用例)从文档派生用例 → 生成 Playwright 脚本 → agent 实测 → 三层校验(交互/界面数据展示/持久化) → 失败三段定责(脚本/用例/代码，并分前端/后端) → 仅出修复方案需用户确认。Triggers - "做端到端测试"/"写自动化测试"/"e2e 测试"/"生成测试用例并运行"/"验证XX功能数据是否正确"/"UI 自动化"。
---
```
2. **Overview** + 4 阶段流水线一览（派生→生成→实测→定责）+ 一句「v1：Web/Electron 实测，移动端占位；仅出方案」。
3. **When to Use / When NOT to Use** 表（NOT：纯单测/接口测试无 UI、一次性脚本、bug 修复用 systematic-debugging）。
4. **核心原则**：权威阶梯（派生与定责共用）；三层校验；走后门+数据网关；flaky/环境前置闸；仅出方案。每条一句话 + 指到对应 reference（`references/oracle-and-data.md`、`references/triage-decision-tree.md`）。
5. **Workflow（四阶段，编号步骤）**：
   - ① 用例派生：读 需求/技术方案/代码/旧用例 → 阶梯裁决 → 写 `docs/test-cases/`（带溯源 + 冲突报告）→ 列清单请用户确认范围。模板见 `assets/test-case-template.md`。
   - ② 脚本生成：用例→脚本到 `tests/e2e/<feature>/`，按平台选适配器（见 `references/platform-adapters.md`），语义优先定位。骨架见 `assets/playwright-adapter-skeleton.ts`。
   - ③ 实测：按环境清单（`assets/env-manifest-template.yaml`）起前后端、走后门 seed、复用 `webapp-testing` 跑、收证据包、去抖判 flaky。
   - ④ 三段定责 + 提案：按 `references/triage-decision-tree.md` 定责，写 `docs/test-report/`，仅出方案等确认。
6. **Output Specification**：落点表（用例/脚本/证据包/报告/环境清单，照 Global Constraints）。
7. **Quick Reference** 表 + **Common Mistakes** 表 + **Red Flags — STOP**（如：失败没去抖就判代码问题、只断言 UI 不断言持久化、用截图断言数据值、私自改业务代码、移动端当已实现去跑）。
8. **Cross-References**：`webapp-testing`（实测驱动）、`dum-solution-design`（技术方案输入）、`dum-knowledge-base-build`/`dum-arch-spec-doc`（需求/架构输入）、`dum-doc-reconcile`（文档冲突下游）、`dum-session-summary`（修复后记账）、`superpowers:writing-plans`（修复实施）。

- [ ] **Step 3: 校验 frontmatter、章节、跨链解析**

Run（全部应为 OK）：
```bash
f=skills/dum-e2e-test/SKILL.md
test -f "$f" && echo OK-exists
head -1 "$f" | grep -q '^---$' && echo OK-fm-open
grep -q '^name: dum-e2e-test$' "$f" && echo OK-name
grep -q '^description:' "$f" && echo OK-desc
for s in 'When to Use' 'Workflow' 'Quick Reference' 'Red Flags' 'Cross-References'; do grep -q "$s" "$f" && echo "OK-sec:$s"; done
python3 -c "import sys;t=open('$f').read();sys.exit(0 if t.count('\`\`\`')%2==0 else 1)" && echo OK-fences
# 跨链解析：SKILL.md 引用的每个 references/ assets/ 文件都须存在
cd skills/dum-e2e-test && miss=0; for r in $(grep -oE '(references|assets)/[A-Za-z0-9._-]+' SKILL.md | sort -u); do test -f "$r" || { echo "MISSING $r"; miss=1; }; done; [ $miss -eq 0 ] && echo OK-xrefs-resolve
```
Expected: OK-exists / OK-fm-open / OK-name / OK-desc / 5×OK-sec / OK-fences / OK-xrefs-resolve（无 MISSING）

- [ ] **Step 4: Commit**

```bash
git add skills/dum-e2e-test/SKILL.md
git commit -m "feat(e2e-test): SKILL.md 四阶段闭环工作流（派生/生成/实测/定责）"
```

---

## Task 7: 技能 README

**Files:**
- Create: `skills/dum-e2e-test/README.md`

**Interfaces:**
- Consumes: 指向同目录 SKILL.md / references / assets。
- Produces: 人类视角介绍页（被仓库 README 表的技能名链接指向）。

- [ ] **Step 1: 确认验收点当前失败**

Run: `test -f skills/dum-e2e-test/README.md && echo EXISTS || echo MISSING`
Expected: `MISSING`

- [ ] **Step 2: 写 README**

照 `dum-arch-spec-doc/README.md` 章法：**它做什么**（四阶段一句话 + 三层校验/三段定责亮点表）、**何时触发**（✅/❌，❌ 指到 systematic-debugging / 纯单测）、**它交付什么**（用例/脚本/报告落点表）、**跟其它技能怎么衔接**（webapp-testing / solution-design / doc-reconcile / session-summary）、**完整工作流**一句话指到 SKILL.md、**资源**列 references×3 + assets×4。结尾注明 v1 平台范围。

- [ ] **Step 3: 校验**

Run（全部应为 OK）：
```bash
f=skills/dum-e2e-test/README.md
test -f "$f" && echo OK-exists
grep -q 'SKILL.md' "$f" && echo OK-link-skill
grep -qE 'references/|assets/' "$f" && echo OK-link-res
grep -qE 'Web|Electron' "$f" && grep -qE 'Flutter|占位' "$f" && echo OK-scope
```
Expected: 4 行 OK-*

- [ ] **Step 4: Commit**

```bash
git add skills/dum-e2e-test/README.md
git commit -m "docs(e2e-test): 技能 README 介绍页"
```

---

## Task 8: 仓库级 wiring（索引表 + 版本号 + CHANGELOG）

**Files:**
- Modify: `CLAUDE.md`（技能清单表加一行 + 衔接段提一句）
- Modify: `README.md`（技能一览表加一行 + 仓库结构树加目录 + 版本行 `v1.1.4`→`v1.1.6`）
- Modify: `GEMINI.md`（技能索引表加一行）
- Modify: `CHANGELOG.md`（顶部加 `[1.1.6]` 条目）
- Modify: `package.json`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`.codex-plugin/plugin.json`、`.cursor-plugin/plugin.json`、`gemini-extension.json`（`1.1.5`→`1.1.6`）

**Interfaces:**
- Consumes: 技能已存在于 `skills/dum-e2e-test/`（Task 1-7）。
- Produces: 发布就绪状态。

- [ ] **Step 1: 确认验收点当前失败**

Run: `grep -rl 'dum-e2e-test' CLAUDE.md README.md GEMINI.md 2>/dev/null || echo "NOT-LISTED-YET"`
Expected: `NOT-LISTED-YET`

- [ ] **Step 2a: CLAUDE.md** 在技能清单表（6 行那张）后追加一行：
```
| **dum-e2e-test** | 给带后端的前端/客户端做端到端测试：按权威阶梯从文档派生用例→生成 Playwright 脚本→agent 实测→三层校验(交互/界面数据/持久化)→失败三段定责(脚本/用例/代码)→仅出修复方案。触发："做端到端测试"/"e2e"/"UI 自动化测试"/"验证XX数据是否正确" | `skills/dum-e2e-test/SKILL.md` |
```
并在"这几个技能相互衔接"段补一句：`dum-e2e-test` 消费 `dum-solution-design` 的技术方案与需求/架构文档派生用例，复用 `webapp-testing` 实测，定责出的文档冲突回流 `dum-doc-reconcile`、修复后用 `dum-session-summary` 记账。

- [ ] **Step 2b: README.md** 技能一览表追加一行：
```
| [`dum-e2e-test`](skills/dum-e2e-test/README.md) | 给带后端的前端/客户端做端到端测试：文档派生用例 → Playwright 脚本 → agent 实测 → 三层校验 → 三段定责 → 仅出修复方案（Web/Electron 实，移动端占位） | [SKILL.md](skills/dum-e2e-test/SKILL.md) |
```
仓库结构树 `skills/` 下补 `│   └── dum-e2e-test/`（注意调整上一行树枝符号）。版本行 `当前版本 **v1.1.4**` 改为 `当前版本 **v1.1.6**`。

- [ ] **Step 2c: GEMINI.md** 技能索引表追加一行：
```
| **dum-e2e-test** | 给带后端的前端/客户端做端到端测试，文档派生用例→脚本→实测→三段定责→仅出方案；"做端到端测试"/"e2e"/"UI 自动化" | `skills/dum-e2e-test/SKILL.md` |
```

- [ ] **Step 2d: CHANGELOG.md** 在 `# Changelog` 说明段后、`## [1.1.4]` 前插入：
```markdown
## [1.1.6] - 2026-06-26

### Added
- **新增 `dum-e2e-test` 技能**：带后端的前端/客户端端到端测试闭环——按权威阶梯
  (需求>技术方案>代码>用例)从文档派生带溯源的用例 → 生成 Playwright 脚本 → agent
  实测 → 三层校验(交互/界面数据展示/持久化，API 黑盒优先 DB 白盒兜底) → 失败三段
  定责(脚本/用例/代码，并以展示×持久化交叉表分前端/后端) → 仅出修复方案待确认。
  v1：Web/Electron 用 Playwright 做实，Flutter/Android/iOS 留统一驱动契约占位。
  含 SKILL.md + 3 references(定责树/三层校验数据/各端适配) + 4 assets(用例/环境清单/
  报告模板 + Playwright 参考骨架)。
```
（若仓库实际最新条目非 1.1.4 请置于最顶部，保持倒序。）

- [ ] **Step 2e: 版本号** 6 文件 `1.1.5`→`1.1.6`：
```bash
for f in package.json .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json .cursor-plugin/plugin.json gemini-extension.json; do
  python3 - "$f" <<'PY'
import sys,re
p=sys.argv[1]; s=open(p).read()
s=s.replace('"version": "1.1.5"','"version": "1.1.6"')
open(p,'w').write(s)
PY
done
```

- [ ] **Step 3: 校验登记齐全 + JSON 合法 + 版本一致**

Run（全部应为 OK）：
```bash
for f in CLAUDE.md README.md GEMINI.md CHANGELOG.md; do grep -q 'dum-e2e-test' "$f" && echo "OK-listed:$f"; done
for j in package.json .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json .cursor-plugin/plugin.json gemini-extension.json; do python3 -m json.tool "$j" >/dev/null && echo "OK-json:$j"; done
n=$(grep -REho '"version": "1.1.6"' package.json .claude-plugin .codex-plugin .cursor-plugin gemini-extension.json | wc -l | tr -d ' '); echo "version-1.1.6-count=$n (expect 6)"
grep -q 'v1.1.6' README.md && echo OK-readme-ver
! grep -q '1.1.5' package.json && echo OK-no-stale-pkg
```
Expected: 4×OK-listed / 6×OK-json / count=6 / OK-readme-ver / OK-no-stale-pkg

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md README.md GEMINI.md CHANGELOG.md package.json .claude-plugin/ .codex-plugin/ .cursor-plugin/ gemini-extension.json
git commit -m "chore: 注册 dum-e2e-test 技能到各 agent 索引 + 版本 1.1.5→1.1.6"
```

---

## Task 9: 全局自检与冒烟

**Files:** 无新增（只读校验）

- [ ] **Step 1: 技能目录完整性 + 全仓 Mermaid/跨链冒烟**

Run（全部应为 OK）：
```bash
ls skills/dum-e2e-test/SKILL.md skills/dum-e2e-test/README.md \
   skills/dum-e2e-test/references/{triage-decision-tree,oracle-and-data,platform-adapters}.md \
   skills/dum-e2e-test/assets/{test-case-template.md,env-manifest-template.yaml,test-report-template.md,playwright-adapter-skeleton.ts} \
   >/dev/null && echo OK-all-9-files
# 全技能 Mermaid fence 配对
for f in $(find skills/dum-e2e-test -name '*.md'); do python3 -c "import sys;t=open('$f').read();sys.exit(0 if t.count('\`\`\`')%2==0 else 1)" || echo "BAD-fences:$f"; done; echo OK-fences-checked
# frontmatter description 含触发词
grep -q 'Triggers' skills/dum-e2e-test/SKILL.md && echo OK-triggers
```
Expected: OK-all-9-files / OK-fences-checked（无 BAD）/ OK-triggers

- [ ] **Step 2: 对照方案做覆盖自检（人工 checklist）**

逐项确认（对 `docs/tech-design/20260626-E2eTestSkill.md`）：
- [ ] 权威阶梯在「派生」与「定责」两处都出现且一致
- [ ] 三层校验（交互/展示/持久化）齐全；持久化 API 优先 DB 兜底
- [ ] 展示值默认结构化提取、截图仅取证/兜底
- [ ] 三段定责决策树 + 展示×持久化交叉表（分前端/后端）
- [ ] flaky/环境前置闸
- [ ] 走后门 + 数据网关契约
- [ ] 各端适配映射（Web/Electron 实，移动端占位 not-implemented）
- [ ] 仅出方案边界（不私自改业务代码）
- [ ] 落点：用例/脚本/证据包/报告/环境清单

- [ ] **Step 3: 最终确认（无遗漏即结束）**

Run: `git status --porcelain` → Expected: 干净（所有改动已分任务提交）

---

## Self-Review

- **Spec coverage**：方案 5 模块 + §3.7–3.11 + §4.1–4.7 均有任务承载——架构/适配(Task3)、三层校验/数据(Task2)、定责(Task1)、模板/契约(Task4/5)、工作流串联(Task6)、注册(Task8)。需求三条：①派生(Task6 工作流① + 阶梯)②生成(工作流②)③实测+三段定责(工作流③④ + Task1)。
- **Placeholder scan**：每个 doc 任务给了须含小节 + 字段清单 + 可执行校验命令；代码骨架在 assets（Task5）有明确接口点；无 TBD/TODO 占位（assets 骨架内 `// TODO 接 DSN` 是模板留给使用者的填空，非计划占位）。
- **Type consistency**：verdict 取值 `script/test-case/code/flaky/escalate` 与 `layer=frontend/backend/suspect-cache`、网关 `api|db`、展示 `source=dom|visual|ocr`、契约 `launch/locate/act/observe/readDisplay/assert/collectEvidence/teardown` 全计划统一；用例字段在 Task4 与 Task6 引用一致。
