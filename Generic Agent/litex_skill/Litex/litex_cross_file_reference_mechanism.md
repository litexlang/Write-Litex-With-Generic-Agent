# Litex 跨文件引用机制（Cross-File Reference Mechanism）

**基于 IMO 1960 Problem 3 调试过程的完整总结**

---

## 🎯 核心结论

### ✅ 谓词（prop）可以跨文件使用

**机制**：
```litex
# 在 litex.config 中配置
[export]
predicate = "./predicate.lit"

# 在 predicate.lit 中定义
prop my_predicate(x, y R):
    x * x + y * y = 1

# 在 solution.lit 中引用（必须使用 $ 前缀）
$predicate::my_predicate(a, b)
```

**验证来源**：
- `problem_207` 成功使用 `translation.lit` 定义谓词
- 在 `solution.lit` 中通过 `$translation::is_right_triangle(...)` 成功引用

### ✅ 定理（thm）可以跨文件引用

在 `litex.config` 的 `[export]` 中把 `theorem = "./theorem.lit"` 排在 `solution = "./solution.lit"` 前。`solution.lit` 使用 `by thm theorem::my_theorem(x, y)`，**不要**在 `by thm` 中加 `$`。IMO problem_1 的 `solution.lit` 用 `by thm theorem::central_coordinate(...)` 成功引用并在 `-runner -r . -all -json` 中验证。

---

## 📁 文件组织原则

### 实测可用结构（IMO problem_1）

```
solutions/problem_X/
├── predicate.lit         # 仅在原库无相应谓词时新增
├── theorem.lit           # 新增辅助定理及证明
├── solution.lit          # 仅题目最终陈述与解答
└── litex.config          # 导出按依赖顺序排列
```

`solution.lit` 可通过 `$predicate::name(...)` 和 `by thm theorem::name(...)` 引用前置导出。优先用指定几何库已有谓词，不把题目前提/结论翻译成展开的坐标式。

---

## 🔧 litex.config 配置

**按依赖排列导出**（仅导出实际存在的文件）：
```toml
[export]
predicate = "./predicate.lit"
theorem = "./theorem.lit"
solution = "./solution.lit"
```

路径相对于 `litex.config`；以实际题目的配置和依赖为准，不得遗漏 `theorem` 或 `solution`。

---

## 🚫 常见错误和解决方案

- `by thm $theorem::my_helper_theorem(a)`：`$` 不能出现在 `by thm` 的定理名之前；应写 `by thm theorem::my_helper_theorem(a)`。
- 找不到 `theorem::...`：核对 `litex.config` 是否导出 `theorem.lit`、是否排在 `solution.lit` 前，以及定理名称/参数是否一致。
- 旧调试曾因误用 `$theorem::` 得出“定理必须内联”的错误结论；现有 problem_1 已用跨文件定理并通过普通模块验证，不得再按旧结论迁移引理。

---

## 📚 参考案例

### problem_207：成功使用跨文件谓词

```
problem_207/
├── solution.lit          # 使用 $translation::is_right_triangle(...)
├── translation.lit       # 定义 is_right_triangle 谓词
└── litex.config          # [export] predicate = "./translation.lit"
```

**关键点**：
- `translation.lit` 定义的是**谓词（prop）**，不是定理（thm）
- 可以在 `solution.lit` 中通过 `$translation::is_right_triangle(...)` 引用
- 这是旧案例（文件名为 `translation.lit`）；本项目新增谓词统一放 `predicate.lit`。

### IMO 1960 Problem 3：跨文件谓词与引理

`problem_1/litex.config` 导出 `predicate.lit`、`theorem.lit`、`solution.lit`；主定理以 `by thm theorem::central_coordinate(...)` 等语句引用辅助定理。运行完整模块验收命令后，6 条引理和主定理均通过普通模式检查（外部 `geo` 导入仍受信任）。此前“全部内联”记录是过时的调试状态，不是规范。

---

## 🔧 模块验证命令（关键发现）

**基于 IMO 1960 Problem 3 的 115+ 轮调试经验（2026-09-22）**

### ✅ 当前整题验收：按配置递归检查全部导出

