#!/usr/bin/env python3
"""文档索引自动更新脚本（dum-architecture-doc-build skill 模板）。

按约定的文档体系扫描 `docs/` 下各分类目录，渲染出**按分类分节**的文档索引，
写进 `docs/reference/docs-index.md` 的 DOCS-INDEX 区。是 `update_architecture_*.py`
（源码清单）的姊妹脚本——那个回答「代码在哪」，这个回答「文档在哪」。

设计：
- 幂等：内容没变就不重写（含时间戳）。
- 静默：目标文件 / marker 缺失时 exit 0。
- 自我过滤：hook 触发时只在被改的是 `.md` 时才跑。
- 与源码脚本不同：把**描述也纳入对比**（标题改了也刷新），并解析 `YYYYMMDD-标题.md`
  文件名，按日期倒序排，每类成节。

用法（手动）：
    python3 scripts/update_docs_index.py
用法（hook）：
    .claude/settings.local.json 的 PostToolUse → Write|Edit 触发，10s timeout
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ============================================================================
# 项目配置 — 复制脚本到新项目后只需要改这一段
# ============================================================================

# 1) 索引文件位置 + docs 根（相对项目根）
DOCS_INDEX_MD_REL = "docs/reference/docs-index.md"
DOCS_ROOT_REL = "docs"

# 2) 分类顺序与中文标题 —— 必须与 scaffold_docs_structure.py 的 CATEGORIES 对齐。
CATEGORIES: list[tuple[str, str]] = [
    ("architecture", "架构文档"),
    ("specification", "规范文档"),
    ("product-design", "产品设计"),
    ("tech-design", "技术方案"),
    ("superpowers", "Superpowers 产出"),
    ("modify_history", "修改记录"),
    ("deffered", "待办"),
    ("manual_deployment", "部署文档"),
    ("manual_userguides", "用户手册"),
    ("report", "分析报告"),
    ("reference", "参考资料"),
]

# 3) 算作"文档"的扩展名
DOC_EXTENSIONS: set[str] = {".md"}

# 4) 不进索引的文件名（目录说明 / 索引自身）
EXCLUDE_FILES: set[str] = {"README.md", "docs-index.md"}

# 5) 排除目录
EXCLUDE_DIRS: set[str] = {"node_modules", "__pycache__", ".git"}

# ============================================================================
# 以下不需要改
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DOCS_INDEX_MD = PROJECT_ROOT / DOCS_INDEX_MD_REL
DOCS_ROOT = PROJECT_ROOT / DOCS_ROOT_REL
INDEX_DIR = DOCS_INDEX_MD.parent

START_MARKER = "<!-- DOCS-INDEX:START -->"
END_MARKER = "<!-- DOCS-INDEX:END -->"

# YYYYMMDD-标题 / YYYY-MM-DD-标题 / YYYY_MM_DD 标题
_DATE_RE = re.compile(r"^(\d{4})[-_]?(\d{2})[-_]?(\d{2})[-_ ]*(.*?)$")
_MD_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
_FRONTMATTER_KEY_RE = re.compile(r"^(title|description)\s*:\s*(.+?)\s*$", re.IGNORECASE)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")


def _clean(text: str) -> str:
    text = _MD_LINK_RE.sub(r"\1", text)
    text = text.replace("`", "").replace("[", "").replace("]", "")
    return text.strip().strip("\"'").strip()[:90]


def extract_doc_title(filepath: Path) -> str:
    """frontmatter title/description → 首个 # 标题 → 首行非空正文。"""
    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except (OSError, UnicodeDecodeError):
        return ""
    if lines and lines[0].strip() == "---":
        for line in lines[1:40]:
            if line.strip() == "---":
                break
            m = _FRONTMATTER_KEY_RE.match(line.strip())
            if m:
                return _clean(m.group(2))
    in_code = False
    for line in lines[:80]:
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = _MD_HEADING_RE.match(line)
        if m:
            return _clean(m.group(1))
    for line in lines[:80]:
        s = line.strip()
        if s and not s.startswith(("<!--", "---", "```", "|", ">")):
            return _clean(s)
    return ""


