# dum-doc-reconcile-domain 技能设计

日期：2026-07-19 ｜ 状态：已确认

## 1. 背景与目标

zebook-platform 项目内有一份项目级技能 `dum-doc-reconcile-newest`（位于
`zebook-platform/.claude/skills/dum-doc-reconcile-newest/SKILL.md`），维护
`docs/tech-design-newest/` `docs/product-design-newest/` 两棵按模块组织的"现状真相"权威文档树，
配套 `sre/scripts/check_module_freshness.py` + `_freshness_lib.py` 做鲜度标记。

现状问题：
- zebook 的目录已改名为 `docs/domain-tech-design/` / `docs/domain-product-design/`，
  但技能正文与脚本仍写 `*-newest`，已脱节；文档 frontmatter 的 `related` 链接也残留
  `product-design-newest/` 旧路径。
- 该技能是项目级私有的，未收进 dum-agent-skills 插件仓库，无法跨项目复用。

目标：把它**通用化**后收进本插件仓库，命名 `dum-doc-reconcile-domain`，实现**领域模块权威
文档生成**；目录术语统一为 `domain-*-design`，附带一次性迁移指引与打包脚本。

## 2. 决策记录（澄清结论）

| 议题 | 决策 |
|---|---|
| 定位 | 通用化 + 改名：完整继承 Bootstrap / Incremental / 鲜度记账能力，去掉 zebook 专有路径 |
| 目标树 | `docs/domain-tech-design/`、`docs/domain-product-design/`；dated 历史树仍是 `docs/tech-design/` `docs/product-design/` 不变 |
| 脚本 | 随技能打包在 `skills/dum-doc-reconcile-domain/scripts/`，使用时复制到目标项目 `scripts/`（同 dum-knowledge-base-build 惯例） |
| 迁移 | SKILL.md 带一节「从 *-newest 迁移」，首次在已有 `-newest` 树的项目触发时先走迁移 |
| 结构 | 单文件 SKILL.md（约 250 行）+ scripts/，不建 references/（规约全量生效，无按需查阅内容） |

## 3. 技能定位与边界

**四棵树模型**：`docs/tech-design/` `docs/product-design/` 是**带日期的历史快照堆**（一次决策
的存档）；`docs/domain-tech-design/` `docs/domain-product-design/` 是与之 1:1 对照的**无日期、
按领域模块、现状真相**的权威树。想知道某模块"现在是什么样"只看 domain 树，dated 树只在追溯
"当时为何这么决定"时翻。

**组织形式**：`docs/domain-<type>-design/<模块>/<模块>-<子模块>.md`（子模块粒度），每个模块
目录一份 `README.md` 作为现状总入口 + 鲜度总览表（表由脚本自动回写，不手写）。

**分工链**：`dum-session-summary` 如实记录改动（不预判文档过时）→ `check_module_freshness.py`
判 🟢/🟡 状态 → 本技能真正把内容改对（合成首份 / 吸收增量）。

**与 `dum-doc-reconcile` 的边界**：目标文件在 `domain-*-design/` 下 → 本技能；目标是
`docs/architecture/` 或 dated 方案的 prose 漂移 → `dum-doc-reconcile`。判据看路径。
二者记账体系不同（本技能：frontmatter 鲜度头 + 修改记录表 + README 鲜度表；
`dum-doc-reconcile`：单行校对水印），不混用。

## 4. 记账约定（沿用参考技能，术语换 domain-*）

- **frontmatter 鲜度头**十字段不变：`module / submodule / type / status / last-reconciled /
  reconciled-through / covers / source(services+paths) / supersedes / related`。
  `related` 链接统一用 `domain-product-design/...` 等新术语；`supersedes` 指向 dated 树路径。
- **修改记录表**：正文第一块，`版本|日期|修改者|修改点`，每次 Bootstrap/Incremental 追加一行。
- **四步收尾**：改正文 → 追加修改记录行 → 同步 frontmatter（`last-reconciled` /
  `reconciled-through` / `supersedes`）→ 跑 `python3 scripts/check_module_freshness.py
  --module <模块>` 确认转 🟢。三处记账一次同步，缺一不可。
- **正文骨架**两套内嵌 SKILL.md，对齐 `docs/原始需求/` 的《技术方案文档规范》《产品文档规范》：
  - 方案（domain-tech-design）：修改记录 / 1 背景介绍 / 2 架构设计与模块设计 / 3 核心业务流程 /
    4 重点（难点）问题解决 / 5 关键接口和数据 / 6 疑问与遗留 / 决策追溯（附加）。
  - 需求（domain-product-design）：修改记录 / 1 背景介绍 / 2 设计思路 / 3 功能点 /
    4 产品体验流程故事（角色定义 + 场景故事）/ 需求演进追溯（附加）。
