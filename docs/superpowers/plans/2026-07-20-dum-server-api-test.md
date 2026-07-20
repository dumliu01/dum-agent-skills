# dum-server-api-test 技能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `dum-server-api-test` 技能——给带服务端的项目生成并运行基于真实服务端 API 的 Go 功能测试（正常+异常流程，可按模块/优先级选跑）。

**Architecture:** 一个工作流技能，正文 `SKILL.md` 描述 4 阶段（摄入探测 → 用例设计 → 脚手架+生成 → 选择运行）；`assets/scaffold/` 提供一份可编译的最小 Go 测试骨架（裸 HTTP 版，goconvey 断言，命名约定 + `run.sh` 选择器）；`references/` 提供接口清单抽取、异常用例 checklist、命名↔选择正则三份参考。最后按多 agent 插件约定同步根索引/README/CHANGELOG/版本号/manifest。

**Tech Stack:** Markdown（SKILL/README/references）、Go + goconvey（scaffold 模板）、bash（build.sh/run.sh）、JSON（plugin manifest）。

## Global Constraints

- 技能名固定 `dum-server-api-test`；目录 `skills/dum-server-api-test/`。
- 断言风格一律 goconvey（`github.com/smartystreets/goconvey/convey` 的 `Convey`/`So`）。
- 测试工程落点约定 `testcase/<service>-api-test/`。
- 命名约定：文件 `<模块字母><NN>_<Interface>_test.go`；函数 `Test_<字母><NN>_<P0|P1|P2>_<Case>`；顶部注解 `@desc / @label / @interface / @dependent`。
- 选择机制：命名约定 + `run.sh` 包装（`--module` / `--priority` / `--interface` / `--list` / `--run`），把 module→字母前缀、priority→`_P0_` 片段拼 `-test.run` 正则。
- 调用方式：优先复用目标项目已有 Go client SDK；无则回退裸 HTTP。scaffold 以裸 HTTP 为默认可编译形态。
- 真实服务端护栏：只连测试/beta；敏感值占位 + `.gitignore` 真实 config；每条产生资源的用例末尾必须「清理数据」子 Convey；破坏性接口需确认纳入。
- 版本号 bump：`1.2.0 → 1.3.0`。
- SKILL.md 正文用 Claude Code 工具名（Read/Write/Edit/Bash/Grep/Glob），并说明跨 agent 等价工具（对齐根 CLAUDE.md 约定）。
- 参考项目（只读，勿改）：`/Users/dum/Vmware_Share/work_dev/aigc-agent/testcase/aigc-agent-manager`。
- Go 骨架验证用 `gofmt -e -l`（离线解析语法，不下载依赖）；有 go 环境时可另跑 `go vet`，但不作为硬门槛。

---

### Task 1: 骨架目录 + SKILL.md 正文

**Files:**
- Create: `skills/dum-server-api-test/SKILL.md`

**Interfaces:**
- Produces: 技能正文，后续 Task 引用其中约定；frontmatter `name: dum-server-api-test`。

- [ ] **Step 1: 写 SKILL.md**

内容须包含以下小节（用中文正文，对标 `skills/dum-e2e-test/SKILL.md` 的组织）：

1. YAML frontmatter：
   ```yaml
   ---
   name: dum-server-api-test
   description: Use when 用户要给带服务端的项目做接口/API 功能测试、写 go test 接口用例、连真实服务端验证接口行为、按模块或优先级选跑接口测试。能力：按权威阶梯(需求>技术方案>代码)读懂每个接口 → 设计正常+异常用例(P0/P1/P2) → 生成可编译 Go 测试(goconvey，连真实服务端不 mock，优先复用项目已有 client SDK 否则裸 HTTP) → 命名约定+run.sh 按 --module/--priority 选跑。落点 testcase/<service>-api-test/ 与 docs/test-cases/<service>-api.md。Triggers - "写接口测试"/"API 功能测试"/"go test 测接口"/"生成接口测试用例并跑"/"按模块/优先级跑接口测试"/"服务端接口测试"。区别 dum-e2e-test：那个带 UI 端到端，本技能无 UI 纯服务端 API。
   ---
   ```
