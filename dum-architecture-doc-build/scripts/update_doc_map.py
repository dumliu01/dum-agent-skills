#!/usr/bin/env python3
"""项目级「文档地图 / 知识库索引」自动更新脚本（dum-architecture-doc-build skill 模板）。

跟 `update_architecture_manifest.py` 是姊妹脚本：
- manifest 脚本回答「**源码**有哪些、在哪些目录」（一服务一脚本，扫 SCAN_SUBDIRS）
- 本脚本回答「**文档**有哪些、在哪些目录」（一项目一脚本，扫全项目的 .md）

复制本文件到目标项目（建议路径：`<project>/scripts/update_doc_map.py`），
然后修改 §"项目配置" 段。

设计原则（与 manifest 脚本一致）：
- 幂等：多次运行结果一致（除时间戳外）
- 静默：目标 markdown 不存在或 DOC-MAP 标记缺失时 exit 0
- 自我过滤：hook 触发时按"被改文件是不是文档"判断要不要跑
- 与 manifest 不同点：文档地图的价值在**描述本身**，所以标题/首行变化也会触发更新
  （manifest 为了避免 commit 噪音，只在树形结构变化时才重写）

用法（手动）：
    python3 scripts/update_doc_map.py
用法（hook）：
    .claude/settings.local.json 的 PostToolUse → Write|Edit 触发，10s timeout
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

# ============================================================================
# 项目配置 — 复制脚本到新项目后只需要改这一段
# ============================================================================

# 1) 文档地图写入哪个 markdown（相对项目根）。
#    约定放在架构文档索引页里；单服务项目也可直接指向那一份架构文档。
DOC_MAP_MD_REL = "docs/architecture/README.md"   # ← 改成实际路径

# 2) 要扫描的目录（相对项目根）。默认 ["."] = 全项目（靠 EXCLUDE_DIRS 兜底）。
#    噪音太多时收窄成白名单，比如 ["docs", "方案设计", "claude_refs", "."]。
#    注意：列了 "." 就是整棵树，再列别的子目录会重复，二选一。
DOC_SCAN_DIRS: list[str] = ["."]

# 3) 算作"文档"的扩展名。默认只认 Markdown；按需加 .mdx / .rst / .adoc / .txt。
DOC_EXTENSIONS: set[str] = {".md"}

# 4) 树根那一行显示的标签（通常是项目名）。
ROOT_LABEL = "<project>"   # ← 改成 e.g. "myproject"

# 5) 排除目录（walk 到这些名字直接跳过；另外所有 dotdir 默认也跳过）。
EXCLUDE_DIRS: set[str] = {
    "node_modules",
    "vendor",
    "site-packages",
    "dist",
    "build",
    "target",
    "coverage",
    "htmlcov",
    "__pycache__",
    "venv",
}

# 6) 排除文件名（噪音文档：依赖自带的、机器生成的）。按需加。
EXCLUDE_FILES: set[str] = {
    "CHANGELOG.md",   # 大多是机器生成，不属于"知识库"
    "LICENSE.md",
}

# ============================================================================
# 以下不需要改（除非有特殊需求）
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DOC_MAP_MD = PROJECT_ROOT / DOC_MAP_MD_REL

START_MARKER = "<!-- DOC-MAP:START -->"
END_MARKER = "<!-- DOC-MAP:END -->"

# Markdown 标题：# 到 ###### ，去掉尾随的 #
_MD_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
# YAML frontmatter 里的 title: / description:
_FRONTMATTER_KEY_RE = re.compile(r"^(title|description)\s*:\s*(.+?)\s*$", re.IGNORECASE)
# [文字](链接) → 文字
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")


def _clean(text: str) -> str:
    """去掉 markdown 链接/反引号/引号，截断到 80 字。"""
    text = _MD_LINK_RE.sub(r"\1", text)
    text = text.replace("`", "").strip().strip("\"'").strip()
    return text[:80]


def extract_doc_title(filepath: Path) -> str:
    """文档描述提取：frontmatter title/description → 首个 # 标题 → 首行非空文本。"""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return ""
    lines = text.splitlines()

    # 1) YAML frontmatter 块内的 title / description
    if lines and lines[0].strip() == "---":
        for line in lines[1:40]:
            if line.strip() == "---":
                break
            m = _FRONTMATTER_KEY_RE.match(line.strip())
            if m:
                return _clean(m.group(2))

    # 2) 第一个 markdown 标题
    in_code = False
    for line in lines[:80]:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = _MD_HEADING_RE.match(line)
        if m:
            return _clean(m.group(1))

    # 3) 第一行非空、非标记的正文
    for line in lines[:80]:
        stripped = line.strip()
        if stripped and not stripped.startswith(("<!--", "---", "```", "|", ">")):
            return _clean(stripped)
    return ""


