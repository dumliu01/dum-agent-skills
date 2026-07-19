# dum-doc-reconcile-domain 技能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 zebook 项目内的 `dum-doc-reconcile-newest` 通用化收进本插件仓库，命名 `dum-doc-reconcile-domain`，实现领域模块权威文档生成（维护 `docs/domain-tech-design/` 与 `docs/domain-product-design/` 两棵现状权威树）。

**Architecture:** 单文件 SKILL.md（完整继承 Bootstrap / Incremental 两模式 + 新增迁移模式 M + frontmatter 鲜度头/修改记录表/四步收尾记账）+ `scripts/` 打包两个通用化鲜度脚本（复制安装到目标项目 `scripts/`）。仓库集成走既有惯例：根索引文档补条目、CHANGELOG + 全 manifest 版本 1.1.9 → 1.2.0。

**Tech Stack:** Markdown 技能文档；Python 3（仅 stdlib + pyyaml）。

**Spec:** `docs/superpowers/specs/2026-07-19-dum-doc-reconcile-domain-design.md`

## Global Constraints

- 仓库根：`/Users/dum/Vmware_Share/dum_dev/dum-agent-skills`（下文 `$REPO`）。所有相对路径基于它。
- 目标树命名固定：`docs/domain-tech-design/`、`docs/domain-product-design/`；dated 历史树 `docs/tech-design/`、`docs/product-design/` 不变。
- `AGENTS.md` 是 `CLAUDE.md` 的**软链**，只改 `CLAUDE.md`，不要单独写 AGENTS.md。
- 脚本只依赖 stdlib + pyyaml；不引入测试框架，验证用临时 fixture 跑通。
- 平台是 macOS：`sed -i` 必须写成 `sed -i ''`。
- commit message 用中文、跟随仓库惯例（`feat(dum-doc-reconcile-domain): ...` / `docs: ...` 等）。
- 版本号：所有 manifest 与 `package.json` 由 `1.1.9` → `1.2.0`（新技能 = minor）。
- scratchpad：`/private/tmp/claude-501/-Users-dum-Vmware-Share-dum-dev-dum-agent-skills/a7689544-d337-4c8d-a43a-b6a53c42e909/scratchpad`（下文 `$SCRATCH`），fixture 放这里。

---

### Task 1: 鲜度脚本通用化（scripts/ 两文件 + fixture 验证）

**Files:**
- Create: `skills/dum-doc-reconcile-domain/scripts/_freshness_lib.py`（从 zebook 原样复制）
- Create: `skills/dum-doc-reconcile-domain/scripts/check_module_freshness.py`（通用化改写）

**Interfaces:**
- Consumes: 无（首个任务）。
- Produces: `check_module_freshness.py` CLI —— `python3 check_module_freshness.py --docs-root docs --repo . [--module <模块>] [--fail-on-stale]`；扫 `docs/domain-tech-design/` `docs/domain-product-design/`，按 frontmatter 的 `last-reconciled`/`reconciled-through`/`source.paths` 判 🟢/🟡，回写各模块 `README.md` 的 `<!-- FRESHNESS:START/END -->` 区。Task 2 的 SKILL.md 会引用这个 CLI。

- [ ] **Step 1: 原样复制 `_freshness_lib.py`**

```bash
mkdir -p /Users/dum/Vmware_Share/dum_dev/dum-agent-skills/skills/dum-doc-reconcile-domain/scripts
cp /Users/dum/Vmware_Share/work_dev/zebook-platform/sre/scripts/_freshness_lib.py \
   /Users/dum/Vmware_Share/dum_dev/dum-agent-skills/skills/dum-doc-reconcile-domain/scripts/_freshness_lib.py
```

复制后 Read 确认文件开头是 `"""模块现状权威文档 · 鲜度判定纯函数库。仅 stdlib + pyyaml。"""`，
且包含函数 `parse_frontmatter / parse_dated_prefix / source_commits_since / compute_status / render_freshness_table / splice_region` 与常量 `FRESH_START / FRESH_END`。该文件不含目录名硬编码，**不做任何修改**。

- [ ] **Step 2: 写通用化的 `check_module_freshness.py`**

写入 `skills/dum-doc-reconcile-domain/scripts/check_module_freshness.py`，完整内容如下
（相对 zebook 原版的改动：docstring 技能名与目录说法；`_NEWEST_DIRS` 后缀剥离改为
`_DOMAIN_TO_DATED` 显式映射表；结果字典键 `newest_dir` → `tree_dir`）：

