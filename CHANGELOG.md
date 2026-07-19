# Changelog

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [1.2.0] - 2026-07-19

### Added
- **新技能 `dum-doc-reconcile-domain`（领域模块权威文档生成）**：把 zebook 项目内验证过的
  `dum-doc-reconcile-newest` 通用化收编。维护 `docs/domain-tech-design/` 与
  `docs/domain-product-design/` 两棵按领域模块组织的"现状真相"权威树（`<模块>/<模块>-<子模块>.md`，
  每模块 README 作总入口 + 鲜度总览表）；含三种模式——M（`*-newest` 旧目录一次性迁移：
  `git mv` 改名 + 批量修 related 链接 + 换新脚本）、A（Bootstrap：读全量 dated + 深读现状代码
  合成 v1.0，只写当前生效结论）、B（Incremental：鲜度 🟡 驱动，`git diff` 取证只吸收增量）；
  记账体系为 frontmatter 鲜度头 + 修改记录表 + 四步收尾，报告先行确认后才动正文。
- **打包鲜度脚本**：`skills/dum-doc-reconcile-domain/scripts/` 下 `check_module_freshness.py`
  （扫 domain 树、按 `reconciled-through`/`source.paths` 比对 git 提交与新 dated 快照判 🟢/🟡、
  回写各模块 README 鲜度表；domain→dated 用显式映射表）与 `_freshness_lib.py`（判定纯函数库，
  仅 stdlib + pyyaml）；首次使用复制到目标项目 `scripts/`。
- `docs/原始需求/` 收录《技术方案文档规范》《产品文档规范》，是该技能两套正文骨架的对齐依据。

### Changed
- 根 `CLAUDE.md`（软链 `AGENTS.md`）/`GEMINI.md`/`README.md` 技能清单与衔接说明补入新技能，
  明确与 `dum-doc-reconcile` 按路径分工（domain 树 vs architecture/dated prose）。
- 各 manifest 与 `package.json` 版本 `1.1.9` → `1.2.0`。

## [1.1.9] - 2026-07-02

### Changed
- **`dum-ppt` fintech-dark 章节分隔页标题改为按宽度自动换行**：去掉 8 个分隔页标题
  （`.section-divider .section-h`）里手写的强制 `<br/>`，标题合并为单行源码（连接处
  紧贴、不在中文间留空格），改由容器宽度自然折行；配套给 `.section-divider .section-h`
  加 `text-wrap: balance`，多行时两行长度尽量均衡。承接 1.1.8 的加宽，宽屏下标题可排成
  一行、窄屏自动折成两行，不再写死断点。
- 各 manifest 与 `package.json` 版本 `1.1.8` → `1.1.9`。

## [1.1.8] - 2026-07-02

### Fixed
- **`dum-ppt` fintech-dark 模板章节分隔页宽度修复**：章节分隔页（`.section-divider`）
  的标题/正文列 `max-width` 由 `min(880px, 100%)` 放宽到 `min(1200px, 100%)`，描述段
  `max-width` 由 `640px` 放宽到 `900px`（各 8 处分隔页同步）。此前在宽屏下，巨大的罗马
  数字只占约 380px，右侧留白很多，标题与描述却被窄容器挤得过早换行；放宽后两处文字随
  页面宽度自然折行，不再被约束提前断行。相关 CSS 注释一并更新。

### Changed
- **README「Claude Code 更新」指令简化**：由「`/plugin marketplace update` +
  `/plugin update`」两步（及本地路径装法说明）收敛为一行 `claude plugin update
  dum-agent-skills@dum-skills`。
- 各 manifest 与 `package.json` 版本 `1.1.7` → `1.1.8`（含修正 `gemini-extension.json`
  误写成 `"8"` 为 `"1.1.8"`）。

## [1.1.7] - 2026-06-26

