# 命名约定与 run.sh 选择正则映射

> 用途：指导 `dum-server-api-test` 技能阶段③「脚手架 + 生成」的文件/函数命名，以及阶段④「选择运行」里 `run.sh` 参数到 `-test.run` 正则的构造规则。
> 本文件是**方法论 reference**，不含可运行实现代码（`run.sh` 的实际实现在 `assets/scaffold/`）。

---

## 1. 命名约定

### 文件名

```
<字母><NN>_<Interface>_test.go
```

- `<字母>`：模块字母（见 `interface-inventory.md` §5），大写单字母，如 `A`、`B`。
- `<NN>`：模块内两位数序号，如 `01`、`02`，从 `01` 起按接口在模块内的顺序递增。
- `<Interface>`：接口的语义名（驼峰），如 `RegisterAgent`。

示例：`A01_RegisterAgent_test.go`、`B02_CreateInstance_test.go`。

### 函数名

```
Test_<字母><NN>_<P0|P1|P2>_<Case>
```

- `<字母><NN>`：与文件名前缀一致，标识该函数测的是哪个模块第几个接口。
- `<P0|P1|P2>`：该测试函数的优先级（见 `interface-inventory.md` §4）。
- `<Case>`：场景简述（驼峰），如 `Normal`、`NoToken`、`InvalidParam`。

示例：`Test_A01_P0_Normal`、`Test_A01_P0_NoToken`、`Test_A01_P1_InvalidParam`。

> 一个文件（一个接口）内可以有多个测试函数，分别覆盖正常与不同优先级的异常场景；也可以用单个函数 + 内部 goconvey 子 `Convey` 覆盖多个场景，此时函数名以该文件里**最高优先级**场景命名，各子 `Convey` 标题标注具体场景。

### 注解

每个测试函数（或其所在文件顶部）需要写以下注解，供人读也供 `run.sh --list` 与 `--interface` 解析：

| 注解 | 语义 |
|---|---|
| `@desc` | 该测试的一句话描述（做什么、验证什么） |
| `@label` | 场景标签，如 `normal`/`abnormal`，也可加更细的分类标签 |
| `@interface` | 对应的接口语义名（与 `interface-inventory.md` 清单表中的接口名对应），用于 `--interface` 匹配 |
| `@dependent` | 该用例依赖的前置资源/接口，说明运行顺序或前置条件 |

示例：

```go
// @desc 正常注册一个 agent，校验返回的 agent_id 非空且状态为 active
// @label normal
// @interface RegisterAgent
// @dependent 无
func Test_A01_P0_Normal(t *testing.T) {
    ...
}
```

---

## 2. run.sh 参数 → -test.run 正则构造规则

`run.sh` 把 `--module` / `--priority` / `--interface` 的组合翻译成 Go test 的 `-test.run` 正则，正则始终锚定在 `Test_` 前缀并以 `^` 开头，保证只匹配符合命名约定的函数。

### 构造规则

1. `--module A,B,C` → 取模块字母集合，拼成 `(A|B|C)`，插在 `Test_` 之后：`^Test_(A|B|C)[0-9]+_`。
2. `--priority p0,p1` → 优先级统一大写，拼成 `(P0|P1)`：`^Test_[A-Z][0-9]+_(P0|P1)_`。
3. 同时传 `--module` 与 `--priority` → 两段都替换为具体集合：`^Test_(<模块集合>)[0-9]+_(<优先级集合>)_`。
4. `--interface <name>` → 不走字母/优先级正则，而是先 `grep` 源码里的 `@interface:.*<name>` 注解，取命中的函数名列表，再 OR 拼接成正则（如 `^(Test_A01_P0_Normal|Test_A01_P1_NoToken)$`）。

### Worked Examples

| 命令 | 生成的 `-test.run` 正则 |
|---|---|
| `--module A,B` | `^Test_(A|B)[0-9]+_` |
| `--priority p0` | `^Test_[A-Z][0-9]+_P0_` |
| `--module B --priority p0,p1` | `^Test_(B)[0-9]+_(P0|P1)_` |
| `--interface RegisterAgent` | 先 `grep '@interface:.*RegisterAgent'` 取函数名，再 OR 拼接，如 `^(Test_A01_P0_Normal|Test_A01_P0_NoToken)$` |

---

## 3. --list 行为

`--list` 不实际运行测试，而是 `grep` 所有测试文件的注解，汇总列出：

- 全部模块字母及各自包含的接口（来自文件名前缀 + `@interface` 注解）。
- 全部出现过的优先级（P0/P1/P2）及各自用例数。
- 全部 `@interface` 值（去重），供 `--interface` 参数取值参考。

输出用于用户在真正 `--run` 之前核对将要选中的范围是否符合预期。

---

*本文件供 `SKILL.md` 「阶段③ 脚手架 + 生成」与「阶段④ 选择运行」引用，命名前缀里的模块字母定义见 `interface-inventory.md` §5。*
