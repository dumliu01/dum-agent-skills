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
