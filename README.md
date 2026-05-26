# Dum Agent Skills

一组可复用的 AI agent 工作流技能（skills），偏工程文档场景。以**多 agent 插件**形式发布：
技能正文集中在 [`skills/`](skills/)，Claude Code / Codex / Gemini CLI / Cursor 各有一份 manifest 指向它。

## 技能一览

| 技能 | 一句话 |
|---|---|
| [`dum-knowledge-base-build`](skills/dum-knowledge-base-build/) | 给项目搭建/维护标准化知识库文档体系（`docs/` 分类目录 + `CLAUDE.md` 入口 + 架构文档 + 自动文档索引），并接 hook 自动更新 |
| [`dum-arch-spec-doc`](skills/dum-arch-spec-doc/) | 给单个服务按语言（前端/Go/Python）生成**分离的两份**文档：程序架构文档（`docs/architecture/`）+ 开发规范文档（`docs/specification/`） |
| [`dum-solution-design`](skills/dum-solution-design/) | 出结构化技术方案：架构/时序/关键逻辑/接口/遗留 五段，文档与代码分离 |
| [`dum-doc-reconcile`](skills/dum-doc-reconcile/) | 按修改记录（兼查 git）把设计文档跟代码现状对账修正 |
| [`dum-session-summary`](skills/dum-session-summary/) | 把会话改动总结进 `docs/modify_history/`，生成交接文档 |
| [`dum-ppt`](skills/dum-ppt/) | 把 Markdown 转成单 HTML、可全屏播放的演示文档 |

> 变更历史见 [`CHANGELOG.md`](CHANGELOG.md)。

## 安装

不同 agent 安装方式不同；多个一起用就各装一次。

### Claude Code

通过插件市场安装：

```bash
# 注册市场（指向本仓库）
/plugin marketplace add dumliu01/dum-agent-skills
# 安装插件
/plugin install dum-agent-skills@dum-skills
```

或本地开发时直接加本地路径：

```bash
/plugin marketplace add /Users/dum/Vmware_Share/dum_dev/dum-agent-skills
/plugin install dum-agent-skills@dum-skills
```

装好后输入 `/help` 或直接描述任务（如"出个技术方案"），相应技能会自动触发。

> 旧装法（手动 `cp` 到 `~/.claude/skills/`）已不再需要——插件会统一提供这些技能，
> 留着拷贝会和插件重复。删掉即可：`rm -rf ~/.claude/skills/dum-*`。

### Codex CLI

把本仓库作为插件加入 Codex（读取 `.codex-plugin/plugin.json` 与 `AGENTS.md`）：

```bash
git clone https://github.com/dumliu01/dum-agent-skills.git
# 按 Codex 的插件安装方式引入该目录（plugin.json 的 "skills" 指向 ./skills/）
```

### Gemini CLI

作为 Gemini 扩展安装（读取 `gemini-extension.json`，上下文文件 `GEMINI.md`）：

```bash
gemini extensions install https://github.com/dumliu01/dum-agent-skills
```

### Cursor

把本仓库作为 Cursor 插件引入（读取 `.cursor-plugin/plugin.json`，`skills` 指向 `./skills/`）。

## 仓库结构

```
.
├── skills/                     # ← 所有技能（唯一真源，各 agent 共享）
│   ├── dum-knowledge-base-build/
│   ├── dum-arch-spec-doc/
│   ├── dum-solution-design/
│   ├── dum-doc-reconcile/
│   ├── dum-session-summary/
│   └── dum-ppt/
├── .claude-plugin/             # Claude Code：plugin.json + marketplace.json
├── .codex-plugin/plugin.json   # Codex
├── .cursor-plugin/plugin.json  # Cursor
├── gemini-extension.json       # Gemini CLI
├── CLAUDE.md  ←  AGENTS.md      # 入口/索引（AGENTS.md 是 CLAUDE.md 的软链）
├── GEMINI.md                   # Gemini 上下文索引
└── package.json
```

新增技能：在 `skills/` 下建一个目录放 `SKILL.md` 即可，所有 agent 自动共享，无需改 manifest。

## License

MIT