```python
"""扫描 docs/domain-*-design 现状权威文档，判 🟢/🟡 并回写各模块 README 鲜度表。

用法：
  python3 check_module_freshness.py --docs-root docs --repo . [--module 邮箱] [--fail-on-stale]
只标状态，不改正文（内容合成交给 dum-doc-reconcile-domain 技能）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _freshness_lib import (  # noqa: E402
    FRESH_END, FRESH_START, compute_status, parse_dated_prefix,
    parse_frontmatter, render_freshness_table, source_commits_since,
    splice_region,
)

_TYPE_CN = {"tech-design": "方案", "product-design": "需求"}
# domain 现状权威树 → 对应的 dated 历史快照树
_DOMAIN_TO_DATED = {
    "domain-tech-design": "tech-design",
    "domain-product-design": "product-design",
}


def _newer_dated_count(docs_root: Path, tree_dir: str, module: str,
                       last_reconciled: str) -> int:
    """dated 树里 module 目录下、日期晚于 last_reconciled 的快照数。"""
    dated_dir = docs_root / _DOMAIN_TO_DATED[tree_dir] / module
    if not dated_dir.is_dir():
        return 0
    n = 0
    for f in dated_dir.glob("*.md"):
        d = parse_dated_prefix(f.name)
        if d and d > str(last_reconciled):
            n += 1
    return n


def scan(docs_root: Path, repo: Path, only_module: str | None) -> list[dict]:
    results: list[dict] = []
    for tree_dir in _DOMAIN_TO_DATED:
        base = docs_root / tree_dir
        if not base.is_dir():
            continue
        for module_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            module = module_dir.name
            if only_module and module != only_module:
                continue
            for doc in sorted(module_dir.glob("*.md")):
                if doc.name == "README.md":
                    continue
                fm = parse_frontmatter(doc.read_text(encoding="utf-8"))
                last = str(fm.get("last-reconciled", ""))
                ref = str(fm.get("reconciled-through", ""))
                paths = ((fm.get("source") or {}).get("paths")) or []
                commits = source_commits_since(repo, ref, paths)
                n_dated = _newer_dated_count(docs_root, tree_dir, module, last)
                status, detail = compute_status(len(commits), n_dated)
                results.append({
                    "tree_dir": tree_dir, "module": module, "doc": doc.name,
                    "type": _TYPE_CN.get(_DOMAIN_TO_DATED[tree_dir], "?"),
                    "last_reconciled": last or "—",
                    "status": status, "detail": detail,
                })
    return results


def write_readmes(docs_root: Path, results: list[dict]) -> list[Path]:
    written: list[Path] = []
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in results:
        groups.setdefault((r["tree_dir"], r["module"]), []).append(r)
    for (tree_dir, module), rows in groups.items():
        readme = docs_root / tree_dir / module / "README.md"
        table = render_freshness_table(rows)
        if readme.exists():
            content = readme.read_text(encoding="utf-8")
        else:
            content = f"# {module}模块 · 现状总入口\n"
        readme.write_text(
            splice_region(content, table, FRESH_START, FRESH_END),
            encoding="utf-8")
        written.append(readme)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-root", default="docs", type=Path)
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--module", default=None)
    ap.add_argument("--fail-on-stale", action="store_true")
    args = ap.parse_args(argv)

    results = scan(args.docs_root, args.repo, args.module)
    write_readmes(args.docs_root, results)
    stale = [r for r in results if r["status"] == "stale"]
    for r in results:
        badge = "🟢" if r["status"] == "fresh" else f"🟡 {r['detail']}"
        print(f"{badge}  {r['tree_dir']}/{r['module']}/{r['doc']}")
    print(f"\n合计 {len(results)} 份，{len(stale)} 份可能过时。")
    return 1 if (args.fail_on_stale and stale) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: fixture 验证 · 过时判定（🟡）**

在 scratchpad 造最小项目：1 份 domain 文档 + 1 份更晚的 dated 快照 + 1 次触及 `source.paths` 的提交，期望判 🟡。

```bash
SCRATCH=/private/tmp/claude-501/-Users-dum-Vmware-Share-dum-dev-dum-agent-skills/a7689544-d337-4c8d-a43a-b6a53c42e909/scratchpad
REPO=/Users/dum/Vmware_Share/dum_dev/dum-agent-skills
FIX="$SCRATCH/freshness-fixture"
rm -rf "$FIX"
mkdir -p "$FIX/src" "$FIX/docs/domain-tech-design/邮箱" "$FIX/docs/tech-design/邮箱"
cd "$FIX" && git init -q
echo v1 > src/a.txt
git add -A && git -c user.email=t@t -c user.name=t commit -qm init
H1=$(git rev-parse --short HEAD)
cat > "docs/domain-tech-design/邮箱/邮箱-同步.md" <<EOF
---
module: 邮箱
submodule: 同步
type: tech-design
status: authoritative-current
last-reconciled: 2026-01-01
reconciled-through: $H1
covers: [同步]
source:
  services: [mail]
  paths: [src/**]
supersedes: []
related: []
---
正文
EOF
echo "# 新方案" > "docs/tech-design/邮箱/20260601-新方案.md"
echo v2 >> src/a.txt
git add -A && git -c user.email=t@t -c user.name=t commit -qm change
python3 "$REPO/skills/dum-doc-reconcile-domain/scripts/check_module_freshness.py" \
  --docs-root "$FIX/docs" --repo "$FIX"
grep -c "FRESHNESS:START" "$FIX/docs/domain-tech-design/邮箱/README.md"
```

Expected 输出包含：
- `🟡 1 次相关提交 / 1 份新方案  domain-tech-design/邮箱/邮箱-同步.md`
- `合计 1 份，1 份可能过时。`
- 最后的 `grep -c` 输出 `1`（README 鲜度区已自动生成）。

- [ ] **Step 4: fixture 验证 · 新鲜判定（🟢）+ `--fail-on-stale` 退出码**

把 frontmatter 推到 HEAD、日期推到今天（晚于 dated 快照的 2026-06-01），期望转 🟢：

```bash
cd "$FIX"
H2=$(git rev-parse --short HEAD)
python3 - "$H2" <<'EOF'
import sys, pathlib, re
p = pathlib.Path("docs/domain-tech-design/邮箱/邮箱-同步.md")
t = p.read_text(encoding="utf-8")
t = re.sub(r"reconciled-through: \S+", f"reconciled-through: {sys.argv[1]}", t)
t = re.sub(r"last-reconciled: \S+", "last-reconciled: 2026-07-19", t)
p.write_text(t, encoding="utf-8")
EOF
python3 "$REPO/skills/dum-doc-reconcile-domain/scripts/check_module_freshness.py" \
  --docs-root "$FIX/docs" --repo "$FIX" --fail-on-stale
echo "exit=$?"
```

Expected 输出包含：
- `🟢  domain-tech-design/邮箱/邮箱-同步.md`
- `合计 1 份，0 份可能过时。`
- `exit=0`

注意：frontmatter 改动尚未 commit，`H2..HEAD` 无新提交、`source.paths` 也未再变，判定应为 fresh；若这里意外出 🟡，先检查是不是把 fixture 的 doc 改动 commit 出了新 HEAD。

- [ ] **Step 5: Commit**

```bash
cd /Users/dum/Vmware_Share/dum_dev/dum-agent-skills
git add skills/dum-doc-reconcile-domain/scripts/
git commit -m "feat(dum-doc-reconcile-domain): 鲜度检查脚本通用化（扫 domain-*-design 树，显式 dated 映射）"
```

---

### Task 2: SKILL.md + 技能 README.md

**Files:**
- Create: `skills/dum-doc-reconcile-domain/SKILL.md`
- Create: `skills/dum-doc-reconcile-domain/README.md`

**Interfaces:**
- Consumes: Task 1 的 CLI —— `python3 scripts/check_module_freshness.py --docs-root docs --repo . [--module <模块>] [--fail-on-stale]`（SKILL.md 中按"已复制到目标项目 `scripts/`"的路径引用）。
- Produces: 技能入口 `skills/dum-doc-reconcile-domain/SKILL.md`（Task 3 的根索引条目指向它）。

- [ ] **Step 1: 写 `SKILL.md`**

完整内容如下（源自 zebook `dum-doc-reconcile-newest` 参考技能，改动点：目录术语
`*-newest` → `domain-*-design`；脚本路径 `sre/scripts/` → `scripts/`；新增"前置 · 安装检查"
与"模式 M · 迁移"两节；frontmatter 模板示例去 zebook 专有服务名；红旗/出口判断同步更新）：

````markdown
---
name: dum-doc-reconcile-domain
description: Use when 建立/维护 docs/domain-tech-design 与 docs/domain-product-design 下按领域模块的"现状真相"权威文档——从带日期的历史方案合成首份(Bootstrap)，或按鲜度检查器标记做增量校对(Incremental)，兼做 *-newest 旧目录的一次性迁移。Triggers - "建领域模块现状文档"、"生成领域权威文档"、"合成现状权威文档"、"reconcile domain"、"更新模块现状文档"、"把 dated 方案收口成现状"。边界：本技能只动 domain-*-design 树；architecture/ 与 dated tech-design 的 prose 漂移用 dum-doc-reconcile。
---

# Dum Doc Reconcile Domain

## Overview

本技能维护**四棵树模型**里的"现状权威树"：`docs/tech-design/` `docs/product-design/` 是**带日期的历史快照堆**（一次决策的存档），`docs/domain-tech-design/` `docs/domain-product-design/` 是与之 1:1 对照的**无日期、按领域模块、现状真相**的活文档——想知道某模块"现在是什么样"只看 domain 树，dated 树只在追溯"当时为何这么决定"时才翻。

组织形式：`docs/domain-<type>-design/[模块]/[模块]-[子模块].md`（子模块粒度，避免单文件过大、鲜度更精细），每个模块目录下一份 `README.md` 作为**现状总入口 + 鲜度总览表**（表由 `check_module_freshness.py` 自动刷新，不手写）。

本技能是 `dum-session-summary → modify_history` 的下游：`dum-session-summary` 只如实记录"改了什么、为什么"，不预判哪份 domain 文档过时；`check_module_freshness.py` 负责把"谁可能过时"判成 🟢/🟡 状态标记；本技能负责**真正把内容改对**——合成首份、或把增量吸收进已有正文。三者分工：**记录事实（session-summary）→ 判定状态（freshness 脚本）→ 合成/校对内容（本技能）**。

## 与 dum-doc-reconcile 的边界

目标是 `docs/domain-tech-design/` `docs/domain-product-design/` 树 → 用**本技能**（`dum-doc-reconcile-domain`）。

目标是 `docs/architecture/` 或带日期的 `docs/tech-design/**/YYYYMMDD-*.md` `docs/product-design/**/YYYYMMDD-*.md` 的 prose 漂移校正 → 用 `dum-doc-reconcile`。

二者互不越界：`dum-doc-reconcile` 章程收得紧，只校正已存在的 prose、明确不写新文档；本技能天生要做它不干的事——**Bootstrap 合成**（从全量 dated 堆出 domain 树 v1.0，是"创建+综合"）与一整套新记账（frontmatter 鲜度头 + 修改记录表 + README 鲜度表，与 `dum-doc-reconcile` 的单行校对水印是两套不同约定，不要混用）。拿不准该跑哪个：看目标文件在不在 `domain-*-design/` 目录下。

## 核心原则

1. **报告先行**：动正文前先出"合成报告"（Bootstrap）或"漂移报告"（Incremental），停下等用户确认，再动文档。domain 文档是精雕内容，未经确认的重写会抹掉有意的细节。
2. **只本技能管 `domain-*-design` 树**；不碰 `architecture/`、dated 的 `tech-design/` `product-design/`、`specification/`——这些是 `dum-doc-reconcile` 或人工的地盘。
3. **修改记录表 + frontmatter 鲜度头一次同步更新**：正文改了、修改记录表追加了、frontmatter 的 `last-reconciled`/`reconciled-through`/`supersedes` 也必须同步，三者不能只改一处。
4. **内容合成归本技能，状态标记归 `check_module_freshness.py`**：不要手写 README 的鲜度总览表——那是脚本的活；本技能只负责把脚本判 🟡 的文档改到能重新判 🟢。
5. **代码溯源、宁瘦勿假**：domain 文档要写厚（对齐两份规范的完整章节），但架构图/时序图/接口签名/数据字段/流程必须从真实代码或 dated 溯源、注明 `文件:符号`；写不实处标"未核实"，**绝不为了充实而虚构机制/字段/API，更不能谎称"据代码核实"**。宁可某节薄而真，不可厚而假。

## 前置 · 安装检查

首次在一个项目里使用本技能时：

- 目标项目 `scripts/` 下没有 `check_module_freshness.py` / `_freshness_lib.py` → 从本技能的 [`scripts/`](scripts/) 复制过去（两个文件一起复制，checker 依赖 lib）。
- 依赖：python3 + pyyaml（`python3 -c "import yaml"` 报错则先 `pip install pyyaml`）。
- 用法：`python3 scripts/check_module_freshness.py --docs-root docs --repo . [--module <模块>] [--fail-on-stale]`。它只判状态并回写各模块 README 的 `<!-- FRESHNESS:START/END -->` 区，不改正文。

## 模式 M · 从 *-newest 迁移（一次性）

**触发场景**：项目里存在历史命名的 `docs/tech-design-newest/` 或 `docs/product-design-newest/`。检测到就先走本模式，迁移完成后才进入 A/B。

1. **目录改名**：`git mv docs/tech-design-newest docs/domain-tech-design`、`git mv docs/product-design-newest docs/domain-product-design`（只迁存在的那棵）。
2. **修链接**：全树 grep `-newest`，把文档 frontmatter `related` 及正文里指向 `tech-design-newest/` `product-design-newest/` 的路径改为 `domain-tech-design/` `domain-product-design/`（`supersedes` 指向 dated 树，正常不受影响，顺手核查）。
3. **换脚本**：项目里扫 `*-newest` 的旧鲜度脚本（无论在 `scripts/` 还是别处，如 `sre/scripts/`）删除或替换为本技能打包的新脚本（见"前置 · 安装检查"）。
4. **验证**：跑 `python3 scripts/check_module_freshness.py --docs-root docs --repo .`，确认各文档鲜度状态与迁移前一致、README 鲜度表正常回写；`grep -rn "newest" docs/domain-tech-design/ docs/domain-product-design/` 应无残留。
5. **独立 commit**：迁移单独提交，不与内容合成/校对混在一起。

## 模式 A · Bootstrap（建首份）

**触发场景**：某模块在 `domain-*-design/` 下尚无对应文档（新试点模块，或模块下新识别出一个此前没有 domain 文档的子模块）。

**输入**：
- 该模块**全量 dated** 快照：`docs/tech-design/<模块>/*.md` + `docs/product-design/<模块>/*.md`
- **深读现状代码**（该模块对应的 service/路径）——不仅核实 dated 是否仍是现状，更要从代码提炼架构图/时序图/接口签名/数据字段，填充规范第 2/3/5 节。dated 方案往往简略，正文的**厚度与准确度靠读代码补齐**，不是靠润色 dated 文字。
- `docs/architecture/<service>.md`（链接用，不抄代码结构）

**产出**：`<模块>-<子模块>.md` v1.0，含：
- 正文骨架填满（见下方"正文骨架"，方案/需求两种选一）
- 修改记录表首行 `v1.0`
- frontmatter 鲜度头（见下方模板）
- `supersedes` 列出本次合成收口的全部 dated 快照路径

**流程**：读全量 dated（按时间顺序，越新越权威）+ 现状代码，识别"当前生效的结论"与"已被后续方案推翻/取代的结论"，只把**当前生效**的部分写进 domain 正文；被推翻的历史决策留在 dated 树里，不搬进 domain 树（domain 树是现状真相，不是决策合集）。产出前先出合成报告，停下等确认，确认后再落盘并执行"四步收尾"。

## 模式 B · Incremental（增量校对）

**触发场景**：模块已有 domain 文档，被 `check_module_freshness.py` 标记为 🟡（可能过时）。

**输入**：
- 由检查器 🟡 列表驱动——先跑 `python3 scripts/check_module_freshness.py --module <模块>`（或不带 `--module` 跑全量），看哪些文档判 🟡 及原因（N 次相关提交 / M 份新方案）。
- 取证：`git diff <reconciled-through>..HEAD -- <source.paths>`（`reconciled-through` 与 `source.paths` 取自该文档 frontmatter）
- 晚于该文档 `last-reconciled` 的新 dated 快照（`docs/tech-design/<模块>/` 或 `docs/product-design/<模块>/` 下日期晚于 `last-reconciled` 的文件）
- 该时间范围内相关的 `docs/modify_history/` 记录

**原则**：只把**增量**（上次校对后新增的事实）吸收进正文，**不整篇重写**——已核实无变化的段落原样保留。产出漂移报告（复用 `dum-doc-reconcile` 的报告手法：逐条列"文档现述 vs 当前事实"），停下等确认，确认后再改并执行"四步收尾"。

## 四步收尾

两模式共用，产出/改动经用户确认后执行：

1. **改正文相关段落**——按报告里确认的项落盘。
2. **修改记录表追加一行**：版本号在原有基础上 +1（首次为 `v1.0`）、日期取今天、修改者取 `whoami`/`$USER`、修改点用一句话概括本次改了什么。
3. **同步 frontmatter**：`last-reconciled` 设为今天、`reconciled-through` 设为本次校对时的 git HEAD short hash、`supersedes` 追加本次新吸收的 dated 快照路径（Bootstrap 是首次写入全量，Incremental 是追加增量）。
4. **跑鲜度检查器**：`python3 scripts/check_module_freshness.py --module <模块>`，确认该文档在对应 README 的鲜度总览表里转为 🟢。检查器会自动回写 README，不要手改 README 的鲜度表。

## frontmatter 鲜度头模板

所有 domain 文档共用，是鲜度检查器的全部输入依据（`last-reconciled` + `reconciled-through` + `source.paths` 三件套）：

```yaml
---
module: 邮箱
submodule: 邮件同步
type: tech-design                 # 或 product-design
status: authoritative-current
last-reconciled: 2026-07-15       # 上次校对日期
reconciled-through: 27611a76      # 校对时的 git HEAD short hash（关键）
covers: [邮件同步Worker, 分片扩缩容, 队头阻塞治理]
source:                           # 鲜度检测依据：改了这些=可能过时
  services: [mail-server, mail-sync-worker]
  paths: [mail-server/internal/syncworker/**]
supersedes:                       # 收口了哪些历史 dated 快照
  - tech-design/邮箱/20260623-邮件同步Worker队头阻塞治理方案.md
related: [architecture/mail-sync-worker.md, domain-product-design/邮箱/邮箱-收信.md]
---
```

字段说明：
- `module` / `submodule`：对应 `domain-*-design/[模块]/[模块]-[子模块].md` 的路径分段。
- `type`：`tech-design`（方案）或 `product-design`（需求），决定用哪种正文骨架。
- `status`：固定 `authoritative-current`，标记这是现状权威文档（区别于 dated 的归档文档）。
- `last-reconciled` / `reconciled-through`：鲜度检查器唯一依据，每次四步收尾第 3 步必须同步。
- `covers`：本文档覆盖的主题/机制点列表，供人快速判断"这份文档答不答得了我的问题"。
- `source.services` / `source.paths`：鲜度检测的比对源——这些路径/服务有新提交，检查器就判 🟡。
- `supersedes`：本文档收口的历史 dated 快照，Bootstrap 首次写入全量，Incremental 追加新收口的。
- `related`：链到 `architecture/<service>.md`、对面 domain 树的姊妹文档等不重复抄写的关联文档。

## 修改记录表模板

正文第一块，所有 domain 文档统一，与 frontmatter 互补（一次更新同时动）：

```markdown
## 修改记录
| 版本 | 日期 | 修改者 | 修改点 |
|---|---|---|---|
| v1.0 | 2026-07-15 | dum | 首次由 dated 方案合成建立，源到 27611a76 |
| v1.1 | 2026-07-20 | dum | reconcile：补入队头阻塞治理 |
```

规则：每次 reconcile（Incremental）或 Bootstrap 首建 → 追加一行（版本递增、日期、修改者取本机登录用户名 `whoami`/`$USER`、一句修改点），同时同步 frontmatter 的 `last-reconciled` / `reconciled-through`（四步收尾第 2、3 步）。

## 正文骨架

按 frontmatter 的 `type` 选一种，两种都以 `## 修改记录`（= 规范第 0 节·文档修改历史）打头。骨架对齐两份规范：方案对齐《技术方案文档规范》，需求对齐《产品文档规范》。

**每一节都要有实质内容，不是一句话占位。** 文档"太简陋"的根因，是只从简略的 dated 方案合成、又没去读代码。要写厚**且不编造**，唯一正确来源是**深读真实代码**——架构图、时序图、接口签名、数据表/字段，全部从代码（或 dated）溯源；写不实处标"未核实"，**绝不为充实而虚构**（曾出过"谎称按 created_at tiebreak 且据代码核实"的编造事故，见红旗）。

**方案（domain-tech-design）** —— 现状视角，逐节实写：

```
## 修改记录                      // 规范第0节·文档修改历史（版本|日期|修改者|修改点）

## 1. 背景介绍                   // 本模块/子模块解决什么产品需求或问题、为何存在

## 2. 架构设计与模块设计          // 当前架构+模块划分+各模块职责；配一张 mermaid 模块关系图
                                //（从代码结构提炼，不照抄 architecture 目录树，链 architecture/<service>.md）

## 3. 核心业务流程               // 用 mermaid 时序图/流程图描述当前关键流程（不止文字）；标注涉及的关键函数/服务

## 4. 重点（难点）问题解决        // 每个难点用「问题→方案→取舍」分段（### 4.1/4.2…），参数/阈值入表，代码锚点收段末

## 5. 关键接口和数据             // 真实 API 签名（方法/路径/入参出参）+ 关键数据模型（表/结构体字段：名+类型+含义），
                                // 全部代码溯源、注明 文件:符号

## 6. 疑问与遗留                 // 已知遗留、待优化、存疑点（含未核实项；项目有 docs/deffered/ 之类目录就顺手链上）

## 决策追溯                      //（附加）本现状由哪些历史 dated 方案演进而来，反向链接 dated，不搬正文只指路
```

**需求（domain-product-design）** —— 现状视角，逐节实写：

```
## 修改记录                      // 规范第0节·文档修改历史

## 1. 背景介绍                   // 需要解决的问题和目标

## 2. 设计思路                   // 产品设计核心思路（如何解决问题/完成目标）+ 核心业务流程（可配流程图）

## 3. 功能点                     // 当前功能模块清单 + 有哪些功能页面

## 4. 产品体验流程故事            // 先「角色定义」再「场景故事」；角色按"谁操作"定义，默认1个，仅多人协作场景才多角色
                                //（详见下方"产品体验流程故事写法"；每场景一张 环节|界面|动作 表）

## 需求演进追溯                  //（附加）链历史 dated 需求
```

不重复边界：代码结构/编码规范只**链** `architecture/<service>.md`、`specification/` 不整段抄；历史决策在"决策追溯/需求演进追溯"反向链接 dated，不搬正文。**但架构图、时序图、接口签名、数据字段、角色体验流程属于本文档必须自带的实质内容**（现状真相要能独立看懂），不能用"详见 architecture"一笔带过。

## 产品体验流程故事写法（需求文档 §4）

§4 分两块：先**角色定义**，再**场景故事**。

**角色 = 按"谁操作产品"定义，不是按"用户做的不同任务"拆。**
- 一个功能面若**全程只有一个人在操作**（如"邮箱使用者"管理自己的签名/规则/草稿/设置——都是同一个人的不同任务），**就只定义 1 个角色**。**不要**把同一个人的多件事拆成"角色 A 管签名 / 角色 B 管规则"——那是**场景**，不是角色。
- **只有当某个场景真的需要不同的人各自操作**才定义多个角色。例：A 发消息给 B（发送者 vs 接收者）、发起审批 vs 审批人、组织管理员开权限 vs 员工绑定。判据：这两个人是不是**各自都要在产品里动手操作**？是→两个角色；若只是"另一个人被动收到结果"（如自动回复的来信人、被抄送人）→ 仍是 1 个操作角色。

**写法**：
1. `### 角色定义`：一张表 `角色 | 说明（谁、在什么位置操作）`。单人功能就一行。
2. `### 场景 N：<标题>`（标注涉及角色，如"（角色：邮箱使用者）"，跨角色写"（角色：管理员 → 员工）"）：每个场景一张 `环节 | 界面 | 动作` 表；跨角色场景要在"环节/动作"里标明该步是**谁**在操作。
3. **不要**再用"### 角色 A/B/C"给同一个人的不同任务编号——那是场景，用"### 场景 1/2/3"。

## 排版与可读性（方案文档必守）

坏味道：一个难点写成 4-5 行的运行句，句子中段塞满 `文件:符号`、配置项、默认值、还夹带"这在 dated 未见描述是本轮读代码新发现"的考证——**准确但读起来像代码考古，不是设计文档**。参照 `dum-solution-design`：主文档只讲逻辑与决策，接口/数据/参数用表格，代码只留锚点。硬性规约：

1. **难点用「问题 → 方案 → 取舍」分段**（`### 4.1 xxx`），每段独立成行；不要一个 bullet 塞满全部信息。
2. **代码引用收口段末单独一行**：`代码：\`文件:符号\``。正文用自然语言把结论讲清，`文件:符号` **不塞进句子中段**；一个点最多 1-2 个关键锚点，不逐 symbol 堆。
3. **参数/默认值/枚举/错误码/阈值 → 表格**（如 `参数|默认|环境变量|作用`、`错误类型|阈值|处理`）。**禁止**句子里罗列 `默认3`/`默认10`/`120s~3600s`。
4. **接口 → 表格**（`路径|method|入参|出参|错误码`）；**数据模型 → 字段表**（`字段|类型|含义`）。
5. **考证/元注记不内联**：`读代码新发现`/`未见于 dated`/`纠正旧文档X`/`（未核实其实现）` 这类**不写进正文**——正文只讲现状结论；把"与 architecture/dated 的差异及本轮纠正了什么"集中到 **决策追溯** 段的一张「与旧文档差异」小表，"未核实项"归入 **§6 遗留**。
6. **一个观点一段/一条**，避免 4-5 行运行长句；能拆表就拆表，能拆子标题就拆子标题。
7. 文档/代码分离（同 `dum-solution-design`）：不贴函数实现，只留签名/schema/伪代码 + 锚点。

目标：一个没读过代码的人也能顺畅读完、抓住设计要点；要查证据再顺着段末锚点去代码。

## 红旗

- 未出报告就改正文 → 停，先出合成/漂移报告等确认。
- 检测到项目里还有 `*-newest` 旧目录却直接在 domain 树建/改文档 → 停，先走模式 M 迁移。
- 动了 `domain-*-design` 之外的目录（`architecture/`、dated 的 `tech-design/`/`product-design/`、`specification/`）→ 撤销，改用 `dum-doc-reconcile` 或人工处理。
- 手写 README 鲜度表（应由 `check_module_freshness.py` 生成）→ 撤销，改跑脚本回写。
- Incremental 模式整篇重写正文（而非只吸收增量）→ 撤销，改成只改被新事实影响的段落。
- Bootstrap 把已被后续方案推翻的历史结论也写进 domain 正文 → 撤销，只保留当前生效的结论，推翻的部分留在 dated 树。
- 只改了正文、忘了同步修改记录表或 frontmatter（三处只动一两处）→ 补全，三者必须一次同步。
- 规范某节写成一句话占位，或用"详见 architecture"搪塞架构图/时序图/接口数据 → 停，去读代码把实质内容补上（图、真实签名、字段）。
- **为了充实而虚构 API/字段/流程/机制（哪怕"看起来合理"），或谎称"据代码核实" → 撤销**，只写能溯源的，存疑处标"未核实"。这是本技能最严重的红旗。
- 难点写成塞满 `文件:符号`/配置默认值的运行长句 → 停，改「问题→方案→取舍」分段 + 参数入表 + 代码锚点收段末（见"排版与可读性"）。
- `读代码新发现`/`纠正旧文档`/`未核实其实现` 等考证内联进正文 → 移出：差异归 决策追溯「与旧文档差异」小表，未核实项归 §6 遗留，正文只留现状结论。
- §4 把同一操作者的不同任务拆成多个"角色"（角色 A 管签名/角色 B 管规则…其实都是同一个人）→ 停，合并为 1 个角色 + 多个"场景"；只有不同的人各自操作才是多角色（见"产品体验流程故事写法"）。

## 出口判断

- ✅ 合成/漂移报告已交并获用户确认（报告先行）。
- ✅ 正文、修改记录表、frontmatter（`last-reconciled`/`reconciled-through`/`supersedes`）三处已同步更新。
- ✅ `python3 scripts/check_module_freshness.py --module <模块>` 已跑过，且该模块对应文档在 README 鲜度总览表里转为 🟢。
- ✅ 未触碰 `domain-*-design` 之外的目录；README 鲜度表未被手写，全部由脚本回写。
- ✅ 项目里已无 `*-newest` 旧目录残留（有则模式 M 已完成并独立提交）。
- ✅ 逐节实写、无一句话占位：方案文档第 2/3/5 节有真实**架构图·时序图·接口数据**（代码溯源、注明 `文件:符号`）；需求文档第 4 节先有**角色定义**（按操作者定义，单人功能只 1 个角色，多人协作才多角色，未把同一人的不同任务误拆为多角色）、再是**分场景的体验流程故事**（环节/界面/动作）；全文无虚构、无"据代码核实"的不实断言。
- ✅ 排版工整可读：难点走「问题→方案→取舍」分段；参数/阈值/枚举/错误码/接口/字段均以表格呈现；代码锚点收段末不散落句中；考证类元注记不内联（归 决策追溯「与旧文档差异」小表或 §6 遗留）。

漏任一项就还没完成。
````

- [ ] **Step 2: 写技能 `README.md`**

完整内容如下（体例仿 `skills/dum-doc-reconcile/README.md`：它做什么/何时触发/交付什么/衔接/完整工作流）：

````markdown
# dum-doc-reconcile-domain

> 把带日期的历史方案堆**收口**成 `docs/domain-tech-design/` `docs/domain-product-design/` 下按领域模块的"现状真相"权威文档——**报告先行**，确认后才写；鲜度脚本自动标 🟢/🟡。

## 它做什么

dated 方案（`docs/tech-design/` `docs/product-design/`）是一次次决策的存档，想知道某模块"现在是什么样"得翻一堆历史。本技能维护与之 1:1 对照的**现状权威树**：`docs/domain-<type>-design/<模块>/<模块>-<子模块>.md`，每模块一份 README 作总入口 + 鲜度总览表。

**三种模式**：

| 模式 | 何时 | 做什么 |
|---|---|---|
| M · 迁移 | 项目里还有 `*-newest` 旧目录 | `git mv` 改名 domain-* + 批量修链接 + 换新脚本（一次性，独立 commit） |
| A · Bootstrap | 模块在 domain 树下没文档 | 读全量 dated + 深读现状代码，合成 v1.0（只写当前生效的结论） |
| B · Incremental | 鲜度脚本判 🟡 | `git diff` 取证 + 新 dated 快照 + modify_history，只吸收增量不整篇重写 |

**记账体系**：frontmatter 鲜度头（`last-reconciled`/`reconciled-through`/`source.paths` 三件套）+ 修改记录表 + 四步收尾（改正文→追记录→同步 frontmatter→跑脚本转 🟢）。

**打包脚本**（[`scripts/`](scripts/)，首次使用复制到目标项目 `scripts/`）：

- `check_module_freshness.py` — 扫 domain 树，按 frontmatter 比对 git 提交与新 dated 快照，判 🟢/🟡 并回写各模块 README 鲜度表
- `_freshness_lib.py` — 判定纯函数库（仅 stdlib + pyyaml）

## 何时触发

- ✅ "建领域模块现状文档" / "生成领域权威文档" / "把 dated 方案收口成现状"
- ✅ "更新模块现状文档" / "reconcile domain"
- ❌ `docs/architecture/` 或 dated 方案的 prose 漂移校正 → 用 [`dum-doc-reconcile`](../dum-doc-reconcile/)
- ❌ 写新方案 → 用 [`dum-solution-design`](../dum-solution-design/)
- ❌ 总结会话改动 → 用 [`dum-session-summary`](../dum-session-summary/)

## 它交付什么

| | |
|---|---|
| 合成/漂移报告 | 动笔前在对话里给用户审（报告先行硬 gate） |
| domain 权威文档 | 骨架对齐《技术方案文档规范》/《产品文档规范》，架构图/时序图/接口数据全部代码溯源 |
| 鲜度记账 | frontmatter + 修改记录表 + 脚本回写的 README 鲜度总览表 |

## 跟其它技能怎么衔接

- [`dum-session-summary`](../dum-session-summary/) 的**下游**：它记事实 → 鲜度脚本判状态 → 本技能改内容
- 与 [`dum-doc-reconcile`](../dum-doc-reconcile/) 按**路径**分工：`domain-*-design/` 归本技能；`architecture/` 与 dated prose 归它。两套记账约定互不混用
- dated 方案由 [`dum-solution-design`](../dum-solution-design/) 产出，是 Bootstrap 的输入

## 完整工作流

三模式详细步骤、frontmatter/修改记录表模板、两套正文骨架、排版规约、红旗自检与出口判断，详见 [`SKILL.md`](SKILL.md)。
````

- [ ] **Step 3: 一致性检查**

```bash
cd /Users/dum/Vmware_Share/dum_dev/dum-agent-skills/skills/dum-doc-reconcile-domain
grep -n "sre/scripts" SKILL.md README.md; echo "---"
grep -n "newest" SKILL.md | grep -v "迁移\|模式 M\|tech-design-newest\|product-design-newest\|\*-newest"
```

Expected：第一个 grep 无输出（不残留 zebook 专有路径）；第二个 grep 无输出（`newest` 只出现在迁移相关语境）。若有输出，逐处修正。

- [ ] **Step 4: Commit**

```bash
cd /Users/dum/Vmware_Share/dum_dev/dum-agent-skills
git add skills/dum-doc-reconcile-domain/SKILL.md skills/dum-doc-reconcile-domain/README.md
git commit -m "feat(dum-doc-reconcile-domain): 领域模块权威文档生成技能正文（Bootstrap/Incremental/迁移三模式）"
```

---

### Task 3: 根索引文档集成 + 提交两份规范

**Files:**
- Modify: `CLAUDE.md`（技能清单表 + 衔接段落；`AGENTS.md` 是软链，勿动）
- Modify: `GEMINI.md:12`（技能表加行）
- Modify: `README.md:16`、`README.md:107`（技能表加行 + 仓库结构树加行）
- Commit（新增跟踪）: `docs/原始需求/技术方案文档规范.md`、`docs/原始需求/产品文档规范.md`

**Interfaces:**
- Consumes: Task 2 产出的 `skills/dum-doc-reconcile-domain/SKILL.md` 与 `README.md`（条目链接指向它们）。
- Produces: 无（纯索引更新）。

- [ ] **Step 1: CLAUDE.md 技能清单表加行**

Edit `CLAUDE.md`，old_string：

```
| **dum-doc-reconcile** | 按时间范围依据 `docs/modify_history`（兼查 git）把 architecture/方案设计文档跟代码现状对账修正。触发："校对/修正设计文档"/"文档对账" | `skills/dum-doc-reconcile/SKILL.md` |
```

new_string（原行 + 新行）：

```
| **dum-doc-reconcile** | 按时间范围依据 `docs/modify_history`（兼查 git）把 architecture/方案设计文档跟代码现状对账修正。触发："校对/修正设计文档"/"文档对账" | `skills/dum-doc-reconcile/SKILL.md` |
| **dum-doc-reconcile-domain** | 建立/维护 `docs/domain-tech-design/` 与 `docs/domain-product-design/` 下按领域模块的"现状真相"权威文档：从 dated 历史方案合成首份（Bootstrap）、按鲜度标记增量校对（Incremental）、兼做 `*-newest` 旧目录迁移。触发："建领域模块现状文档"/"生成领域权威文档"/"reconcile domain"/"把 dated 方案收口成现状" | `skills/dum-doc-reconcile-domain/SKILL.md` |
```

- [ ] **Step 2: CLAUDE.md 衔接段落补一句**

Edit `CLAUDE.md`，old_string：

```
`dum-e2e-test` 消费 `dum-solution-design` 的技术方案与需求/架构文档派生用例，复用 `webapp-testing` 实测，定责出的文档冲突回流 `dum-doc-reconcile`、修复后用 `dum-session-summary` 记账。
```

new_string（原句 + 新句）：

```
`dum-e2e-test` 消费 `dum-solution-design` 的技术方案与需求/架构文档派生用例，复用 `webapp-testing` 实测，定责出的文档冲突回流 `dum-doc-reconcile`、修复后用 `dum-session-summary` 记账。
`dum-doc-reconcile-domain` 同为 `dum-session-summary` 的下游：把 dated 方案堆收口成 `docs/domain-tech-design/` `docs/domain-product-design/` 的现状权威文档，并由随技能打包的鲜度脚本驱动增量校对；与 `dum-doc-reconcile` 按路径分工——domain 树归它，`architecture/` 与 dated 方案的 prose 漂移归 `dum-doc-reconcile`。
```

- [ ] **Step 3: GEMINI.md 技能表加行**

Edit `GEMINI.md`，old_string：

```
| **dum-doc-reconcile** | "校对/修正设计文档"，让 docs/architecture 与方案设计文档跟代码现状对齐 | `skills/dum-doc-reconcile/SKILL.md` |
```

new_string（原行 + 新行）：

```
| **dum-doc-reconcile** | "校对/修正设计文档"，让 docs/architecture 与方案设计文档跟代码现状对齐 | `skills/dum-doc-reconcile/SKILL.md` |
| **dum-doc-reconcile-domain** | "建领域模块现状文档"/"reconcile domain"，把 dated 方案收口成 docs/domain-*-design/ 的现状权威文档并按鲜度增量校对 | `skills/dum-doc-reconcile-domain/SKILL.md` |
```

- [ ] **Step 4: README.md 技能表 + 仓库结构树加行**

Edit `README.md`，old_string：

```
| [`dum-doc-reconcile`](skills/dum-doc-reconcile/README.md) | 按修改记录（兼查 git）把设计文档跟代码现状对账修正 | [SKILL.md](skills/dum-doc-reconcile/SKILL.md) |
```

new_string（原行 + 新行）：

```
| [`dum-doc-reconcile`](skills/dum-doc-reconcile/README.md) | 按修改记录（兼查 git）把设计文档跟代码现状对账修正 | [SKILL.md](skills/dum-doc-reconcile/SKILL.md) |
| [`dum-doc-reconcile-domain`](skills/dum-doc-reconcile-domain/README.md) | 把 dated 历史方案收口成 `docs/domain-*-design/` 按领域模块的现状权威文档（Bootstrap 合成 + 鲜度驱动增量校对） | [SKILL.md](skills/dum-doc-reconcile-domain/SKILL.md) |
```

再 Edit `README.md`，old_string：

```
│   ├── dum-doc-reconcile/
```

new_string：

```
│   ├── dum-doc-reconcile/
│   ├── dum-doc-reconcile-domain/
```

- [ ] **Step 5: 验证 AGENTS.md 软链同步 + 链接落点存在**

```bash
cd /Users/dum/Vmware_Share/dum_dev/dum-agent-skills
grep -c "dum-doc-reconcile-domain" AGENTS.md
ls skills/dum-doc-reconcile-domain/SKILL.md skills/dum-doc-reconcile-domain/README.md
```

Expected：`grep -c` 输出 `2`（表行 + 衔接句，经软链可见）；`ls` 两个文件都存在。

- [ ] **Step 6: Commit（含两份规范首次入库）**

```bash
cd /Users/dum/Vmware_Share/dum_dev/dum-agent-skills
git add CLAUDE.md GEMINI.md README.md "docs/原始需求/技术方案文档规范.md" "docs/原始需求/产品文档规范.md"
git commit -m "docs: 根索引补 dum-doc-reconcile-domain 条目；收录技术方案/产品文档两份规范"
```

---

### Task 4: CHANGELOG + 版本号 1.1.9 → 1.2.0

**Files:**
- Modify: `CHANGELOG.md`（顶部加 `[1.2.0]` 段）
- Modify: `.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`、`.cursor-plugin/plugin.json`、`gemini-extension.json`、`package.json`（version 字段）
- Modify: `README.md:21`（"当前版本"行）

**Interfaces:**
- Consumes: Task 1-3 已全部提交（CHANGELOG 描述的就是它们）。
- Produces: 无（发版收尾）。

- [ ] **Step 1: CHANGELOG.md 顶部加 1.2.0 段**

Edit `CHANGELOG.md`，old_string：

```
## [1.1.9] - 2026-07-02
```

new_string（新段 + 原标题行）：

```
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
```

- [ ] **Step 2: 版本号统一替换**

```bash
cd /Users/dum/Vmware_Share/dum_dev/dum-agent-skills
grep -rln '"version": "1.1.9"' .claude-plugin .codex-plugin .cursor-plugin gemini-extension.json package.json
sed -i '' 's/"version": "1.1.9"/"version": "1.2.0"/' \
  .claude-plugin/plugin.json .codex-plugin/plugin.json .cursor-plugin/plugin.json \
  gemini-extension.json package.json
sed -i '' 's/当前版本 \*\*v1\.1\.9\*\*/当前版本 **v1.2.0**/' README.md
```

第一条 grep 用于确认待改文件清单（若 `.claude-plugin/marketplace.json` 等额外文件也出现在结果里，把它加进 sed 的文件列表一起改）。

- [ ] **Step 3: 验证无 1.1.9 残留**

```bash
cd /Users/dum/Vmware_Share/dum_dev/dum-agent-skills
grep -rn "1\.1\.9" --include="*.json" . | grep -v node_modules | grep -v CHANGELOG || echo "clean"
grep -n "1\.1\.9" README.md || echo "README clean"
```

Expected：两条都输出 clean（CHANGELOG 里的历史 `[1.1.9]` 段保留，不算残留）。

- [ ] **Step 4: Commit**

```bash
cd /Users/dum/Vmware_Share/dum_dev/dum-agent-skills
git add CHANGELOG.md README.md package.json gemini-extension.json \
  .claude-plugin/plugin.json .codex-plugin/plugin.json .cursor-plugin/plugin.json
git commit -m "chore(release): 1.1.9 → 1.2.0（新技能 dum-doc-reconcile-domain）"
git log --oneline -4
```

Expected：`git log` 显示本计划的 4 个 commit。