2. `# dum-server-api-test（服务端 API 功能测试工作流）` + Overview（一段话 + 4 阶段流水线 ASCII 图 + 阶段/产物/落点表）。
3. `## When to Use` 表（写接口测试、API 功能测试、按模块/优先级选跑、连真实服务端验证接口）。
4. `## When NOT to Use` 表（带 UI 的端到端→dum-e2e-test；纯单元测试无网络→直接写 unit test；压测/性能→非本技能；mock/契约测试→非本技能；只跑一次的临时脚本→直接 curl）。
5. `## 核心原则`：① 权威阶梯 需求>技术方案>代码；② 连真实服务端不 mock；③ 每接口多条=正常+异常；④ 优先级分层 P0/P1/P2；⑤ 真实服务端护栏（清理数据/敏感值占位/破坏性接口需确认）。
6. `## 阶段① 摄入与探测`：如何读需求/方案/代码抽每接口（入参/出参/鉴权/错误码/依赖/副作用）；如何探测目标项目（`Grep` 找 client SDK / http_client / NewXxxClient；读 `go.mod` module path；鉴权方式/baseURL/错误码）；产出接口清单。指向 `references/interface-inventory.md`。
7. `## 阶段② 用例设计`：正常+异常怎么设计、优先级怎么分层、异常怎么按接口语义选。指向 `references/abnormal-catalog.md`。产出 `docs/test-cases/<service>-api.md`（用 `assets/test-cases.md.tmpl`）。
8. `## 阶段③ 脚手架 + 生成`：复制 `assets/scaffold/` → `testcase/<service>-api-test/`，改包名/module/接口；SDK 复用路径 vs 裸 HTTP 路径怎么选与怎么改（复用则在 `A00_Main_test.go` new 项目 client，裸 HTTP 则用 `tool.go` 的 `doRequest`）；测试文件命名与注解规则；goconvey 结构（外层接口 Convey + 内层正常/异常子 Convey + 末尾「清理数据」）。指向 `references/naming-and-selection.md`。
9. `## 阶段④ 选择运行`：`build.sh` 编译、`run.sh` 用法与选择正则映射、`--list`、失败透出并提示可转 `superpowers:systematic-debugging` / `dum-doc-reconcile` / `dum-session-summary`。
10. `## 真实服务端护栏` 小节（把 Global Constraints 里护栏展开）。
11. `## 跨 agent 工具名` 一句话 + 指回根 CLAUDE.md 对照表。
12. `## 产物落点` 汇总表（`testcase/<service>-api-test/`、`docs/test-cases/<service>-api.md`）。

- [ ] **Step 2: 验证结构完整**

Run: `grep -c -E '^(## |name: dum-server-api-test|When NOT to Use)' skills/dum-server-api-test/SKILL.md`
Expected: ≥ 8（frontmatter name + 各 `## ` 小节命中）。

Run: `grep -q 'dum-e2e-test' skills/dum-server-api-test/SKILL.md && grep -q 'goconvey' skills/dum-server-api-test/SKILL.md && grep -q 'run.sh' skills/dum-server-api-test/SKILL.md && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/dum-server-api-test/SKILL.md
git commit -m "feat(dum-server-api-test): 技能正文（4 阶段工作流 + 护栏）"
```

---

### Task 2: references 三份参考

**Files:**
- Create: `skills/dum-server-api-test/references/interface-inventory.md`
- Create: `skills/dum-server-api-test/references/abnormal-catalog.md`
- Create: `skills/dum-server-api-test/references/naming-and-selection.md`

**Interfaces:**
- Consumes: SKILL.md 各阶段的 `指向 references/...` 链接。
- Produces: 三份被 SKILL.md 引用的详解文档。

- [ ] **Step 1: 写 interface-inventory.md**

内容：如何从 需求 / 技术方案(`docs/tech-design`) / 代码 三源按权威阶梯抽每个接口的字段——method+path、鉴权、请求体字段（必填/可选/类型/约束）、响应体+错误码、前置依赖（需先建什么资源）、副作用（是否产生/删除资源、是否扣费/发送）。给一张「接口清单表」模板（接口 | 模块字母 | 优先级 | 依赖 | 副作用）。优先级分层规则：P0=核心正常流程+关键异常（鉴权失败/关键参数非法）；P1=常规异常；P2=边界/极端。模块字母分配规则：一个功能域一个字母（A/B/C…），与参考项目一致（示例 A=注册管理 B=实例 …）。

