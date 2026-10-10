---
name: dum-merge-code
description: "用于安全合并、选择性回补和回滚恢复 Git 代码：核对提交图与最终树，识别旧代码覆盖、merge-only 变更和迁移谱系风险，并在验证后交付。"
---

# 合并代码技能

## 目标

安全整合用户指定的代码，避免源/目标分支搞反、旧代码覆盖新行为，以及“没有冲突但行为已经回退”。目标分支接收改动，源分支提供改动；提交图说明历史关系，最终 tree 才说明实际内容，两者必须同时核对。

## 先判断工作模式

### 普通整合

适用于边界清楚的 `merge`、`rebase` 或 `cherry-pick`。按本文件完成预检、确认、执行和验证。

### 高风险语义恢复

出现以下任一情况时，必须同时阅读并执行 [高风险语义整合与恢复审计](references/high-risk-semantic-recovery.md)：

- 分支含 `revert`、`rollback`、`restore baseline`、整树覆盖或异常大提交。
- 源分支已是目标祖先，但用户仍报告功能缺失；普通 merge 可能显示 `Already up to date`。
- 只恢复指定作者、日期、功能或提交，或明确排除部分历史。
- 要从已发布版本、错误回滚或污染分支中恢复代码。
- 涉及迁移重编号、已上线数据库、生成文件、跨模块依赖或受保护 release 分支。

这类任务先产出“纳入 / 排除 / 保留 / 待确认”清单，再选择直接补丁、文件级恢复或用户指定的 Git 操作。作者和路径只能用于发现候选，不能单独证明代码归属或依赖完整。

## 安全门禁（强制）

1. 源分支、目标分支、操作方式和确认边界未明确前，不得执行改变 Git 状态的操作，包括 `merge`、`rebase`、`cherry-pick`、`reset`、带本地改动的 `checkout/switch`、`stash`、提交、推送和中止操作。
2. 不得把“无文本冲突”“Already up to date”或源分支更新作为行为安全的证据；必须审查计划结果相对目标 tree 的实际变化。
3. 不得把 `ours`/`theirs` 作为批量冲突策略；每个冲突都要按具体操作和行为意图判断。
4. 未经用户明确要求并确认影响，不得 `fetch`、`pull`、强制推送、自动提交或重写共享历史；远端新鲜度未知时必须明确说明。
5. 保留脏工作区和用户已有改动；遇到进行中的 Git 操作、钩子、受保护/共享分支或必须 stash/丢弃时停止询问。
6. 不得用无关修改、整文件格式化、依赖升级或大范围重新生成来解决冲突；生成/锁文件规则不明确时先询问。
7. 作者白名单、直接提交路径并集和最终文件哈希都不能替代来源审计。共享文件要检查逐提交 diff；merge commit 要检查父提交差异、重命名和人工冲突解决。
8. 涉及数据库迁移时，测试可按用户要求不运行，但迁移谱系静态审计不能跳过。已执行迁移不得删除、重编号或用 down migration 回退。
9. 冲突解决后先展示 diff 和验证结果；提交、推送、合并到 release 或发布只有明确属于本次范围时才执行。

## 预检：同时检查提交图和最终树

改变引用、索引或工作区前，冻结并记录源、目标和共同基线的完整 object ID：

```sh
git status --short --branch
git branch --show-current
git branch -vv
git rev-parse <target> <source>
git merge-base <target> <source>
git merge-base --is-ancestor <source> <target>
git merge-base --is-ancestor <target> <source>
git rev-list --left-right --count <target>...<source>
git log --graph --decorate --oneline --all -n 60
git log --first-parent --oneline <base>..<source>
git log --merges --oneline <base>..<source>
git diff --stat <target>...<source>
git diff --name-status --find-renames <target>...<source>
git diff --name-status --find-renames <target> <source>
git worktree list --porcelain
```

三点差异回答“源分支从共同基线新增了什么”，两点差异回答“两个最终 tree 现在实际哪里不同”，不得混用。记录目标/源独有提交、祖先关系、重叠文件、删除/重命名、脏/未跟踪文件、sequencer 状态、所有 worktree/并发修改、上游跟踪和远端新鲜度。提交前和推送前重新解析引用；任一 SHA 变化都停止并重审。

同时检查范围内的 merge、revert 和异常大提交：

```sh
git log --oneline --regexp-ignore-case --grep='revert\|rollback\|restore.*baseline' <base>..<source>
git show --no-patch --format=fuller <suspect-commit>
git show --stat --summary <suspect-commit>
git diff --name-status --find-renames <suspect-commit>^ <suspect-commit>
git merge-base --is-ancestor <suspect-commit> <source>
```

源分支过旧、已分叉、包含大范围回退，或可能撤销目标分支新行为时，不要凭提交时间或冲突数量继续。

## 冻结语义清单并确认

普通整合至少说明：

> 将 `<source>@<sha>` 的 `<N>` 个独有提交整合到 `<target>@<sha>`；共同基线为 `<base>`，目标侧独有 `<M>` 个提交。计划使用 `<operation>`，预计影响 `<files/behaviors>`，明确保留 `<preserve>`，不包含 `<non-goals>`。

高风险恢复还必须列出：

- 需要恢复的业务能力及必要依赖，不只列作者或文件。
- 明确排除的功能、提交和路径。
- 必须保持目标现状的路径/行为。
- merge-only 变更、重命名、迁移和生成物。
- 验收方式、是否运行测试，以及若不运行测试仍会执行的静态门禁。

