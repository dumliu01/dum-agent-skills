# 文档结构化（按量自动分子目录）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `docs/tech-design/`（按功能模块）与 `docs/modify_history/`（按年）少则平铺、超 20 篇自动触发分子目录，并把规则落进 4 个技能 + 索引脚本。

**Architecture:** 阈值判定写进落盘技能（solution-design / session-summary）；tech-design 由 AI 聚类+确认后搬迁，modify_history 机械按年搬迁；索引脚本 `update_docs_index.py` 加平铺计数与超阈值横幅（已递归收录子目录）；reconcile 修复单层 glob 改递归。

**Tech Stack:** Python 3（脚本，stdlib only）、Markdown（SKILL.md 规则文件）。

## Global Constraints

- 触发阈值：tech-design **20** 篇、modify_history **20** 篇（均不含 README，只数分类根目录下直接平铺的 `.md`）。
- tech-design 子目录布局：`docs/tech-design/<模块>/YYYYMMDD-方案名.md`；模块名小写英文短语；兜底目录 `docs/tech-design/_misc/`；模块清单写 `docs/tech-design/README.md`。
- modify_history 子目录布局：`docs/modify_history/<YYYY>/YYYY-MM-DD-标题.md`（年份取文件名前 4 位）。
- 文件名约定不变：solution-design 用 `YYYYMMDD-标题.md`，session-summary 用 `YYYY-MM-DD-标题.md`。
- 「已分目录」判定：分类根下已存在至少一个非 README 子目录。
- 脚本 stdlib only，幂等、静默（marker/文件缺失 exit 0）。
- 搬文件一律 `git mv`；tech-design 搬迁前必须出草案并停下等用户确认；modify_history 搬迁 announce 即可。
- 设计依据：`docs/tech-design/20260626-DocStructureAutoSubdir.md`（5 模块方案，本工作的唯一设计文档）。

---

### Task 1: 索引脚本加平铺计数 + 超阈值横幅

**Files:**
- Modify: `skills/dum-knowledge-base-build/scripts/update_docs_index.py`
- Test: `skills/dum-knowledge-base-build/scripts/tests/test_flat_count.py`（Create）

**Interfaces:**
- Produces: `flat_count(dirname: str) -> int`（分类根下直接平铺、排除 EXCLUDE_FILES 的 `.md` 数）；模块级 `SUBDIR_THRESHOLDS: dict[str, int]`；`build_index_text()` 在任一分类 `flat_count >= 阈值` 时于返回文本顶部加 `⚠️` 横幅行。
- Consumes: 现有模块级全局 `DOCS_ROOT`、`DOC_EXTENSIONS`、`EXCLUDE_FILES`。

- [ ] **Step 1: 写失败测试**

Create `skills/dum-knowledge-base-build/scripts/tests/test_flat_count.py`:

```python
import importlib.util
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "update_docs_index.py"


def _load():
    spec = importlib.util.spec_from_file_location("udi", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_flat_count_excludes_readme_and_subdirs():
    mod = _load()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        td = root / "tech-design"
        (td / "auth").mkdir(parents=True)
        (td / "README.md").write_text("# x", encoding="utf-8")
        (td / "auth" / "20260101-A.md").write_text("# a", encoding="utf-8")
        for i in range(3):
            (td / f"2026010{i}-flat.md").write_text("# f", encoding="utf-8")
        mod.DOCS_ROOT = root
        assert mod.flat_count("tech-design") == 3  # README + 子目录文件不计


def test_banner_appears_over_threshold():
    mod = _load()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        td = root / "tech-design"
        td.mkdir(parents=True)
        for i in range(20):
            (td / f"202601{i:02d}-x.md").write_text("# x", encoding="utf-8")
        mod.DOCS_ROOT = root
        mod.SUBDIR_THRESHOLDS = {"tech-design": 20}
        text = mod.build_index_text()
        assert "⚠️" in text and "tech-design" in text and "20" in text
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest skills/dum-knowledge-base-build/scripts/tests/test_flat_count.py -v`
Expected: FAIL（`AttributeError: module 'udi' has no attribute 'flat_count'`）。无 pytest 时用 `python3 -c "import importlib.util,...; ..."` 等价手测，先确认 `flat_count` 不存在报 AttributeError。