- [ ] **Step 2: 写 abnormal-catalog.md**

内容：异常流程用例 checklist（按接口语义勾选适用项），至少覆盖：
- 鉴权类：无 token/签名、错误签名、过期、越权（他人资源）。
- 参数类：必填缺失、类型错误、超长/超短、越界值、非法枚举、空数组/空串。
- 幂等/冲突类：重复创建、重复删除、并发达到限流。
- 依赖类：依赖资源不存在、依赖资源已删除、顺序颠倒。
- 状态机类：非法状态转移（如未启动就发消息）。
每类给「断言要点」（期望 `code != 0` / 特定错误码 / `err != nil`）。说明每接口至少 1 正常 + 按语义选 ≥1 异常。

- [ ] **Step 3: 写 naming-and-selection.md**

内容：命名约定与 `run.sh` 选择正则的完整映射规则。
- 文件名 `<字母><NN>_<Interface>_test.go`；函数 `Test_<字母><NN>_<P0|P1|P2>_<Case>`。
- 注解 `@desc/@label/@interface/@dependent` 语义。
- `run.sh` 参数 → `-test.run` 正则的构造规则，给 3 个 worked example：
  - `--module A,B` → `^Test_(A|B)[0-9]+_`
  - `--priority p0` → `^Test_[A-Z][0-9]+_P0_`
  - `--module B --priority p0,p1` → `^Test_(B)[0-9]+_(P0|P1)_`
  - `--interface RegisterAgent` → grep 注解 `@interface:.*RegisterAgent` 取函数名并 OR 拼接。
- `--list` 行为：grep 注解列出全部 模块字母/优先级/接口。

- [ ] **Step 4: 验证**

Run: `for f in interface-inventory abnormal-catalog naming-and-selection; do test -s skills/dum-server-api-test/references/$f.md && echo "$f ok"; done`
Expected: 三行 `... ok`。

Run: `grep -q 'Test_(A|B)' skills/dum-server-api-test/references/naming-and-selection.md && echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add skills/dum-server-api-test/references/
git commit -m "feat(dum-server-api-test): references（接口清单/异常清单/命名与选择）"
```

---

### Task 3: assets/scaffold —— 可编译 Go 骨架（非测试文件）

**Files:**
- Create: `skills/dum-server-api-test/assets/scaffold/go.mod`
- Create: `skills/dum-server-api-test/assets/scaffold/config.go`
- Create: `skills/dum-server-api-test/assets/scaffold/tool.go`
- Create: `skills/dum-server-api-test/assets/scaffold/test.yml.example`
- Create: `skills/dum-server-api-test/assets/scaffold/.gitignore`

**Interfaces:**
- Produces:
  - `config.go`: `type Config struct{ App AppConfig; Modules map[string]... }` + `func (c *Config) Init(path string) error` + `func GetConfig() *Config`。包名 `apitest`。
  - `tool.go`: `func GenerateRandomString(n int) string`；`func DoRequest(method, path string, body any, headers map[string]string) (status int, respBody []byte, err error)`（用 `net/http`，baseURL 取自 `GetConfig().App.BaseURL`，超时取自 config）；`func SignRequest(...)` 占位注释说明按项目鉴权替换。
  - `test.yml.example`: `app:{ baseURL, appId, secret, requestTimeout }` + 一个示例模块参数块，敏感值写占位 `"<your-secret>"`。
- Consumes: 无（scaffold 自包含，裸 HTTP，不依赖外部 SDK；仅 `config.go`/`tool.go` 用标准库）。

- [ ] **Step 1: 写 go.mod**

```
module apitest

go 1.21

require github.com/smartystreets/goconvey v1.8.1
```
（require 仅供 `go build` 参考；`gofmt` 验证不需要它。）

- [ ] **Step 2: 写 config.go（标准库 yaml 手写解析或 gopkg.in/yaml.v3）**

用 `gopkg.in/yaml.v3`。给出完整可解析 Go：
```go
package apitest

import (
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	App     AppConfig                 `yaml:"app"`
	Modules map[string]map[string]any `yaml:"modules"`
}

type AppConfig struct {
	BaseURL        string `yaml:"baseURL"`
	AppID          int64  `yaml:"appId"`
	Secret         string `yaml:"secret"`
	RequestTimeout int    `yaml:"requestTimeout"` // 秒
}

var c Config

func (c *Config) Init(path string) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return yaml.Unmarshal(b, c)
}

func GetConfig() *Config { return &c }
```
在 go.mod 的 require 里补 `gopkg.in/yaml.v3 v3.0.1`。