- **内容与排版规约**全部保留：逐节实写不占位、代码溯源宁瘦勿假（绝不虚构、不谎称"据代码核实"）、
  难点「问题→方案→取舍」四段式、参数/接口/字段入表、代码锚点收段末、考证类元注记不内联
  （差异归决策追溯「与旧文档差异」表、未核实项归 §6 遗留）、产品角色按"谁操作"定义
  （单人功能 1 角色，多人协作才多角色）。红旗与出口判断清单同步保留并改术语。

## 5. 工作流

SKILL.md 按此顺序组织：

**前置 · 安装检查**：目标项目 `scripts/` 下无 `check_module_freshness.py` /
`_freshness_lib.py` 时，从技能包 `scripts/` 复制过去。

**模式 M · 迁移（一次性）**：检测到项目存在 `docs/tech-design-newest/` 或
`docs/product-design-newest/` 时先走这步：
1. `git mv` 目录改名为 `docs/domain-tech-design/` / `docs/domain-product-design/`。
2. 批量修正文档 frontmatter 里指向 `*-newest/` 的 `related` 链接（`supersedes` 指向 dated 树，
   不受影响，但也顺手核查）。
3. 提示删除/替换项目里扫 `*-newest` 的旧鲜度脚本（如 zebook 的 `sre/scripts/` 那份），
   换装本技能打包的新脚本。
4. 跑一遍新脚本，确认各文档鲜度状态与迁移前一致。
迁移完成后才进入 A/B。

**模式 A · Bootstrap（建首份）**：模块在 domain 树下无对应文档时触发。
输入：该模块全量 dated 快照（越新越权威）+ 深读现状代码（骨架第 2/3/5 节的厚度靠读代码补齐，
不靠润色 dated 文字）+ `docs/architecture/<service>.md`（链接用）。
产出 v1.0：骨架填满 + 修改记录首行 + frontmatter（`supersedes` 列全量收口的 dated 路径）。
只写**当前生效**的结论，被后续方案推翻的留在 dated 树。**合成报告先行**，停下等确认，
确认后落盘 + 四步收尾。

**模式 B · Incremental（增量校对）**：由脚本 🟡 标记驱动。
取证：`git diff <reconciled-through>..HEAD -- <source.paths>` + 晚于 `last-reconciled` 的
新 dated 快照 + 同期 `docs/modify_history/` 记录。
只吸收增量、不整篇重写；**漂移报告先行**（逐条"文档现述 vs 当前事实"），确认后改 + 四步收尾。

## 6. 脚本通用化

`skills/dum-doc-reconcile-domain/scripts/` 两个文件，源自 zebook `sre/scripts/`：

- **`check_module_freshness.py`**：
  - 扫描目录 `["tech-design-newest", "product-design-newest"]` →
    `["domain-tech-design", "domain-product-design"]`。
  - domain 树 → dated 树的映射改为显式映射表：`domain-tech-design → tech-design`、
    `domain-product-design → product-design`（原实现是 `.replace("-newest", "")` 后缀剥离）。
  - CLI 不变：`--docs-root docs --repo . [--module X] [--fail-on-stale]`。
  - 回写各模块 README `<!-- FRESHNESS:START/END -->` 区的行为不变。
  - docstring 中技能名改为 `dum-doc-reconcile-domain`。
- **`_freshness_lib.py`**：原样收入（不含目录名硬编码）。

验证方式：临时目录造最小 docs 树（domain 文档 + dated 快照 + git 仓库）跑脚本，
确认 🟢/🟡 判定与 README 回写正确；不引入测试框架。

## 7. 仓库集成

- 新目录 `skills/dum-doc-reconcile-domain/`：`SKILL.md` + `README.md`（简介+入口）+
  `scripts/` 两脚本。
- 根 `CLAUDE.md`：技能清单表加一行；"技能相互衔接"段落补它的位置（`dum-session-summary`
  下游、与 `dum-doc-reconcile` 按路径分工）。`AGENTS.md` 同步镜像（两文件除首行外保持一致）。
- `GEMINI.md`、根 `README.md` 对应更新。
- `CHANGELOG.md` 新增 `[1.2.0]`（新技能 = minor）；`.claude-plugin/plugin.json`、
  `.codex-plugin/plugin.json`、`.cursor-plugin/plugin.json`、`gemini-extension.json`、
  `package.json` 版本 `1.1.9 → 1.2.0`。
- `docs/原始需求/技术方案文档规范.md`、`产品文档规范.md`（当前未跟踪）随本次一并提交。

## 8. 范围外

- 不动 zebook 仓库；其存量尾巴（related 旧链接、旧脚本）由技能的迁移模式在该项目被触发时处理。
- 不建 `references/`；不引入测试框架。
- `dum-doc-reconcile` 本体不改（边界描述已在其正文，若与新技能表述冲突再另行对齐）。