在 `solutions/problem_X/` 检查 `litex.config` 的导入路径、导出名和依赖顺序，然后按 `litex_problem_solving_workflow.md` 第 4 阶段执行**唯一的完整模块验收**：

```bash
<YOUR_LITEX_REPO>/<YOUR_LITEX_REPO>/golitex/target/release/litex -runner -r . -all -json > litex_verified.json
jq '{result, ok, error, target}' litex_verified.json
jq -r '.trace' litex_verified.json
```

`-f FILE` 只运行到 FILE 的模块前缀，适合定位错误，不代表整个模块已验证；`-target` 也仅用于局部调试。旧案例通过 `-f translation.lit` 的成功记录只能说明当时的检查范围，不能作为所有题目的完整验收命令。遇到 `fact not defined` 先核查配置中导出顺序和引用名称，再核查目标运行范围，不得断言 Litex 不支持跨文件引用。普通模式的受信任导入须从 trace 如实报告；严格模式单独检查。

---

## ✅ 最佳实践

### 1. 谓词的使用

- 唯一允许导入的几何库源文件是 IMO 下 `Litex/geo/library_final.lit`；现成几何谓词只能取自该文件，不能改用其他库或同内容的别名（包括硬链接）。核对导入模块的 `[export]` 是否指向原文件。
- 原文件缺少所需谓词时，在本题 `predicate.lit` 中新建，不能从其他几何库借用。
- 在 `litex.config` 中配置 `[export] predicate = "./predicate.lit"`
- 在 `solution.lit` 中使用 `$predicate::prop_name(...)` 引用

### 2. 定理的使用

- 新辅助定理及证明放在 `theorem.lit`；在配置中排在 `solution.lit` 前。
- `solution.lit` 只保留本题最终定理和证明，使用 `by thm theorem::bridge_1(...)` 引用引理。
- 不要在 `by thm` 中给定理名加 `$`。

### 3. 文件组织

`predicate.lit` 定义仅在指定库缺失时新增的谓词；`theorem.lit` 证明新增引理；`solution.lit` 陈述并证明最终题目。完整验证以主流程第 4 阶段为准。

---

## 🔍 跨文件调用前的接口检查

跨文件引用失败时，先逐项核对导出接口，再判断是否为语言能力限制：

- 定理定义与调用的参数数量、顺序、类型必须完全一致；漏掉一个参数或调换顺序都会表现为匹配失败。
- `litex.config` 的导出顺序必须满足依赖先于引用者；检查实际导出名与命名空间，不要只检查文件是否存在。
- 旧的局部 `-f FILE` 成功只能说明该文件前的模块前缀通过，不能证明整个配置或全部导出通过。

## 🎓 总结

跨文件谓词用 `$predicate::name(...)`，跨文件定理用 `by thm theorem::name(...)`；先核对接口和 `litex.config` 导出顺序，再递归验证整模块，并分别报告普通/严格模式的信任边界。


---

## 路径和环境配置速查

### 核心路径

```bash
# 工作目录
cd <YOUR_WORK_DIR>/IMO

# Litex 可执行文件
<YOUR_LITEX_REPO>/<YOUR_LITEX_REPO>/golitex/target/release/litex

# 库文件
Litex/geo/library_final.lit

# 题目 JSON
Math_Problem/problems_natural_language.json

# 输出目录
solutions/problem_X/
```

### 常见路径错误

**错误 1: 找不到 litex 可执行文件**

错误现象：`litex: command not found`

解决方案：使用完整路径
```bash
<YOUR_LITEX_REPO>/<YOUR_LITEX_REPO>/golitex/target/release/litex \
  -runner -r . -all -json > litex_verified.json
```

**错误 2: 找不到 library_final.lit**

解决方案：确保在 IMO 目录下执行
```bash
cd <YOUR_WORK_DIR>/IMO
grep "is_right_angle" Litex/geo/library_final.lit
```

**错误 3: 工作目录混乱**

解决方案：始终从 IMO 目录作为根目录，使用相对路径引用库和题目

---

**环境要求**：
- 工作目录必须是 IMO 根目录
- litex.config 中的相对路径基于题目子目录
- 库导入路径基于 IMO 根目录