- [ ] **Step 3: 写 tool.go**

完整可解析 Go：`GenerateRandomString`、`DoRequest`（`net/http` + `time` 超时 + `bytes`/`encoding/json` + `io`）、`SignRequest` 占位。示例：
```go
package apitest

import (
	"bytes"
	"encoding/json"
	"io"
	"math/rand"
	"net/http"
	"time"
)

func GenerateRandomString(n int) string {
	const charset = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, n)
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	for i := range b {
		b[i] = charset[r.Intn(len(charset))]
	}
	return string(b)
}

// DoRequest 发起真实服务端请求。鉴权按项目实际方式在 SignRequest 里补全。
func DoRequest(method, path string, body any, headers map[string]string) (int, []byte, error) {
	cfg := GetConfig()
	var reader io.Reader
	if body != nil {
		buf, err := json.Marshal(body)
		if err != nil {
			return 0, nil, err
		}
		reader = bytes.NewReader(buf)
	}
	req, err := http.NewRequest(method, cfg.App.BaseURL+path, reader)
	if err != nil {
		return 0, nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	for k, v := range headers {
		req.Header.Set(k, v)
	}
	SignRequest(req)
	client := &http.Client{Timeout: time.Duration(cfg.App.RequestTimeout) * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return 0, nil, err
	}
	defer resp.Body.Close()
	respBody, err := io.ReadAll(resp.Body)
	return resp.StatusCode, respBody, err
}

// SignRequest 占位：按项目鉴权（签名/token/header）实现。
func SignRequest(req *http.Request) {
	// TODO(接入项目时替换)：例如 req.Header.Set("Authorization", ...)
}
```
（注：`SignRequest` 里的 `TODO` 是**给使用者的接入提示**，属 scaffold 模板语义，非本 plan 的占位违规。）

- [ ] **Step 4: 写 test.yml.example**

```yaml
# 复制为 test.yml 并填真实值；test.yml 已在 .gitignore，勿提交真实密钥。
# 仅连测试/beta 环境。
app:
  baseURL: "https://<your-test-host>"
  appId: 0
  secret: "<your-secret>"
  requestTimeout: 10

modules:
  example:
    sampleText: "hello"
```

- [ ] **Step 5: 写 .gitignore**

```
test.yml
*.test
*.log
```

- [ ] **Step 6: 验证 Go 语法（离线）**

Run: `gofmt -e -l skills/dum-server-api-test/assets/scaffold/config.go skills/dum-server-api-test/assets/scaffold/tool.go`
Expected: 空输出（无语法错误、已格式化）。若列出文件名则说明未格式化，跑 `gofmt -w` 修正后重验。

- [ ] **Step 7: Commit**

```bash
git add skills/dum-server-api-test/assets/scaffold/
git commit -m "feat(dum-server-api-test): scaffold 基座（config/tool/config示例/gitignore）"
```

---

### Task 4: assets/scaffold —— TestMain + worked-example 测试文件

**Files:**
- Create: `skills/dum-server-api-test/assets/scaffold/A00_Main_test.go`
- Create: `skills/dum-server-api-test/assets/scaffold/A01_Example_test.go`

**Interfaces:**
- Consumes: `config.go` 的 `Config.Init` / `GetConfig`；`tool.go` 的 `DoRequest` / `GenerateRandomString`。
- Produces: 一个可照抄的接口测试范例（含正常 + 异常 + 清理），供 SKILL 阶段③ 引用。

- [ ] **Step 1: 写 A00_Main_test.go（TestMain）**

完整可解析 Go：
```go
package apitest

import (
	"flag"
	"fmt"
	"os"
	"testing"
)

func TestMain(m *testing.M) {
	path := flag.String("c", "./test.yml", "-c 配置文件路径（默认 ./test.yml）")
	flag.Parse()
	if err := c.Init(*path); err != nil {
		fmt.Println("load config failed:", err)
		os.Exit(1)
	}
	fmt.Printf("load config success: %s\n", *path)
	// 复用项目 client SDK 时：在此 new 项目 client 并存入包级变量。
	os.Exit(m.Run())
}
```