### Added
- **`dum-e2e-test` 增加 Flutter 端适配**：Flutter 从占位升级为 v1 **做实**，主驱动
  `integration_test` + WidgetTester（白盒·进程内）——`locate` 走 Finder（`ValueKey`/
  `Semantics`）、`readDisplay` 直接读 widget 属性做展示预言机，最贴合"界面数据展示"校验。
  新增参考骨架 `assets/flutter-adapter-skeleton.dart`（实现统一 8 方法契约 + `ApiGateway`
  走后门造数）。**数据层差异**：integration_test 跑在设备/模拟器上难直连测试库，故 Flutter
  持久化校验以 **API 黑盒为主**，DB 白盒兜底需宿主侧 runner（`flutter_driver`/
  `appium-flutter-driver`），不在本进程内适配器范围；三层校验的①交互②展示仍完整。
  `references/platform-adapters.md`、`SKILL.md`、README 同步把 Flutter 移出占位（仅
  Android/iOS 仍 `not-implemented`）。

### Changed
- 各 manifest 与 `package.json` 版本 `1.1.6` → `1.1.7`。

## [1.1.6] - 2026-06-26

### Added
- **新增 `dum-e2e-test` 技能**：带后端的前端/客户端端到端测试闭环——按权威阶梯
  (需求>技术方案>代码>用例)从文档派生带溯源的用例 → 生成 Playwright 脚本 → agent
  实测 → 三层校验(交互/界面数据展示/持久化，API 黑盒优先 DB 白盒兜底) → 失败三段
  定责(脚本/用例/代码，并以展示×持久化交叉表分前端/后端) → 仅出修复方案待确认。
  v1：Web/Electron 用 Playwright 做实，Flutter/Android/iOS 留统一驱动契约占位。
  含 SKILL.md + 3 references(定责树/三层校验数据/各端适配) + 4 assets(用例/环境清单/
  报告模板 + Playwright 参考骨架)。

## [1.1.4] - 2026-06-03

### Changed
- **`dum-solution-design` 方案文档落点改为 `docs/tech-design/`**：原约定放项目根的
  `方案设计/`，现统一落进 `dum-knowledge-base-build` 搭好的 `docs/tech-design/`。
  SKILL.md 的文件位置、目录树、Workflow、Quick Reference、常见错误、Red Flags 及
  description 一并同步；README 交付表与衔接说明同步。
- **姊妹技能对齐新落点**：`dum-doc-reconcile`（对账目标）、`dum-session-summary`
  （边界声明里的"不修改的目录"）、`dum-knowledge-base-build`（衔接说明、方案文档
  强制位置示例）中所有 `docs/方案设计/` / `方案设计/` 引用改为 `docs/tech-design/`，
  保证"出方案 → 记录 → 对账"链路指向同一目录。

## [1.1.3] - 2026-05-27

### Changed
- **`dum-session-summary` 不再触发任何文档对账动作**：原工作流第 2 步会主动 grep
  `docs/方案设计/`、`docs/guides/` 等推导"受影响的设计文档（待校对）"并给修改建议，
  现明确删除——本技能只负责把会话改动如实记进 `docs/modify_history/`，不修任何设计
  文档、也不发起 reconcile。模板从 7 节缩到 6 节（去掉「受影响的设计文档（待校对）」
  一节）；Overview 加边界声明；出口判断新增"`docs/architecture/`、`docs/方案设计/`
  下没有任何文件被本次会话总结修改"校验。
- **`dum-doc-reconcile` 对齐新契约**：原依赖 modify_history 里现成的"待校对清单"，
  改为以「改动清单 + 关键决策」+ 同范围 `git diff` 为输入，**自己 grep
  `docs/architecture/` 与 `docs/方案设计/`** 推断哪些文档需要校对。核心原则、Phase 1
  取数步骤、关键逻辑、常见错误一并同步。

## [1.1.2] - 2026-05-26

