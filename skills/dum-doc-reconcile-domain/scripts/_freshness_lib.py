"""模块现状权威文档 · 鲜度判定纯函数库。仅 stdlib + pyyaml。"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

_DATE_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})-")

FRESH_START = "<!-- FRESHNESS:START -->"
FRESH_END = "<!-- FRESHNESS:END -->"


def parse_frontmatter(text: str) -> dict:
    """读取 Markdown 头部 --- YAML --- 块；无则返回 {}。"""
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def parse_dated_prefix(filename: str) -> str | None:
    """'20260623-xxx.md' -> '2026-06-23'；无 YYYYMMDD- 前缀返回 None。"""
    m = _DATE_RE.match(filename)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def source_commits_since(repo: Path, since_ref: str, paths: list[str]) -> list[str]:
    """since_ref..HEAD 中触及 paths 的 short hash；空 ref / 坏 ref 视为需校对。"""
    if not since_ref:
        return ["<uninitialized>"]
    cmd = ["git", "-C", str(repo), "log", "--format=%h",
           f"{since_ref}..HEAD", "--", *paths]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             check=True).stdout
    except subprocess.CalledProcessError:
        return ["<bad-ref>"]
    return [ln for ln in out.splitlines() if ln.strip()]


def compute_status(n_commits: int, n_dated: int) -> tuple[str, str]:
    """计算鲜度状态。

    Args:
        n_commits: 相关提交数
        n_dated: 新方案数（带日期前缀的文件数）

    Returns:
        ("fresh", "") 或 ("stale", "N 次相关提交 / M 份新方案")
    """
    if n_commits == 0 and n_dated == 0:
        return ("fresh", "")
    bits = []
    if n_commits:
        bits.append(f"{n_commits} 次相关提交")
    if n_dated:
        bits.append(f"{n_dated} 份新方案")
    return ("stale", " / ".join(bits))


def render_freshness_table(rows: list[dict]) -> str:
    """渲染鲜度表格 Markdown。

    Args:
        rows: 行列表，每行需包含 doc, type, last_reconciled, status, detail

    Returns:
        Markdown 表格文本
    """
    lines = ["| 文档 | 类型 | last-reconciled | 状态 |", "|---|---|---|---|"]
    for r in rows:
        badge = "🟢 新鲜" if r["status"] == "fresh" else f"🟡 {r['detail']}"
        lines.append(
            f"| {r['doc']} | {r['type']} | {r['last_reconciled']} | {badge} |")
    return "\n".join(lines)


def splice_region(content: str, replacement: str, start: str, end: str) -> str:
    """替换或插入 Markdown 区块。

    Args:
        content: 原始内容
        replacement: 要插入/替换的内容
        start: 开始标记
        end: 结束标记

    Returns:
        替换后的内容。如果标记存在则替换，否则在末尾追加鲜度总览段。
    """
    block = f"{start}\n{replacement}\n{end}"
    s = content.find(start)
    e = content.find(end)
    if s == -1 or e == -1:
        sep = "" if content.endswith("\n") else "\n"
        return f"{content}{sep}\n## 鲜度总览\n{block}\n"
    return content[:s] + block + content[e + len(end):]