- [ ] **Step 2: 写 A01_Example_test.go（worked example，goconvey 正常+异常+清理）**

完整可解析 Go，展示命名 `Test_A01_P0_...`、注解、外层接口 Convey + 内层子 Convey：
```go
package apitest

import (
	"encoding/json"
	"fmt"
	"testing"

	. "github.com/smartystreets/goconvey/convey"
)

// @desc: 示例接口 CreateExample 的功能测试（正常 + 异常）
// @label: p0
// @interface: CreateExample
// @dependent:
func Test_A01_P0_CreateExample(t *testing.T) {
	name := fmt.Sprintf("example_%s", GenerateRandomString(6))
	var createdID string

	Convey("CreateExample 接口", t, func() {
		Convey("正常流程：合法参数创建成功", func() {
			status, body, err := DoRequest("POST", "/example/create",
				map[string]any{"name": name}, nil)
			So(err, ShouldBeNil)
			So(status, ShouldEqual, 200)
			var resp struct {
				Code int    `json:"code"`
				ID   string `json:"id"`
			}
			So(json.Unmarshal(body, &resp), ShouldBeNil)
			So(resp.Code, ShouldEqual, 0)
			createdID = resp.ID
		})

		Convey("异常流程：缺少必填参数 name", func() {
			status, body, err := DoRequest("POST", "/example/create",
				map[string]any{}, nil)
			So(err, ShouldBeNil)
			_ = status
			var resp struct {
				Code int `json:"code"`
			}
			So(json.Unmarshal(body, &resp), ShouldBeNil)
			So(resp.Code, ShouldNotEqual, 0)
		})

		Convey("清理数据", func() {
			if createdID != "" {
				_, _, err := DoRequest("POST", "/example/delete",
					map[string]any{"id": createdID}, nil)
				So(err, ShouldBeNil)
			}
		})
	})
}
```

- [ ] **Step 3: 验证 Go 语法（离线）**

Run: `gofmt -e -l skills/dum-server-api-test/assets/scaffold/A00_Main_test.go skills/dum-server-api-test/assets/scaffold/A01_Example_test.go`
Expected: 空输出。

Run: `grep -q 'Test_A01_P0_CreateExample' skills/dum-server-api-test/assets/scaffold/A01_Example_test.go && grep -q '清理数据' skills/dum-server-api-test/assets/scaffold/A01_Example_test.go && grep -q '@interface: CreateExample' skills/dum-server-api-test/assets/scaffold/A01_Example_test.go && echo OK`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add skills/dum-server-api-test/assets/scaffold/A00_Main_test.go skills/dum-server-api-test/assets/scaffold/A01_Example_test.go
git commit -m "feat(dum-server-api-test): scaffold TestMain + worked-example 测试"
```

---

### Task 5: assets/scaffold —— build.sh + run.sh 选择器

**Files:**
- Create: `skills/dum-server-api-test/assets/scaffold/build.sh`
- Create: `skills/dum-server-api-test/assets/scaffold/run.sh`

**Interfaces:**
- Consumes: scaffold Go 文件的命名约定（`Test_<字母><NN>_<P0|P1|P2>_`）。
- Produces: `run.sh <config> [--module A,B] [--priority p0,p1] [--interface X] [--list] [--run <regex>]`，内部把参数拼成 `-test.run` 正则调 `go test`。

- [ ] **Step 1: 写 build.sh**

```bash
#!/bin/bash
set -e
export GO111MODULE=on
go test -c -o apitest.test
echo "built: apitest.test"
```

- [ ] **Step 2: 写 run.sh（含选择正则构造）**

```bash
#!/bin/bash
# 用法: run.sh <config.yml> [--module A,B] [--priority p0,p1] [--interface Name] [--list] [--run <regex>]
set -e

CONFIG=""
MODULES=""
PRIORITIES=""
IFACE=""
RAW_RUN=""
LIST=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --module)    MODULES="$2"; shift 2;;
    --priority)  PRIORITIES="$2"; shift 2;;
    --interface) IFACE="$2"; shift 2;;
    --run)       RAW_RUN="$2"; shift 2;;
    --list)      LIST=1; shift;;
    *)           if [[ -z "$CONFIG" ]]; then CONFIG="$1"; shift; else echo "unknown arg: $1"; exit 1; fi;;
  esac