- [ ] **Step 3: 实现 flat_count + 阈值常量**

在 `update_docs_index.py` 配置段（`EXCLUDE_DIRS` 之后）加：

```python
# 6) 平铺超过多少篇就提示分子目录（不含 README）
SUBDIR_THRESHOLDS: dict[str, int] = {
    "tech-design": 20,
    "modify_history": 20,
}
```

在 `collect_category` 之后加函数：

```python
def flat_count(dirname: str) -> int:
    """该分类根目录下直接平铺（不递归子目录）的文档数，排除 EXCLUDE_FILES。"""
    base = DOCS_ROOT / dirname
    if not base.exists():
        return 0
    return sum(
        1 for p in base.iterdir()
        if p.is_file() and p.suffix in DOC_EXTENSIONS and p.name not in EXCLUDE_FILES
    )
```

- [ ] **Step 4: 在 build_index_text 顶部加横幅**

把 `build_index_text` 改为先收集横幅再拼分类块：

```python
def build_index_text() -> str:
    blocks: list[str] = []
    for dirname, threshold in SUBDIR_THRESHOLDS.items():
        n = flat_count(dirname)
        if n >= threshold:
            blocks.append(
                f"> ⚠️ `{dirname}` 平铺已 {n} 篇，超过阈值 {threshold}，建议分子目录"
                f"（tech-design 按模块 / modify_history 按年）。"
            )
    if blocks:
        blocks.append("")
    for dirname, title in CATEGORIES:
        entries = collect_category(dirname)
        count = f"（{len(entries)} 篇）" if entries else ""
        blocks.append(f"### {title} · `{DOCS_ROOT_REL}/{dirname}/`{count}")
        if not entries:
            blocks.append("_（暂无）_")
        else:
            for date, text, link in entries:
                prefix = f"`{date}` " if date else ""
                blocks.append(f"- {prefix}[{text}]({link})")
        blocks.append("")
    return "\n".join(blocks).rstrip() + "\n"
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python3 -m pytest skills/dum-knowledge-base-build/scripts/tests/test_flat_count.py -v`
Expected: PASS（2 passed）。

- [ ] **Step 6: 回归——脚本在本仓库静默运行**

Run: `python3 skills/dum-knowledge-base-build/scripts/update_docs_index.py`
Expected: 无报错退出（本仓库无 docs-index.md → 静默 exit 0）。

- [ ] **Step 7: 提交**

```bash
git add skills/dum-knowledge-base-build/scripts/update_docs_index.py \
        skills/dum-knowledge-base-build/scripts/tests/test_flat_count.py
git commit -m "feat(kb-build): index 加平铺计数 flat_count + 超阈值分子目录提示横幅"
```

---

### Task 2: scaffold 脚本——tech-design 模块清单 README + modify_history 按年 README

**Files:**
- Modify: `skills/dum-knowledge-base-build/scripts/scaffold_docs_structure.py:31-61`（`CATEGORIES` 里 tech-design 与 modify_history 两条的 README 正文）

**Interfaces:**
- Consumes: 现有 `_readme()` / `_write_if_absent()`（幂等，不覆盖已有 README）。
- Produces: 新建项目时 tech-design/README 含模块清单表骨架 + 阈值说明；modify_history/README 含按年归档说明。

- [ ] **Step 1: 改 tech-design 的 README 正文**

把 `CATEGORIES` 里 tech-design 一条（约 40-42 行）替换为：

