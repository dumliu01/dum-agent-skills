#!/usr/bin/env python3
"""通用架构文档目录清单自动更新脚本（dum-knowledge-base-build skill 模板）。

复制本文件到目标项目（建议路径：`<project>/scripts/update_architecture_<service>.py`），
然后修改 §"项目配置" 段。

设计原则（lifted from termcat_*/scripts/update_architecture_manifest.py）：
- 幂等：多次运行结果一致（除时间戳外）
- 静默：架构 markdown 不存在或标记缺失时 exit 0
- 自我过滤：hook 触发时通过 CLAUDE_TOOL_USE_INPUT.file_path 判断是否本服务文件
- 仅在树形结构变化时重写时间戳（描述抖动不算）

用法（手动）：
    python3 scripts/update_architecture_<service>.py
用法（hook）：
    .claude/settings.local.json 的 PostToolUse → Write|Edit 触发，10s timeout
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ============================================================================
# 项目配置 — 复制脚本到新项目后只需要改这一段
# ============================================================================

# 1) 架构 markdown 文件位置（相对项目根）
ARCHITECTURE_MD_REL = "docs/architecture/<service>.md"   # ← 改成实际路径

# 2) 要扫描的子目录（相对项目根）。一服务一脚本，只列本服务的目录。
SCAN_SUBDIRS: list[str] = [
    # "apps/api",
    # "core",
    # "infra",
]

# 3) hook 触发关键字。脚本会查 CLAUDE_TOOL_USE_INPUT.file_path 是否包含其中任一。
#    通常等于 SCAN_SUBDIRS（避免无关服务的 Write/Edit 也跑这个脚本）。
TRIGGER_KEYWORDS: tuple[str, ...] = tuple(SCAN_SUBDIRS)

# 4) 包含的扩展名。后端 .py / 前端 .ts .vue / Go .go / Rust .rs / ...
INCLUDE_EXTENSIONS: set[str] = {".py", ".yaml", ".yml"}   # ← 按语言改

# 5) 描述提取器名称（见下方"内置提取器"）
EXTRACTOR = "extract_python_docstring"   # 也可填 "extract_first_comment" 等

# 6) 树根那一行显示的标签
ROOT_LABEL = "<service>"   # ← 改成 e.g. "myproject (backend)"

# 7) 是否剥掉 SCAN 入口前缀（前端 apps/web/src 这种深嵌套场景设 True）。
#    True  → 树以 SCAN_SUBDIRS[0] 为相对根（apps/web/src/main.ts → main.ts）
#    False → 树以项目根为相对根（apps/api/main.py → apps/api/main.py）
STRIP_SCAN_PREFIX = False

# 8) 排除目录（统一加在 SCAN_SUBDIRS 内部 walk 时跳过）
EXCLUDE_DIRS: set[str] = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".vite",
    ".cache",
}

# ============================================================================
# 以下不需要改（除非有特殊需求）
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ARCHITECTURE_MD = PROJECT_ROOT / ARCHITECTURE_MD_REL

START_MARKER = "<!-- AUTO-GENERATED:START -->"
END_MARKER = "<!-- AUTO-GENERATED:END -->"

# 提取器：// xxx
_LINE_COMMENT_RE = re.compile(r"^\s*//\s*(.+?)\s*$")
# 提取器：单行块 /* xxx */
_BLOCK_COMMENT_RE = re.compile(r"^\s*/\*+\s*(.+?)\s*\*+/\s*$")
# 提取器：单行 JSDoc /** xxx */
_JSDOC_INLINE_RE = re.compile(r"^\s*/\*\*\s*(.+?)\s*\*/\s*$")
# 提取器：YAML 首行 # xxx
_YAML_COMMENT_RE = re.compile(r"^\s*#\s*(.+?)\s*$")


# ---------- 内置提取器 ----------

def extract_python_docstring(filepath: Path) -> str:
    if filepath.suffix != ".py":
        return ""
    try:
        src = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, filename=str(filepath))
        ds = ast.get_docstring(tree)
        if ds:
            return ds.strip().split("\n")[0].strip()
    except (SyntaxError, UnicodeDecodeError, ValueError):
        pass
    return ""


def extract_first_comment(filepath: Path) -> str:
    """适用于 .ts/.vue/.go/.rs/.c/.cpp/.java 等用 // 或 /* */ 风格的语言。

    .vue 特殊处理：先定位到第一个 <script> 块。
    自动过滤明显的 path-banner 注释（如 `// apps/web/src/foo.ts`）。
    """
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return ""

    if filepath.suffix == ".vue":
        m = re.search(r"<script[^>]*>([\s\S]*?)</script>", text, re.IGNORECASE)
        if m:
            text = m.group(1)

    candidates: list[str] = []
    for line in text.splitlines()[:30]:
        stripped = line.strip()
        if not stripped:
            continue
        m = _JSDOC_INLINE_RE.match(line)
        if m:
            candidates.append(m.group(1))
            continue
        m = _BLOCK_COMMENT_RE.match(line)
        if m:
            candidates.append(m.group(1))
            continue
        m = _LINE_COMMENT_RE.match(line)
        if m:
            candidates.append(m.group(1))
            continue
        if not stripped.startswith(("import", "export", "//", "/*", "*", "<!", "package ")):
            break

    rel = str(filepath.relative_to(PROJECT_ROOT))
    for cand in candidates:
        # 跳过 path banner（与文件路径相同 / 路径状字符串）
        if cand == rel or "/" in cand and cand.endswith(tuple(INCLUDE_EXTENSIONS)):
            continue
        return cand
    return ""


def extract_yaml_top_comment(filepath: Path) -> str:
    if filepath.suffix not in (".yaml", ".yml"):
        return ""
    try:
        for line in filepath.read_text(encoding="utf-8", errors="replace").splitlines()[:5]:
            m = _YAML_COMMENT_RE.match(line)
            if m:
                return m.group(1)
    except (OSError, UnicodeDecodeError):
        pass
    return ""


# 路由表 — 主调用 _extract_description 时按 EXTRACTOR 分发
_EXTRACTORS = {
    "extract_python_docstring": extract_python_docstring,
    "extract_first_comment": extract_first_comment,
    "extract_yaml_top_comment": extract_yaml_top_comment,
}


def _extract_description(filepath: Path) -> str:
    """按 EXTRACTOR 路由；对 YAML 文件无论 EXTRACTOR 设啥都用 yaml 提取器。"""
    if filepath.suffix in (".yaml", ".yml"):
        return extract_yaml_top_comment(filepath)
    fn = _EXTRACTORS.get(EXTRACTOR)
    if fn is None:
        print(f"WARNING: unknown EXTRACTOR {EXTRACTOR!r}", file=sys.stderr)
        return ""
    return fn(filepath)


# ---------- 扫描 + 树形渲染 ----------

def _should_exclude(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def scan_files() -> list[tuple[Path, str]]:
    """扫描 SCAN_SUBDIRS 下的所有源文件，返回 (相对路径, 描述)。"""
    results: list[tuple[Path, str]] = []
    for sub in SCAN_SUBDIRS:
        base = PROJECT_ROOT / sub
        if not base.exists():
            continue
        # 决定相对根：True 时以 base 为根（去掉 sub 前缀）；False 时以项目根为根
        rel_root = base if STRIP_SCAN_PREFIX else PROJECT_ROOT
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
            dp = Path(dirpath)
            for fname in sorted(filenames):
                fpath = dp / fname
                if fpath.suffix not in INCLUDE_EXTENSIONS:
                    continue
                rel_check = fpath.relative_to(PROJECT_ROOT)
                if _should_exclude(rel_check):
                    continue
                rel = fpath.relative_to(rel_root)
                results.append((rel, _extract_description(fpath)))
    return results


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
        items = list(node.items())
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
                    padding = max(2, 55 - len(entry))
                    lines.append(f"{entry}{' ' * padding}# {value}")
                else:
                    lines.append(entry)

    render(tree)
    return "\n".join(lines)


# ---------- 写文件（仅结构变化才更新） ----------

def _strip_descriptions(tree_text: str) -> str:
    out: list[str] = []
    for line in tree_text.split("\n"):
        idx = line.find("  # ")
        if idx != -1:
            line = line[:idx]
        out.append(line.rstrip())
    return "\n".join(out)


def _extract_existing_tree(content: str, s: int, e: int) -> str:
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


def update_architecture_md(tree_text: str) -> bool:
    if not ARCHITECTURE_MD.exists():
        return False
    content = ARCHITECTURE_MD.read_text(encoding="utf-8")
    s = content.find(START_MARKER)
    e = content.find(END_MARKER)
    if s == -1 or e == -1 or s >= e:
        print(f"WARNING: markers missing in {ARCHITECTURE_MD}", file=sys.stderr)
        return False

    existing = _extract_existing_tree(content, s, e)
    if _strip_descriptions(existing) == _strip_descriptions(tree_text):
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
    ARCHITECTURE_MD.write_text(content[:s] + replacement + content[e:], encoding="utf-8")
    return True


# ---------- Hook 过滤 ----------

def is_triggered_by_relevant_file() -> bool:
    raw = os.environ.get("CLAUDE_TOOL_USE_INPUT")
    if not raw:
        return True  # 手动调用一律执行
    try:
        tool_input = json.loads(raw)
        fp = tool_input.get("file_path", "")
    except (json.JSONDecodeError, TypeError):
        fp = raw
    if not fp:
        return False
    return any(kw in fp for kw in TRIGGER_KEYWORDS)


# ---------- 入口 ----------

def main() -> None:
    if not ARCHITECTURE_MD.exists():
        sys.exit(0)
    if not is_triggered_by_relevant_file():
        sys.exit(0)
    files = scan_files()
    tree = build_tree_text(files)
    if update_architecture_md(tree):
        print(f"Updated {ARCHITECTURE_MD.relative_to(PROJECT_ROOT)} ({len(files)} files)")
    sys.exit(0)


if __name__ == "__main__":
    main()