done

if [[ "$LIST" == "1" ]]; then
  echo "== 模块字母 =="; grep -rhoE '^func Test_[A-Z][0-9]+_' *_test.go | sed -E 's/^func Test_([A-Z])[0-9].*/\1/' | sort -u
  echo "== 优先级 =="; grep -rhoE '_P[0-9]_' *_test.go | tr -d '_' | sort -u
  echo "== 接口 =="; grep -rhoE '@interface:.*' *_test.go | sed 's/@interface://' | tr ',' '\n' | sed 's/^ *//;/^$/d' | sort -u
  exit 0
fi

if [[ -z "$CONFIG" ]]; then echo "错误：未指定配置文件路径"; exit 1; fi

# 构造 -test.run 正则
build_regex() {
  local mod_part=".*" pri_part=".*"
  if [[ -n "$MODULES" ]]; then mod_part="($(echo "$MODULES" | tr ',' '|'))"; fi
  if [[ -n "$PRIORITIES" ]]; then pri_part="($(echo "$PRIORITIES" | tr ',' '|' | tr 'a-z' 'A-Z'))"; fi
  echo "^Test_${mod_part}[0-9]+_${pri_part}_"
}

if [[ -n "$RAW_RUN" ]]; then
  RUN="$RAW_RUN"
elif [[ -n "$IFACE" ]]; then
  # 按 @interface 注解取对应函数名并 OR 拼接
  FUNCS=$(grep -B4 -E "@interface:.*${IFACE}" *_test.go | grep -oE 'Test_[A-Za-z0-9_]+' | sort -u | paste -sd '|' -)
  if [[ -z "$FUNCS" ]]; then echo "没有匹配 @interface=${IFACE} 的测试"; exit 1; fi
  RUN="^($FUNCS)$"
else
  RUN="$(build_regex)"
fi

echo "-test.run: $RUN"
go test -v -run "$RUN" -args -c "$CONFIG"
```

- [ ] **Step 3: 验证选择正则逻辑（离线 dry-run）**

在临时目录造两个假测试文件，只验证正则构造，不真跑 go test：
```bash
tmp=$(mktemp -d)
cp skills/dum-server-api-test/assets/scaffold/run.sh "$tmp/run.sh"
cat > "$tmp/x_test.go" <<'EOF'
func Test_A01_P0_CreateExample(t *testing.T){}
// @interface: CreateExample
func Test_B02_P1_UpdateExample(t *testing.T){}
// @interface: UpdateExample
EOF
cd "$tmp"
# 用 --run 走一条不触发 go test 的检查：改为只回显正则（把最后一行 go test 前置 echo 已在脚本里）
bash run.sh cfg.yml --module A,B --priority p0 2>/dev/null | grep '^-test.run:'
```
Expected: 打印 `-test.run: ^Test_(A|B)[0-9]+_(P0)_`

Run（--list 验证）: `cd "$tmp" && bash run.sh --list | grep -E '^(A|B)$'`
Expected: 两行 `A` 和 `B`。

（注：脚本末尾会真的调 `go test`；dry-run 只截取 `-test.run:` 回显行，`go test` 在无依赖临时目录会失败但不影响本步只校验回显。若要避免噪声，可临时在 `$tmp/run.sh` 末行 `go test` 前加 `exit 0` 后再验，验证完丢弃临时目录。）

- [ ] **Step 4: 赋可执行位 + Commit**

```bash
chmod +x skills/dum-server-api-test/assets/scaffold/build.sh skills/dum-server-api-test/assets/scaffold/run.sh
git add skills/dum-server-api-test/assets/scaffold/build.sh skills/dum-server-api-test/assets/scaffold/run.sh
git commit -m "feat(dum-server-api-test): build.sh + run.sh（模块/优先级/接口选择器）"
```

---

### Task 6: assets/test-cases.md.tmpl 汇总表模板

**Files:**
- Create: `skills/dum-server-api-test/assets/test-cases.md.tmpl`

**Interfaces:**
- Consumes: SKILL 阶段② 引用。
- Produces: 生成 `docs/test-cases/<service>-api.md` 的模板。

- [ ] **Step 1: 写模板**

```markdown
# <service> API 测试用例汇总