```python
    ("tech-design", "技术方案",
     "技术方案设计文档，dum-solution-design skill 的产出落到这里。\n\n"
     "**组织约定**：平铺文档超过 **20** 篇时，按**功能模块**分子目录："
     "`docs/tech-design/<模块>/YYYYMMDD-方案名.md`；不属任何模块的零散方案放 `_misc/`。\n\n"
     "**模块清单**（新增模块时在此登记一行，落盘前先查此表复用已有模块、防同义词目录）：\n\n"
     "| 模块 | 目录 | 一句话职责 |\n"
     "|---|---|---|\n"
     "| _（示例）auth_ | `auth/` | 登录鉴权相关方案 |\n\n"
     + NAMING),
```

- [ ] **Step 2: 改 modify_history 的 README 正文**

把 `CATEGORIES` 里 modify_history 一条（约 45-47 行）替换为：

```python
    ("modify_history", "修改记录",
     "阶段总结与修改记录（每个里程碑/阶段一份），dum-session-summary skill 的产出落到这里。\n\n"
     "**组织约定**：平铺文档超过 **20** 篇时，按**年**分子目录："
     "`docs/modify_history/<YYYY>/YYYY-MM-DD-标题.md`（年份取文件名前 4 位）。\n\n"
     "文件命名：`YYYY-MM-DD-[修改摘要].md`。"),
```

- [ ] **Step 3: 在临时目录验证生成内容**

Run:
```bash
TMP=$(mktemp -d) && mkdir -p "$TMP/scripts" && \
cp skills/dum-knowledge-base-build/scripts/scaffold_docs_structure.py "$TMP/scripts/" && \
(cd "$TMP" && python3 scripts/scaffold_docs_structure.py >/dev/null) && \
grep -q "模块清单" "$TMP/docs/tech-design/README.md" && \
grep -q "按\*\*年\*\*分子目录\|按.*年.*分子目录" "$TMP/docs/modify_history/README.md" && \
echo OK || echo FAIL; rm -rf "$TMP"
```
Expected: `OK`。

- [ ] **Step 4: 提交**

```bash
git add skills/dum-knowledge-base-build/scripts/scaffold_docs_structure.py
git commit -m "feat(kb-build): scaffold tech-design 模块清单 README + modify_history 按年归档说明"
```

---

### Task 3: dum-solution-design SKILL.md——模块子目录 + 阈值三态

**Files:**
- Modify: `skills/dum-solution-design/SKILL.md`（Output Specification、Quick Reference、Common Mistakes、Red Flags 四处）

**Interfaces:**
- Consumes: 无（纯规则文件）。
- Produces: 规则正文，供 agent 落盘方案时遵循；下游 reconcile（Task 5）按相同子目录约定递归扫描。

- [ ] **Step 1: 替换「### 文件位置（强制）」整节**

把 `## Output Specification` 下「### 文件位置（强制）」到其代码块结束（含目录树示例）替换为：

````markdown
### 文件位置（强制）

所有方案文档放到项目的 `docs/tech-design/` 目录（**不是**项目根的 `方案设计/`、也**不是** `docs/` 根 或 `docs/product/`）。如果项目没有这个目录，先创建。

**少则平铺、多则按模块分子目录**：

```
项目根/docs/tech-design/
├── README.md                 # 模块清单（登记表）+ 命名约定
├── 20260425-FundamentalAnalyst.md          # 平铺 < 20 篇时直接放这层
├── auth/                                     # 平铺 ≥ 20 篇后按功能模块分子目录
│   └── 20260501-OAuthLogin.md
└── _misc/                                    # 不属任何模块的零散方案（兜底，可选）
```

### 按量自动分子目录（强制）

落盘新方案**前**，先数 `docs/tech-design/` 根目录下直接平铺的 `.md` 数（不含 README、不含子目录里的）：

