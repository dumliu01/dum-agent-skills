# 高风险语义整合与恢复审计

本参考用于回滚污染、整树覆盖、选择性回补、已发布迁移或“提交已合入但功能仍缺失”等高风险场景。它补充 `SKILL.md`，不改变用户对 merge、直接恢复、测试、提交或推送的授权边界。

## 1. 先定义四类集合

在编辑前创建审计清单，每个业务能力、提交或路径只能进入一个明确状态：

| 状态 | 含义 |
|---|---|
| 纳入 | 本次必须恢复的行为及其必要依赖 |
| 排除 | 明确不能进入结果的行为、提交或路径 |
| 保留 | 目标分支已有且不得被改写的行为或文件 |
| 待确认 | 无法仅凭历史、代码和测试判断的产品或数据决策 |

清单至少记录：业务能力、来源提交、父提交、作者、直接路径、共享路径、merge-only 路径、重命名、迁移、依赖、验收方式。作者用于定位提交，不是代码归属证明。

## 2. 冻结证据边界

记录完整 SHA，而不是只写分支名：

- 目标起点 `T`
- 源分支顶端 `S`
- 共同基线 `B`
- 已部署提交 `P`（若适用）
- 已知错误提交集合 `K`

远端新鲜度未知时明确标注；若用户授权 fetch，fetch 后重新冻结。编辑前、提交前、推送前都重新解析这些引用。任何值变化都停止并重审，不把旧审计机械套到新 tree。

## 3. 提交图和最终 tree 分开审计

提交图用于回答“某提交是否可达”，tree 用于回答“代码现在是什么”。至少同时查看：

```sh
git rev-list --left-right --count T...S
git log --graph --decorate --oneline B..S
git diff --name-status --find-renames T...S
git diff --name-status --find-renames T S
```

典型陷阱：源分支已经是目标祖先，普通 merge 返回 `Already up to date`；但目标后续的 revert 已经从 tree 中删除了源分支功能。此时不能继续做普通 merge，需要从历史恢复语义补丁。

## 4. 审计 revert、整树覆盖和异常大提交

对范围内每个可疑提交检查父提交、统计和路径分布：

```sh
git show --no-patch --format=fuller <commit>
git show --stat --summary <commit>
git diff --name-status --find-renames <commit>^ <commit>
git merge-base --is-ancestor <commit> S
```

提交名只是线索。判断它是正常反向补丁、历史 tree 替换还是混合提交，要以父 tree 到提交 tree 的实际差异为准。异常大的增删、跨多个无关服务的回退和大量文件复活/删除必须进入人工确认门禁。

## 5. 不得漏掉 merge-only 变更

“直接功能提交的路径并集”是不完整的恢复边界。merge commit 可能承载：

- 冲突解决后的新逻辑。
- 迁移、文件或 API 的重命名/重编号。
- 两个父分支都不存在的手工适配。
- 为消除重复编号或依赖冲突而产生的删除与新增。

逐个检查范围内 merge commit：

```sh
git log --merges --format='%H %P %an %s' B..S
git diff --name-status --find-renames <merge>^1 <merge>
git diff --name-status --find-renames <merge>^2 <merge>
git show --remerge-diff <merge>
```

`--remerge-diff` 为空不代表 merge 对最终 tree 没贡献；仍要检查父差异和重命名。merge 作者也不代表所有合入代码的作者。排除整个 merge 之前，必须把其中必要的 merge-only 结果显式加入清单。

## 6. 选择性回补的安全方法

1. 按业务能力确定依赖闭包：入口、路由、模型、存储、迁移、配置、客户端、管理端、生成物和测试。
2. 按拓扑顺序读取直接提交补丁；同一文件被多类功能修改时按 hunk 分类。
3. 新文件可以从确认来源创建，但要检查它是否只在 merge 后才使用最终名称。
4. 修改文件优先应用该提交的净 hunk。只有当前文件等于可信 preimage，且历史最终 blob 不含其它范围时，才可整文件恢复。
5. 对删除单独建清单。默认保留并不等于删除无效；默认执行删除也不等于忠实恢复，必须由产品/数据语义决定。
6. 生成候选树后反向验证：每个纳入能力都有完整依赖，每个排除能力没有夹带，每个保留路径仍与目标起点一致。

当用户明确要求历史只读时，不使用 merge、cherry-pick、rebase 或 checkout 恢复；`git show`/`git diff` 只提供证据，实际通过受控补丁或文件编辑形成新提交。

## 7. 迁移谱系审计

对每个包含迁移的服务分别列出 `T`、`S` 和候选结果：

```sh
git ls-tree -r --name-only T | rg 'migrations?/.*\.(up|down)\.sql$'
git ls-tree -r --name-only S | rg 'migrations?/.*\.(up|down)\.sql$'
rg --files | rg 'migrations?/.*\.(up|down)\.sql$'
```

按项目规则检查：

- 版本是否重复或出现不允许的缺口。
- up/down 是否成对；已上线项目是否禁止 down。
- 直接提交中的旧编号是否在 merge 中被重编号，旧路径和新路径是否都被白名单漏掉。
- init schema、主迁移和后续 repair migration 是否描述同一最终结构。
- 代码、测试和配置是否引用缺失的迁移、表、列或枚举。

若 `P` 已经执行迁移，必须读取获授权环境的 migration ledger 并记录 `version`、`dirty` 或等价状态。不得根据仓库文件猜生产状态，也不得删除/重编号已执行版本；用新的向前迁移修复。

## 8. 候选结果验收

高风险候选至少完成：

- 计划路径与实际 diff 双向相等：没有漏项，也没有额外路径。
- `git diff --check` 和冲突标记扫描通过。
- 保留集按路径或 blob 校验没有变化。
- 删除、重命名、迁移和 merge-only 清单逐项关闭。
- 对关键入口执行调用链或契约检查，不能只做文件存在性检查。
- 按风险运行测试；若用户不允许运行，明确候选树未经行为验证，不能把静态通过描述为“可发布”。

正式发布前再比较候选提交与当前正式提交/迁移账本。发布或远端引用在审计后变化时，旧结论失效，必须重新冻结并复核。

## 9. 典型污染链与发布门禁

大范围 `restore/revert baseline` 进入 feature 后，再把 release 合入 feature，并不能抵消该反向补丁；若 feature 随后 fast-forward 到 release，Git 只复制 feature 最终 tree。无冲突、`Already up to date` 和 fast-forward 都不是业务正确性证明。复盘这类事故时，单独记录“回退提交 -> feature 合入 -> release fast-forward -> 发布”的链路。

发布验证不能只检查 systemd 主进程为 `active`。若 Worker 内部 scheduler、runtime runnable 或关键子任务已经退出，健康探针仍可能返回成功；必须检查子任务日志/状态、构建包内嵌资源与 commit SHA，以及线上 migration ledger。发现迁移缺失时，先排查旧 worktree、缓存或错误构建包，不要盲目添加重复版本。
