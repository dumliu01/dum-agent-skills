# 描述提取器 — 按语言对照

> 本页讲的是**源码清单脚本** `update_architecture_manifest.py` 的提取器（从代码文件取描述）。
> **文档索引脚本** `update_docs_index.py` 用的是另一个内置提取器 `extract_doc_title`（从 `.md` 取描述：
> frontmatter `title`/`description` → 首个 `#` 标题 → 首行非空正文）+ 解析 `YYYYMMDD-标题.md` 文件名取日期，
> 不在本页范围，一般不用改。

骨架脚本 `scripts/update_architecture_manifest.py` 内置 3 个：

| 提取器 | 适用 | 行为 |
|---|---|---|
| `extract_python_docstring` | `.py` | `ast.get_docstring()` 取模块级 docstring 首行 |
| `extract_first_comment` | `.ts` `.tsx` `.js` `.jsx` `.vue` `.go` `.rs` `.c` `.cpp` `.h` `.java` `.swift` `.kt` `.scala` 等 | 文件首 30 行内首条 `//` / `/* */` / `/** */` 注释；`.vue` 先定位到第一个 `<script>` 块；自动过滤 path-banner |
| `extract_yaml_top_comment` | `.yaml` `.yml` | 文件首 5 行内首个 `# xxx` |

## 选哪个

设 `EXTRACTOR = "..."`：

```python
# Python 后端
EXTRACTOR = "extract_python_docstring"
INCLUDE_EXTENSIONS = {".py", ".yaml", ".yml"}   # YAML 自动用 yaml 提取器

# TS / Vue / React 前端
EXTRACTOR = "extract_first_comment"
INCLUDE_EXTENSIONS = {".ts", ".tsx", ".vue"}

# Go 微服务
EXTRACTOR = "extract_first_comment"
INCLUDE_EXTENSIONS = {".go", ".yaml", ".yml"}

# Rust crate
EXTRACTOR = "extract_first_comment"
INCLUDE_EXTENSIONS = {".rs", ".toml"}   # toml 走 yaml 提取器（# 注释语法相同）

# Java / Kotlin
EXTRACTOR = "extract_first_comment"
INCLUDE_EXTENSIONS = {".java", ".kt"}
```

## 写新提取器

如果上面三个都不够（如要支持 Java javadoc 多行、Rust `///` 三斜杠、Lua `--`、Haskell `{- -}`）：

1. 在 `scripts/update_architecture_manifest.py` 的"内置提取器"段加一个函数，签名 `(filepath: Path) -> str`
2. 注册到 `_EXTRACTORS` 字典
3. 把 `EXTRACTOR` 改成新名字

模板：

```python
def extract_my_lang(filepath: Path) -> str:
    if filepath.suffix != ".XX":
        return ""
    try:
        for line in filepath.read_text(encoding="utf-8", errors="replace").splitlines()[:30]:
            stripped = line.strip()
            # 你的语言里"模块级首行注释"的判定规则
            if stripped.startswith("--- "):   # 比如 Lua 三横线
                return stripped[4:].strip()
            if stripped and not stripped.startswith("--"):
                break    # 遇到第一行非注释非空 → 停
    except (OSError, UnicodeDecodeError):
        pass
    return ""

_EXTRACTORS["extract_my_lang"] = extract_my_lang
```

## 多语言混合服务

如果一个服务里既有 Python 又有 Go（罕见但可能）：

- 选项 A：拆成两个脚本，每个用对应提取器，两个都写到同一份架构文档（用同一对 marker，第一个跑的覆盖第二个 — 不推荐）
- 选项 B：选其中一个为主语言；副语言文件的描述留空（树形里仍出现，但没 `# xxx` 注释）
- 选项 C：写一个 dispatch 提取器：

```python
def extract_dispatch(filepath: Path) -> str:
    if filepath.suffix == ".py":
        return extract_python_docstring(filepath)
    if filepath.suffix in (".go", ".ts"):
        return extract_first_comment(filepath)
    return ""
```

推荐 C。

## 已知坑

- **`.vue` 不能直接 `extract_first_comment` 全文档扫**，否则会拿到 `<template>` 里的 HTML 注释或 `<style>` 里的 CSS 注释。骨架已经做了 `<script>` 块定位，沿用即可
- **C/C++ header guards** 会被误判为非注释非空行 → 停 break。把 `_LINE_COMMENT_RE` 之外的判定加上 `("#ifndef", "#define")` 跳过
- **JS/TS 文件顶部的 `'use strict'`** 同上 → 加上 `('use strict', '"use strict"')` 跳过
- **Rust 模块级文档用 `//!`** 而非 `//`，需要单独写一个提取器（默认 `extract_first_comment` 把 `//!` 也当 `//` 抓，但内容会保留 `!` 前缀）— 加正则 `r"^\s*//!\s*(.+)$"` 优先匹配