| 状态 | 判定 | 动作 |
|---|---|---|
| 已分目录 | 根下已有非 README 子目录 | 读 `README.md` 模块清单：命中已有模块就放进 `<模块>/`；确属新模块才新建子目录 + 往清单补一行；都不沾放 `_misc/` |
| 未分 · 平铺 < 20 | 平铺数 < 20 | 直接平铺写入，不建子目录 |
| 未分 · 平铺 ≥ 20（首次触发） | 平铺数 ≥ 20 且无子目录 | ① 读现有方案标题/关键逻辑**语义聚类**出模块草案（模块名 + 文件→模块映射）→ ② **停下给用户确认/调整** → ③ `git mv` 建 `<模块>/` 搬文件、写 `README.md` 模块清单 → ④ 新方案写入对应子目录 |

**红线**：tech-design 首次分模块必须先出草案、等用户确认，**不可静默搬动存量文件**。
````

- [ ] **Step 2: 更新「### 文件命名（强制）」的强约束**

在该节「强约束」列表末尾追加一条：

```markdown
- 已分模块的项目，路径为 `docs/tech-design/<模块>/YYYYMMDD-方案名.md`，文件名规则不变
```

- [ ] **Step 3: 更新 Quick Reference 的「输出位置」行**

把 Quick Reference 表里 `| 输出位置 | `docs/tech-design/` |` 一行替换为：

```markdown
| 输出位置 | `docs/tech-design/`；平铺 ≥ 20 篇按模块分 `docs/tech-design/<模块>/`（首次分模块需出草案+用户确认） |
```

- [ ] **Step 4: Common Mistakes 加两行**

在 Common Mistakes 表末尾追加：

```markdown
| 平铺已 ≥ 20 篇仍不分模块 | 目录爆炸、难查哪篇属哪个模块 | 首次跨阈值出模块草案 → 确认 → 搬迁 |
| 新模块目录与已有同义（auth/ vs authentication/） | 同一模块文档分裂两处 | 落盘前查 `README.md` 模块清单，复用已登记模块名 |
```

- [ ] **Step 5: Red Flags 加一条**

在 `## Red Flags — STOP` 列表追加：

```markdown
- tech-design 平铺已 ≥ 20 篇却还在平铺塞 / 或未经确认就搬了存量文件 → 停，先出草案等确认
```

- [ ] **Step 6: 一致性自检**

Run: `grep -nE "20 篇|<模块>|模块清单|_misc" skills/dum-solution-design/SKILL.md`
Expected: 命中 Output / Quick Reference / Common Mistakes / Red Flags 各处，无遗漏；通读这几节无自相矛盾（阈值统一 20、首次需确认）。

- [ ] **Step 7: 提交**

```bash
git add skills/dum-solution-design/SKILL.md
git commit -m "feat(solution-design): tech-design 按模块分子目录 + 平铺≥20 自动触发(出草案+确认)"
```

---

### Task 4: dum-session-summary SKILL.md——按年子目录 + 阈值三态

**Files:**
- Modify: `skills/dum-session-summary/SKILL.md`（## 命名与位置约定、## 出口判断）

**Interfaces:**
- Consumes: 无。
- Produces: modify_history 落点改为 `docs/modify_history/<YYYY>/`，供 reconcile 按时间范围扫描时仍能命中（reconcile 已按 modify_history 全目录读取，年子目录不影响其遍历）。

- [ ] **Step 1: 替换「## 命名与位置约定」整节**

把该节替换为：

````markdown
## 命名与位置约定

- 路径：`docs/modify_history/YYYY-MM-DD-<标题>.md`；**平铺 ≥ 20 篇后**按年归档到 `docs/modify_history/<YYYY>/YYYY-MM-DD-<标题>.md`（年份取标题前 4 位）。
- 日期：`YYYY-MM-DD`（用户当前日期，非凭空）。
- 标题：简短描述性短语；空格换 `-`，去掉 `/ \ : * ? " < > |` 等非法字符；可中文。
- 同日多篇：追加 `-2`、`-3`。

**按量自动分子目录**：落盘前数 `docs/modify_history/` 根下平铺 `.md` 数（不含 README、不含年子目录）：