> 生成自 dum-server-api-test；权威阶梯 需求 > 技术方案 > 代码。

## 模块字母映射

| 字母 | 功能模块 |
|---|---|
| A | <模块名> |

## 用例清单

| 接口 | 用例名(函数) | 模块 | 优先级 | 类型 | 期望 | 依赖 | 副作用/清理 |
|---|---|---|---|---|---|---|---|
| CreateExample | Test_A01_P0_CreateExample | A | P0 | 正常 | code==0 返回 id | 无 | 建资源→末尾删除 |
| CreateExample | Test_A01_P0_CreateExample/缺少name | A | P0 | 异常 | code!=0 | 无 | 无 |

## 破坏性接口（需确认纳入）

| 接口 | 风险 | 是否纳入 |
|---|---|---|
| DeleteExample | 删除资源不可逆 | 待确认 |
```

- [ ] **Step 2: 验证**

Run: `grep -q 'Test_A01_P0_CreateExample' skills/dum-server-api-test/assets/test-cases.md.tmpl && grep -q '破坏性接口' skills/dum-server-api-test/assets/test-cases.md.tmpl && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/dum-server-api-test/assets/test-cases.md.tmpl
git commit -m "feat(dum-server-api-test): 用例汇总表模板"
```

---

### Task 7: 技能 README.md

**Files:**
- Create: `skills/dum-server-api-test/README.md`

**Interfaces:**
- Consumes: 无。
- Produces: 技能自述（对标 `skills/dum-solution-design/README.md` 的体例）。

- [ ] **Step 1: 写 README.md**

包含：一句话简介、何时触发（触发词列表）、与 dum-e2e-test 的分工、产物落点、跨 agent 工具名一句话、快速上手（复制 scaffold → 填 test.yml → build.sh → run.sh 选跑）。

- [ ] **Step 2: 验证**

Run: `test -s skills/dum-server-api-test/README.md && grep -q 'run.sh' skills/dum-server-api-test/README.md && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add skills/dum-server-api-test/README.md
git commit -m "docs(dum-server-api-test): 技能 README"
```

---

### Task 8: 多 agent 注册 + 根索引/CHANGELOG/版本号同步

**Files:**
- Modify: `CLAUDE.md`（技能清单表 + 衔接段）
- Modify: `README.md`（根，技能列表）
- Modify: `CHANGELOG.md`（新版本条目）
- Modify: `.claude-plugin/plugin.json`（version）
- Modify: `.claude-plugin/marketplace.json`（version）
- Modify: `package.json`（version，若有）
- 核对并按需 Modify: `.codex-plugin/plugin.json`、`.cursor-plugin/plugin.json`、`gemini-extension.json`

**Interfaces:**
- Consumes: 已建好的 `skills/dum-server-api-test/`。
- Produces: 技能在各 agent 生态可被发现。

- [ ] **Step 1: 先核对各 manifest 是否需逐技能登记**

Run: `grep -rl 'dum-e2e-test' .claude-plugin .codex-plugin .cursor-plugin gemini-extension.json package.json 2>/dev/null`
Expected: 列出所有「显式列举技能」的文件——这些都要加 `dum-server-api-test`；未列出的文件（靠扫 `skills/` 目录自动收）无需改。据此结果确定 Step 2 改哪些文件。

- [ ] **Step 2: 根 CLAUDE.md**

在「## 技能清单」表末加一行：
```
| **dum-server-api-test** | 给带服务端的项目生成并运行基于真实服务端 API 的 Go 功能测试（正常+异常，goconvey，优先复用项目 client SDK 否则裸 HTTP），命名约定+run.sh 按模块/优先级选跑。触发："写接口测试"/"API 功能测试"/"go test 测接口"/"按模块/优先级跑接口测试" | `skills/dum-server-api-test/SKILL.md` |
```
在衔接段补一句：`dum-server-api-test` 补 `dum-e2e-test` 排除的「无 UI 纯服务端 API」；消费 `dum-solution-design` 方案与需求/代码派生接口用例，失败转 `systematic-debugging`/`dum-doc-reconcile`，改完用 `dum-session-summary` 记账。

- [ ] **Step 3: 根 README.md 技能列表加一行**（对齐现有体例）。

- [ ] **Step 4: CHANGELOG.md 加条目**

```
## 1.3.0
### 新增
- **dum-server-api-test**：服务端 API 功能测试技能。连真实服务端（不 mock），go test + goconvey，读需求/方案/代码派生每接口正常+异常用例，命名约定 + run.sh 按模块/优先级选跑；补 dum-e2e-test 排除的无 UI 纯接口测试场景。
```

- [ ] **Step 5: 版本号 bump 到 1.3.0**

改 `.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`package.json`（若存在 version 字段）里 `1.2.0` → `1.3.0`，以及 Step 1 查出的其它显式登记文件。

