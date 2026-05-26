#!/usr/bin/env python3
"""一次性脚手架：建立项目知识库的标准 docs/ 结构（dum-knowledge-base-build skill）。

按约定的文档体系创建 docs/ 下全部子目录，每个目录放一份 README.md 说明用途和
文件命名规范；并生成 docs/docs-index.md 的骨架（带 DOCS-INDEX marker，
之后由 update_docs_index.py 自动维护内容）。

特性：
- 幂等：已存在的目录/文件**不覆盖**（保护用户已有内容），只补缺的。
- 不碰 CLAUDE.md：根 / 子项目的 CLAUDE.md 由 Claude 用模板填实际内容（保护已有）。

用法：
    python3 scripts/scaffold_docs_structure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DOCS = PROJECT_ROOT / "docs"

# ============================================================================
# 文档体系定义 — (目录名, 中文标题, README 正文)
# 顺序即 docs-index.md 里的分类顺序。改这里就能调整整套结构。
# ============================================================================

NAMING = "文件命名：`YYYYMMDD-[标题].md`（如 `20260525-登录功能.md`），按日期排序。"

CATEGORIES: list[tuple[str, str, str]] = [
    ("architecture", "架构文档",
     "保存每个子项目的核心架构文档，文件名 `<子项目>.md`（如 `backend.md` / `frontend.md`）。\n"
     "每份文档的源码目录清单由 `scripts/update_architecture_<service>.py` 自动维护。"),
    ("specification", "规范文档",
     "编程与工程规范：编码风格、命名约定、提交/分支策略、测试规范、评审规范等。\n"
     "文件名自描述，不加日期前缀（规范是长期有效的，不是按时间归档）。"),
    ("product-design", "产品设计",
     "产品（需求）设计文档。可按子项目或模块再分子目录。\n" + NAMING),
    ("tech-design", "技术方案",
     "技术方案设计文档。可按子项目或模块再分子目录。\n"
     "dum-solution-design skill 的方案产出落到这里。\n" + NAMING),
    ("superpowers", "Superpowers 产出",
     "superpowers 工作流产生的技术与执行文档。子目录：`plans/`（实施计划）、`specs/`（规格）。\n" + NAMING),
    ("modify_history", "修改记录",
     "阶段总结与修改记录（每个里程碑/阶段一份）。\n"
     "文件命名：`YYYYMMDD-[修改摘要].md`。"),
    ("deffered", "待办",
     "待办 / 暂缓事项文档（记录决定推迟、但不能丢的工作）。\n"
     "文件命名：`YYYYMMDD-[摘要].md`。"),
    ("manual_deployment", "部署文档",
     "部署手册：环境要求、部署流程、配置项、回滚步骤、运维注意事项。"),
    ("manual_userguides", "用户手册",
     "面向最终用户的使用手册 / 操作指南。"),
    ("report", "分析报告",
     "分析报告：性能分析、调研、复盘、数据分析等。\n" + NAMING),
    ("reference", "参考资料",
     "参考资料与外部链接收集（dashboard 链接、外部文档指针、ADR 参考等）。\n"
     "注：全项目文档索引 `docs-index.md` 在 `docs/` 根目录下（不在本目录），\n"
     "由 `scripts/update_docs_index.py` 自动维护。"),
]

# superpowers 的子目录
SUBDIRS: dict[str, list[tuple[str, str]]] = {
    "superpowers": [
        ("plans", "实施计划文档（superpowers 产出）。命名 `YYYYMMDD-[标题].md`。"),
        ("specs", "规格 / 规范文档（superpowers 产出）。命名 `YYYYMMDD-[标题].md`。"),
    ],
}

DOCS_INDEX_REL = "docs/docs-index.md"
INDEX_START = "<!-- DOCS-INDEX:START -->"
INDEX_END = "<!-- DOCS-INDEX:END -->"


def _write_if_absent(path: Path, content: str, created: list[str], skipped: list[str]) -> None:
    if path.exists():
        skipped.append(str(path.relative_to(PROJECT_ROOT)))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(str(path.relative_to(PROJECT_ROOT)))


def _readme(title: str, dirname: str, body: str) -> str:
    return f"# {title}（`docs/{dirname}/`）\n\n{body}\n"


def build_index_skeleton() -> str:
    return (
        "# 文档索引 docs-index.md\n\n"
        "> 📚 全项目文档总索引。下方「文档清单」区由 `scripts/update_docs_index.py` 自动维护，\n"
        "> 通过 Claude Code Hook（PostToolUse → Write|Edit）在任意 `docs/**/*.md` 变更后刷新。\n"
        "> 想让某份文档在索引里显示得清楚，就给它写个好的一级 `#` 标题或 frontmatter `title`。\n\n"
        "## 文档清单（自动生成区域）\n\n"
        f"{INDEX_START}\n"
        "<!-- 占位：首次运行 scripts/update_docs_index.py 后自动填充 -->\n"
        "(pending first run)\n"
        f"{INDEX_END}\n"
    )


def main() -> None:
    created: list[str] = []
    skipped: list[str] = []

    DOCS.mkdir(parents=True, exist_ok=True)

    for dirname, title, body in CATEGORIES:
        d = DOCS / dirname
        d.mkdir(parents=True, exist_ok=True)
        _write_if_absent(d / "README.md", _readme(title, dirname, body), created, skipped)
        for sub, sub_body in SUBDIRS.get(dirname, []):
            sd = d / sub
            sd.mkdir(parents=True, exist_ok=True)
            _write_if_absent(
                sd / "README.md",
                _readme(f"{title} · {sub}", f"{dirname}/{sub}", sub_body),
                created, skipped,
            )

    _write_if_absent(PROJECT_ROOT / DOCS_INDEX_REL, build_index_skeleton(), created, skipped)

    print(f"docs/ 结构脚手架完成：新建 {len(created)} 个文件，跳过 {len(skipped)} 个已存在文件。")
    for c in created:
        print(f"  + {c}")
    if skipped:
        print(f"  （已存在、未改动：{', '.join(skipped)}）")
    print("\n下一步：")
    print("  1) 用 assets/claude_md_*_template.md 写根 / 各子项目 CLAUDE.md（已存在则只补缺失段，勿覆盖）")
    print("  2) 用 assets/arch_doc_template.md 写 docs/architecture/<service>.md")
    print("  3) 配置并跑 scripts/update_architecture_<service>.py + scripts/update_docs_index.py")
    sys.exit(0)


if __name__ == "__main__":
    main()