| 状态 | 动作 |
|---|---|
| 已有年子目录 | 直接写入当年目录 `docs/modify_history/<当年>/` |
| 平铺 < 20 | 平铺写入根目录 |
| 平铺 ≥ 20（首次触发） | 按每篇前 4 位年份 `git mv` 归档到 `<YYYY>/`，**announce 分了哪些年、各几篇**（机械、可逆，无需逐项确认）→ 新文档写入当年目录 |
````

- [ ] **Step 2: 更新「## 出口判断」加一条**

在出口判断列表追加：

```markdown
- ✅ 若 modify_history 平铺已 ≥ 20 篇：已按年归档（`<YYYY>/`）并 announce；新文档落在当年目录。
```

- [ ] **Step 3: 一致性自检**

Run: `grep -nE "<YYYY>|按年|20 篇" skills/dum-session-summary/SKILL.md`
Expected: 命名约定与出口判断各命中；阈值 20、年份取前 4 位表述一致。

- [ ] **Step 4: 提交**

```bash
git add skills/dum-session-summary/SKILL.md
git commit -m "feat(session-summary): modify_history 按年分子目录 + 平铺≥20 自动按年归档"
```

---

### Task 5: dum-doc-reconcile SKILL.md——递归 glob 修复 + 按模块限定

**Files:**
- Modify: `skills/dum-doc-reconcile/SKILL.md`（Phase 1 第 4 步、漂移报告模板路径示例、关键逻辑/难点）

**Interfaces:**
- Consumes: tech-design `<模块>/` 与 modify_history `<YYYY>/` 子目录（Task 3 / Task 4 产生）。
- Produces: 修复后的扫描规则，确保子目录里的设计文档不被漏扫。

- [ ] **Step 1: 修 Phase 1 第 4 步的 glob**

把 Phase 1 第 4 步里 `grep `docs/architecture/*.md` 与 `docs/tech-design/*.md`` 的表述替换为：

```markdown
4. **推断待校对清单**：把第 2、3 步得到的模块名/功能名/文件路径作为关键词，**递归** grep `docs/architecture/**/*.md` 与 `docs/tech-design/**/*.md`（用 `grep -r` 或等价递归，**务必含子目录**——tech-design 可能已按模块分 `<模块>/`），挑出描述了这些模块/功能、内容可能已不符的文档。去重；**只保留这两个目录内**的文档。若用户只点名某个模块，可把 tech-design 范围收窄到 `docs/tech-design/<模块>/`。
```

- [ ] **Step 2: 关键逻辑/难点加一条**

在「## 关键逻辑 / 难点」追加：

```markdown
- **递归扫子目录**：tech-design 平铺超阈值后会按模块分 `<模块>/` 子目录，扫描务必递归（`grep -r` / `**/*.md`），否则子目录里的方案文档会被整批漏掉——这是结构化后最容易踩的盲区。
```

- [ ] **Step 3: 常见错误加一行**

在「## 常见错误」表追加：

```markdown
| 用单层 `docs/tech-design/*.md` 扫描 | 漏掉已按模块分子目录的方案，漂移无人校 | 改递归 `grep -r` / `**/*.md` |
```

- [ ] **Step 4: 一致性自检**

Run: `grep -nE "递归|\*\*/\*.md|grep -r" skills/dum-doc-reconcile/SKILL.md`
Expected: Phase 1、关键逻辑、常见错误各命中；确认不再有"用 `docs/tech-design/*.md` 单层"未加递归提醒的残留。

- [ ] **Step 5: 提交**

```bash
git add skills/dum-doc-reconcile/SKILL.md
git commit -m "fix(doc-reconcile): Phase1 扫描改递归(含子目录)，防漏扫 tech-design 按模块子目录"
```

---

### Task 6: kb-build SKILL.md + CLAUDE 模板 + 根 CLAUDE.md——补子目录约定说明