### Changed
- **`dum-arch-spec-doc` 日志规范模板补完**：原 `go-specification.md` §6 与
  `frontend-specification.md` §10 只有寥寥几行（"用统一 logger / 禁止裸打印"），生成的
  规范文档不够实操。参考 termcat_server / termcat_client 实际约定，按多维度展开：
  - **Go**（5 个子节）：Logger 使用 · 级别(DEBUG/INFO/ERROR + `LOG_LEVEL`) ·
    格式与结构化字段(固定单行格式 + `WithFields`) · 文件与按日轮转(`LOG_DIR` /
    `LOG_RETAIN_DAYS` / `<svc>-YYYY-MM-DD.log`) · 敏感信息脱敏(含 IP 尾段脱敏)
  - **前端**（6 个子节）：Logger 使用(两种调用形式) · 级别(DEBUG/INFO/WARN/ERROR) ·
    事件键命名(`<domain>.<entity>.<action>`) · 模块常量(`LOG_MODULE` 枚举) ·
    文件存储与轮转(按 OS 路径 + 10MB/5 文件) · 敏感信息脱敏(HTTP 拦截器剥离 + 命令脱敏)
  - 全部祈使句 + ✅/❌ 例子，项目特定值保留 `{{...}}` 占位。
  - Python 模板未动（无对应参考），日后按需补齐。

## [1.1.1] - 2026-05-26

### Fixed
- **`docs-index.md` 默认落点改回 `docs/` 根**：原先 `dum-knowledge-base-build` 与
  `dum-arch-spec-doc` 把分类文档索引放到 `docs/reference/docs-index.md`，使用中发现
  它被埋在子目录里、不再像"docs/ 总入口"。现统一为 **`docs/docs-index.md`**；
  `reference/` 分类目录保留，但只承担"参考资料 / 外部链接"角色，不再装索引文件。
  涉及 14 个文件 / 27 处路径 + 2 个脚本常量（`scaffold_docs_structure.py`、
  `update_docs_index.py`）+ 3 棵目录树插图 + 1 处 scaffold 给 reference/ 写的描述。
  - **升级影响**：老项目里 `docs/reference/docs-index.md` 仍可读，新生成的会落到
    `docs/docs-index.md`。若想统一，把老文件 `git mv` 过去再跑一次脚本即可。

### Added
- **各技能的「介绍文档」**（`skills/<name>/README.md`）：人类视角的概览
  （一句话定位 / 它做什么 / 何时触发 / 它交付什么 / 跟其它技能怎么衔接 / 指向 SKILL.md），
  6 个技能各一篇。主 `README.md` 技能一览表加一列「完整工作流」直接指向 `SKILL.md`，
  并在 GitHub 上点进任何 `skills/<name>/` 都会自动渲染对应介绍。

## [1.1.0] - 2026-05-26

### Added
- **新技能 `dum-arch-spec-doc`**：给单个服务按语言（前端 / Go / Python，另带 generic 骨架）
  生成**分离的两份**文档——程序架构文档（`docs/architecture/<service>.md`，描述性）+
  开发规范文档（`docs/specification/<service>-规范.md`，规范性）。
  含 8 个语言模板 + 2 篇 references（架构 vs 规范拆分 taxonomy、各语言章节速查）。

### Changed (Breaking)
- **重命名技能** `dum-architecture-doc-build` → **`dum-knowledge-base-build`**。
  原名"只搭架构文档"太窄，新名更贴合它实际承担的"搭整套知识库框架"职责
  （docs/ 分类目录 + CLAUDE.md 入口 + 文档索引 + PostToolUse hook）。
  - **升级路径**：装了本插件的用户跑 `claude plugin update dum-agent-skills` 后，
    旧名 `dum-architecture-doc-build` 会消失、新名 `dum-knowledge-base-build` 出现；
    任何写死旧名的脚本 / 文档 / 工作流需手动改为新名。
  - 仓库内的交叉引用、`CLAUDE.md` / `README.md` / `GEMINI.md` 索引、
    `dum-session-summary` 等其它 skill 对它的引用、目录内 3 个脚本里的注释，均已同步更新。

### Docs
- `CLAUDE.md` / `README.md` / `GEMINI.md`：技能清单加 `dum-arch-spec-doc` 行；
  「技能相互衔接」段补充与 `dum-knowledge-base-build` 的分工说明。

## [1.0.0] - 2026-05-25

首个正式版多 agent 插件发布。技能集合：
- `dum-architecture-doc-build`（在 1.1.0 重命名为 `dum-knowledge-base-build`）
- `dum-solution-design`
- `dum-doc-reconcile`
- `dum-session-summary`
- `dum-ppt`

打包为 Claude Code / Codex / Gemini CLI / Cursor 四套 manifest，正文集中于 `skills/`。