# ---------- 扫描 + 树形渲染 ----------

def _should_exclude_dir(name: str) -> bool:
    return name in EXCLUDE_DIRS or name.startswith(".")


def scan_docs() -> list[tuple[Path, str]]:
    """扫描 DOC_SCAN_DIRS 下的所有文档，返回 (项目根相对路径, 标题)。"""
    results: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for sub in DOC_SCAN_DIRS:
        base = (PROJECT_ROOT / sub).resolve()
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if not _should_exclude_dir(d))
            dp = Path(dirpath)
            for fname in sorted(filenames):
                if Path(fname).suffix not in DOC_EXTENSIONS:
                    continue
                if fname in EXCLUDE_FILES:
                    continue
                fpath = dp / fname
                rel = fpath.relative_to(PROJECT_ROOT)
                if rel in seen:
                    continue
                seen.add(rel)
                results.append((rel, extract_doc_title(fpath)))
    return results


def _display_width(text: str) -> int:
    """CJK 全角字符算 2 列，用来对齐树形里的 `# 描述` 注释。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def build_tree_text(files: list[tuple[Path, str]]) -> str:
    tree: dict = {}
    for rel, desc in files:
        node = tree
        parts = rel.parts
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = desc

    lines: list[str] = [f"{ROOT_LABEL}/"]

    def render(node: dict, prefix: str = "") -> None:
        # 目录在前、文件在后，各自按名字排序 → 输出稳定
        items = sorted(node.items(), key=lambda kv: (not isinstance(kv[1], dict), kv[0]))
        for i, (name, value) in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "
            if isinstance(value, dict):
                lines.append(f"{prefix}{connector}{name}/")
                render(value, prefix + extension)
            else:
                entry = f"{prefix}{connector}{name}"
                if value:
                    padding = max(2, 60 - _display_width(entry))
                    lines.append(f"{entry}{' ' * padding}# {value}")
                else:
                    lines.append(entry)

    render(tree)
    return "\n".join(lines)


# ---------- 写文件（内容变化才更新；含描述） ----------

def _extract_existing_region(content: str, s: int, e: int) -> str:
    region = content[s + len(START_MARKER):e]
    in_code = False
    out: list[str] = []
    for line in region.strip().split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if stripped.startswith("<!--"):
            continue
        if in_code:
            out.append(line)
    return "\n".join(out).strip()


def update_doc_map_md(tree_text: str) -> bool:
    if not DOC_MAP_MD.exists():
        return False
    content = DOC_MAP_MD.read_text(encoding="utf-8")
    s = content.find(START_MARKER)
    e = content.find(END_MARKER)
    if s == -1 or e == -1 or s >= e:
        print(f"WARNING: DOC-MAP markers missing in {DOC_MAP_MD}", file=sys.stderr)
        return False

    # 文档地图把描述也纳入对比：标题/首行变了也要刷新（与 manifest 脚本不同）
    if _extract_existing_region(content, s, e) == tree_text.strip():
        return False

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    replacement = (
        f"{START_MARKER}\n"
        f"<!-- 自动生成，请勿手动编辑此区域 | Auto-generated, do not edit manually -->\n"
        f"<!-- 最后更新: {ts} -->\n"
        f"\n"
        f"```\n"
        f"{tree_text}\n"
        f"```\n"
        f"\n"
    )
    DOC_MAP_MD.write_text(content[:s] + replacement + content[e:], encoding="utf-8")
    return True


# ---------- Hook 过滤 ----------

def is_triggered_by_relevant_file() -> bool:
    """hook 触发时只在被改文件是文档（DOC_EXTENSIONS）时才跑；手动调用一律跑。"""
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


# ---------- 入口 ----------

def main() -> None:
    if not DOC_MAP_MD.exists():
        sys.exit(0)
    if not is_triggered_by_relevant_file():
        sys.exit(0)
    files = scan_docs()
    tree = build_tree_text(files)
    if update_doc_map_md(tree):
        print(f"Updated {DOC_MAP_MD.relative_to(PROJECT_ROOT)} ({len(files)} docs)")
    sys.exit(0)


if __name__ == "__main__":
    main()