def parse_filename(stem: str) -> tuple[str | None, str]:
    """从文件名 stem 解析 (ISO 日期 或 None, 文件名里的标题)。"""
    m = _DATE_RE.match(stem)
    if m:
        y, mo, d, rest = m.groups()
        try:
            datetime(int(y), int(mo), int(d))
            return f"{y}-{mo}-{d}", (rest.strip() or stem)
        except ValueError:
            pass
    return None, stem


def _rel_link(filepath: Path) -> str:
    rel = os.path.relpath(filepath, INDEX_DIR)
    return rel.replace(os.sep, "/")


def collect_category(dirname: str) -> list[tuple[str | None, str, str]]:
    """返回该分类下的 (date, link_text, rel_link)，已排序（有日期者倒序在前）。"""
    base = DOCS_ROOT / dirname
    entries: list[tuple[str | None, str, str]] = []
    if not base.exists():
        return entries
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith("."))
        dp = Path(dirpath)
        for fname in sorted(filenames):
            if Path(fname).suffix not in DOC_EXTENSIONS or fname in EXCLUDE_FILES:
                continue
            fpath = dp / fname
            date, fname_title = parse_filename(Path(fname).stem)
            title = extract_doc_title(fpath) or fname_title
            # 子目录（如按模块分）→ 在标题前标出相对子路径
            rel_within = fpath.relative_to(base)
            if len(rel_within.parts) > 1:
                prefix = "/".join(rel_within.parts[:-1])
                title = f"{prefix}/ {title}"
            entries.append((date, title, _rel_link(fpath)))
    dated = sorted((e for e in entries if e[0]), key=lambda e: e[0], reverse=True)
    undated = sorted((e for e in entries if not e[0]), key=lambda e: e[1])
    return dated + undated


def build_index_text() -> str:
    blocks: list[str] = []
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


# ---------- 写文件（内容变化才更新） ----------

def _existing_region(content: str, s: int, e: int) -> str:
    region = content[s + len(START_MARKER):e]
    out = [ln for ln in region.split("\n") if not ln.strip().startswith("<!--")]
    return "\n".join(out).strip()


def update_index(body: str) -> bool:
    if not DOCS_INDEX_MD.exists():
        return False
    content = DOCS_INDEX_MD.read_text(encoding="utf-8")
    s = content.find(START_MARKER)
    e = content.find(END_MARKER)
    if s == -1 or e == -1 or s >= e:
        print(f"WARNING: DOCS-INDEX markers missing in {DOCS_INDEX_MD}", file=sys.stderr)
        return False
    if _existing_region(content, s, e) == body.strip():
        return False
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    replacement = (
        f"{START_MARKER}\n"
        f"<!-- 自动生成，请勿手动编辑此区域 | Auto-generated, do not edit manually -->\n"
        f"<!-- 最后更新: {ts} -->\n\n"
        f"{body}\n"
    )
    DOCS_INDEX_MD.write_text(content[:s] + replacement + content[e:], encoding="utf-8")
    return True


# ---------- Hook 过滤 ----------

def is_triggered_by_relevant_file() -> bool:
    raw = os.environ.get("CLAUDE_TOOL_USE_INPUT")
    if not raw:
        return True
    try:
        fp = json.loads(raw).get("file_path", "")
    except (json.JSONDecodeError, TypeError):
        fp = raw
    if not fp:
        return False
    return any(fp.endswith(ext) for ext in DOC_EXTENSIONS)


def main() -> None:
    if not DOCS_INDEX_MD.exists():
        sys.exit(0)
    if not is_triggered_by_relevant_file():
        sys.exit(0)
    body = build_index_text()
    if update_index(body):
        total = sum(len(collect_category(d)) for d, _ in CATEGORIES)
        print(f"Updated {DOCS_INDEX_MD.relative_to(PROJECT_ROOT)} ({total} docs indexed)")
    sys.exit(0)


if __name__ == "__main__":
    main()