- [ ] **Step 6: 验证 JSON 合法 + 技能已登记**

Run: `for f in $(grep -rl '"version"' .claude-plugin .codex-plugin .cursor-plugin package.json gemini-extension.json 2>/dev/null); do python3 -c "import json,sys; json.load(open('$f'))" && echo "$f json-ok"; done`
Expected: 每个文件 `... json-ok`（JSON 合法）。

Run: `grep -rq '1.3.0' .claude-plugin/plugin.json && grep -q 'dum-server-api-test' CLAUDE.md && grep -q 'dum-server-api-test' README.md && grep -q '1.3.0' CHANGELOG.md && echo OK`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore(release): 1.2.0 → 1.3.0（新技能 dum-server-api-test）+ 根索引/CHANGELOG 同步"
```

---

### Task 9: 端到端自检（渲染 scaffold 并编译，如有 go 环境）

**Files:**
- 无（临时验证，不落库）

**Interfaces:**
- Consumes: 全部 scaffold。
- Produces: 一次真实编译验证（best-effort）。

- [ ] **Step 1: 检查 go 是否可用**

Run: `command -v go && go version || echo "no-go"`
Expected: 有 go 版本号，或 `no-go`（则跳过本 Task 剩余步骤，仅以前面 gofmt 验证为准）。

- [ ] **Step 2: 复制 scaffold 到临时目录并 go vet（有 go 时）**

```bash
tmp=$(mktemp -d); cp -r skills/dum-server-api-test/assets/scaffold/* "$tmp"/; cd "$tmp"
cp test.yml.example test.yml
go mod tidy && go vet ./... && echo "VET-OK"
```
Expected: `VET-OK`（依赖可下载时）。若因离线/网络失败，记录为「已知环境限制」，不阻塞——scaffold 语法已由 gofmt 保证。

- [ ] **Step 3: 记录自检结论**

在 `docs/superpowers/plans/2026-07-20-dum-server-api-test.md` 末尾追加一行「自检结果：VET-OK / no-go / offline-skip」并 commit（可选）。

---

## Self-Review

**1. Spec coverage：**
- spec §1 定位/边界 → Task 1（SKILL When to/NOT to Use、跨 agent）、Task 8（根 CLAUDE 衔接段）。✓
- spec §2 六项决策 → Global Constraints 逐条落 + 各 Task 体现（goconvey=Task4/5、命名+run.sh=Task5、SDK 探测=Task1/3、落点=Task1/8、汇总表=Task6）。✓
- spec §3 四阶段 → Task 1 SKILL 正文四小节 + references（Task2）+ scaffold（Task3/4/5）+ 汇总表（Task6）。✓
- spec §4 护栏 → Global Constraints + Task1 护栏小节 + Task4 清理数据 example + Task3 .gitignore/占位。✓
- spec §5 技能包结构 → Task1(SKILL)/Task2(references)/Task3-5(assets/scaffold)/Task6(tmpl)/Task7(README) 全覆盖。✓
- spec §6 收尾同步 → Task 8。✓
- spec §7 非目标 → SKILL When NOT to Use（Task1 Step1 第4点）体现。✓

**2. Placeholder scan：** 计划内无 TBD/TODO 作为「待补」；唯一 `TODO` 出现在 scaffold `SignRequest` 里，是给使用者的接入提示（模板语义），已在 Task3 Step3 注明。✓

**3. Type consistency：** `DoRequest(method, path string, body any, headers map[string]string) (int, []byte, error)` 在 Task3 定义、Task4 example 一致调用；`GenerateRandomString(n int) string`、`GetConfig()/Config.Init` 一致；包名统一 `apitest`；函数命名 `Test_A01_P0_CreateExample` 在 Task4/5/6 一致引用。✓

## Execution Handoff

见对话中的执行方式选择。