**Files:**
- Modify: `skills/dum-knowledge-base-build/SKILL.md`（Overview 目录树注释 + 常见错误）
- Modify: `skills/dum-knowledge-base-build/assets/claude_md_root_template.md`（文档结构约定段，如含 tech-design/modify_history 描述）
- Modify: `CLAUDE.md`（本仓库技能清单，dum-solution-design / dum-doc-reconcile 行的一句话摘要可点到子目录约定，可选）

**Interfaces:**
- Consumes: Task 1–5 定下的约定。
- Produces: 文档说明，无运行时契约。

- [ ] **Step 1: kb-build SKILL.md 目录树注释**

把 Overview 目录树里 tech-design 与 modify_history 两行注释更新为：

```
│   ├── tech-design/           # 技术方案设计（YYYYMMDD-[标题].md；平铺≥20 按模块分 <模块>/，见 dum-solution-design）
│   ├── modify_history/        # 阶段总结/修改记录（平铺≥20 按年分 <YYYY>/，见 dum-session-summary）
```

- [ ] **Step 2: kb-build SKILL.md 常见错误加一行**

```markdown
| tech-design/modify_history 平铺到几十篇仍单层 | 难查、AI 难定位模块 | 交给 dum-solution-design / dum-session-summary 的「平铺≥20 自动分子目录」机制；索引脚本会在 docs-index 顶部出提示横幅 |
```

- [ ] **Step 3: 检查 root CLAUDE.md 模板是否需同步**

Run: `grep -nE "tech-design|modify_history" skills/dum-knowledge-base-build/assets/claude_md_root_template.md`
- 若命中且描述了这两类目录布局 → 在对应描述补「平铺≥20 自动分子目录（tech-design 按模块 / modify_history 按年）」一句。
- 若未命中 → 跳过本步（模板未细述目录，无需改），在提交信息里注明跳过原因。

- [ ] **Step 4: 本仓库根 CLAUDE.md（可选）**

打开根 `CLAUDE.md` 技能清单表，在 dum-solution-design 与 dum-session-summary 行的「何时用」摘要末尾各加一句「（文档多了自动按模块/按年分子目录）」。若觉得摘要已够长可跳过——此步为可选润色。

- [ ] **Step 5: 提交**

```bash
git add skills/dum-knowledge-base-build/SKILL.md \
        skills/dum-knowledge-base-build/assets/claude_md_root_template.md \
        CLAUDE.md
git commit -m "docs(kb-build): 补 tech-design 按模块/modify_history 按年子目录约定与阈值机制说明"
```

---

## 收尾（非任务，执行完后做）

- [ ] 通读 `docs/tech-design/20260626-DocStructureAutoSubdir.md` 方案与本 plan，确认 6 个 commit 覆盖方案 §3 全部难点（计数口径、tech-design 半自动、modify_history 按年、迁移折叠、递归扫描）。
- [ ] 决定是否删除重复的 brainstorming spec（`docs/superpowers/specs/2026-06-26-...-design.md`），二选一保留。
- [ ] 视情况 bump 各 agent manifest 版本号（参照最近 commit `6a20a92` 的版本补齐惯例）。

## Self-Review 记录

- **Spec coverage**：§D1–D8 / 方案 §1–§4 均有任务覆盖——分层(Task3/4)、模块治理(Task2/3)、自动触发(Task3/4)、阈值(Global+Task1)、tech-design 确认门(Task3)、modify_history 按年(Task4)、迁移折叠(Task3/4 首次触发步)、索引(Task1)、reconcile 修复(Task5)、文档说明(Task6)。无遗漏。
- **Placeholder scan**：无 TBD/TODO/"类似 Task N"；每个 markdown 替换块给了完整文本，每个 Python 步给了完整代码。
- **Type consistency**：`flat_count(dirname)`、`SUBDIR_THRESHOLDS`、`build_index_text()` 在 Task1 内部及测试中签名一致；阈值 20 全程统一；「已分目录=根下有非README子目录」定义在 Global 与 Task3/4 一致。