方向、操作、语义范围、删除、迁移或共享文件决策不明确时，等待人工确认；等待期间不得编辑。

## 执行最小且安全的整合

确认后重新解析源/目标完整 SHA 并检查工作区。任一引用、远端或工作区事实变化时立即停止，展示旧值和新值，重新确认基线。

- 优先执行用户选择的操作，不得静默把 merge 改成 rebase、squash、cherry-pick 或直接文件恢复。
- 记录操作前分支和 `HEAD`；普通 merge 必须在目标分支执行。
- 高风险或共享 release 分支优先在隔离 worktree 中形成候选结果，验证后再由用户决定如何交付。
- 用户选择“历史只读、当前树直接回补”时，历史仅用于 `show`/`diff`/blame；按拓扑顺序应用确认过的补丁，不调用 merge 类命令。
- 整文件恢复仅在能证明当前 preimage、目标行为和来源边界都匹配时使用。共享文件、交叉作者文件或 merge 后文件必须逐块应用，不能拿历史最终 blob 覆盖当前文件。
- 出现意外冲突、文件、删除、依赖或范围外修改时立即停止，不得先解决再汇报。

Squash 只压缩已经审计过的净差异，不能替代来源、语义、迁移或最终 tree 审计；不得用 squash 隐藏漏项或夹带无关历史。

## 按三方语义解决冲突

对每个未合并路径：

1. 用 `git diff --name-only --diff-filter=U` 和 `git ls-files -u` 查看冲突及阶段。
2. 对比共同基线、目标/ours、源/theirs、相关直接提交和 merge commit 父差异。
3. 按确认的业务行为决策，不按“更新的文本”、作者名或提交时间决策。
4. 删除、重命名、API/Schema、迁移、依赖/锁文件、生成文件和测试冲突都要单独确认语义。
5. 每次只暂存已确认路径并检查 cached diff；禁止批量 `add`、`checkout ours/theirs` 或无审计地接受整棵目录。

## Merge-only、删除和依赖闭包审计

逐个检查范围内 merge commit 的两个父差异和重命名；`--remerge-diff` 为空不代表 merge 对最终 tree 没贡献：

```sh
git log --merges --format='%H %P %an %s' <base>..<source>
git diff --name-status --find-renames <merge>^1 <merge>
git diff --name-status --find-renames <merge>^2 <merge>
git show --remerge-diff <merge>
```

按业务能力而不是作者恢复依赖闭包：入口、路由、模型、存储、迁移、配置、客户端、管理端、生成物和测试。共享文件按 hunk 分类；删除单独列清单，默认保留，除非产品/数据语义已确认删除。

## 数据库迁移门禁

只要计划结果增删改迁移，就必须在提交或发布交付前完成：

- 枚举目标、源和候选结果的迁移版本，检查重复、缺口、up/down 配对、重命名及 init schema 一致性。
- 检查后续 repair migration 是否依赖缺失的主迁移；“有修复迁移”不代表基础迁移完整。
- 检查代码和测试是否引用不存在的迁移文件、表、列或配置。
- 若任一版本已部署，取得被授权环境的实际 migration ledger；无法取得时明确阻断发布结论，不能猜测。
- 已执行版本保持不可变；需要兼容修复时只新增向前迁移。重编号必须证明线上未执行，否则停止询问。

```sh
git ls-tree -r --name-only <target> | rg 'migrations?/.*\.(up|down)\.sql$'
git ls-tree -r --name-only <source> | rg 'migrations?/.*\.(up|down)\.sql$'
rg --files | rg 'migrations?/.*\.(up|down)\.sql$'
```

## 完成前验证

- 执行 `git diff --check`，搜索跟踪文本文件中的冲突标记。
- 将最终/cached diff 与“纳入 / 排除 / 保留”清单逐项对照，检查删除、重命名、merge-only 路径和共享文件。
- 验证保留集仍存在且内容未被候选结果改写；验证排除功能没有经依赖文件或 merge commit 夹带。
- 执行变更模块及必要回归路径的针对性测试；只在项目规范或风险要求时扩大到构建、类型检查或 lint。
- 用户明确不运行测试时，记录未验证风险，但仍完成迁移谱系、路径范围、冲突标记和 diff 静态检查。
- 对 `go:embed`、manifest、容器或发布包核对内嵌迁移/脚本/资源和 commit SHA，避免源码正确而产物过旧。
- 正式部署不能只看主进程 `active` 或健康探针；还要确认关键 worker/scheduler 子任务、迁移账本和构建产物身份。
- 确认提交图、`HEAD`、上游 SHA 和工作区状态，确保操作前本地改动未丢失。

测试失败时区分整合错误、语义冲突、既有失败和环境问题；不得用修改无关代码换取全绿。

## 停止与最终报告

无法证明方向、旧代码可能撤销新行为、merge-only 依赖未审清、迁移账本未知、分支在确认后变化、工作区无法保留或出现范围外失败时停止询问，不要猜测。

最终报告源 → 目标、冻结 SHA、共同基线、操作方式、纳入/排除/保留行为、merge-only 与迁移处理、验证结果，以及是否提交、推送、合入 release 或发布。若结果只是候选恢复树，必须明确它尚不代表可发布版本。
