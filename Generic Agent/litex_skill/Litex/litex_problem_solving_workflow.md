# Litex Problem Solving Workflow

**完整的 IMO 几何题做题流程（从题目 JSON 到全部答案文件验证通过）**

---

## 主流程与文档职责

本文件是 Litex 做题的**唯一编排入口**。每道题都按下列阶段执行；其他文档是被本流程按需引用的技能资料，不定义另一套流程，也不替代本文件的整题验收规则。

- **语法与解析**：`litex_syntax_quick_reference.md`（含 builtin 技能附录）
- **几何翻译与建模**：`litex_solution_translation_spec.md`（含库定理精确匹配规则）、`litex_geometry_pitfalls.md`（含保留变量清单）
- **模块与路径**：`litex_cross_file_reference_mechanism.md`（含路径速查）
- **证明构造与决策**：`litex_proof_guide.md`（整合核心机制与决策规则）
- **坐标专项**：`litex_coordinate_solving_sop.md`
- **增量调试**：`litex_incremental_debugging_guide.md`（Session 模式与 REPL-try 模式）

### 开始前的最小阅读

1. 先读本文，按阶段推进。
2. 形式化前查 `litex_syntax_quick_reference.md`（含 builtin 附录）、`litex_solution_translation_spec.md`（含库定理精确匹配规则），并检查 `library_final.lit`。
3. 证明阶段参考 `litex_proof_guide.md`（整合核心机制与决策规则）。
4. 只有涉及对应场景时，才读取坐标、Session、REPL 或错误诊断专项文档。
5. 任何文档中的旧命令、旧统计或历史案例都必须以当前 Litex 二进制的最小探针和本文第 4 阶段整题验收为准。

---

---

## 🎯 工作环境

```bash
工作目录: <YOUR_WORK_DIR>/IMO
题目 JSON: Math_Problem/problems_natural_language.json
库文件（唯一允许的几何库源文件）: Litex/geo/library_final.lit
输出目录: solutions/problem_X/  (每个题目一个子文件夹)
验证内核: /Users/judy-zhu/.../<YOUR_LITEX_REPO>/golitex/target/release/litex
```

**题目文件结构**：
```text
solutions/problem_X/
├── solution.lit                   # 单问题答案
├── solution_part_a.lit            # 多问时：第一问答案（替代 solution.lit）
├── solution_part_b.lit            # 多问时：第二问答案；更多小问同理
├── predicate.lit                  # 各问共享的自定义谓词（如果需要）
├── theorem.lit                    # 各问共享的自定义定理（如果需要）
├── litex.config                   # 按依赖顺序导出共享文件和全部答案文件
├── agent_session.log              # 完整做题日志（运行时生成）
├── litex_verified.json            # 整题模块普通验收（多问时需要）
├── litex_strict.json              # 整题模块 strict 验收（多问时需要）
├── litex_part_a_verified.json     # 多问时：第一问独立普通验收
├── litex_part_a_strict.json       # 多问时：第一问独立 strict 验收
├── litex_part_b_verified.json     # 多问时：第n问独立普通验收
├── litex_part_b_strict.json       # 多问时：第n问独立strict 验收
└── README.md                      # 题目信息和工作流程
```

单问题使用 `solution.lit`。多问任务不再使用一个答案文件轮流承载不同小问；每问从开始即使用独立 `solution_part_*.lit` 和独立 export。分问报告按实际小问继续命名，不要求固定只有 a/b 两问。

---

## 📋 第 0 阶段：启动完整对话日志（1 分钟）⚠️

**每次做题前必须先启动完整日志记录！**在独立终端运行：

```bash
cd <YOUR_LITEX_REPO>/generic agent

# 示例：为 problem 1 启动完整 Prompt/Response 捕获
python3 memory/Litex/start_full_logging.py 1
```

默认输出为：

```text
<YOUR_LITEX_REPO>/generic agent/temp/Litex/result_simplify/verified/problem_1/agent_session.log
```

**完整日志会记录**：
- 每轮 Prompt 和 Response 的原始结构
- 可见的 thinking、文本响应、`tool_use` 和 `tool_result`
- WORKING_MEMORY 内容、时间戳和模型名
- 当前 `temp/model_responses/` 中 agent 产生的完整响应流
- 同目录的 `.metadata.json`（来源、字节数、停止原因和 SHA-256）

**⚠️ 重要**：
- 日志脚本必须在独立终端先启动，做题过程在另一个终端进行
- 默认从启动时最新响应文件的末尾开始，只记录本题启动后的内容
- 做题结束后在日志终端按 Ctrl+C；这会写入 metadata 并关闭捕获
- 若要从当前响应文件开头记录，追加 `--from-start`
- 若该 problem 目录已有日志，需明确追加 `--overwrite` 才会替换原日志
- 长会话结束时须抽查日志尾部是否覆盖最终验收；`model_responses` 源文件可能在捕获期间轮转，而已打开的 capture 会继续跟随旧文件。若发现轮转，不要把新源强行 `--append` 到旧源偏移；应使用同一 capture 工具把新源从偏移 0 保存为单独的 `agent_session_continuation*.log`，保留每段各自的 `.metadata.json`、来源偏移和 SHA-256，并在题目 README 中注明分段顺序。若结束前需刷新续段，应重新生成完整快照并覆盖该续段，不使用 `--append`：当前 capture 的 append 元数据中 `bytes` 只记录本次增量，而 SHA-256 覆盖整个输出文件，不能用 `文件大小 == bytes` 做完整性校验。

---

## 📋 第 0.5 阶段：预检唯一几何库（必须先做）

在翻译题目或编写证明前，先独立严格验收唯一允许的几何库。这样可以把库本身的定义域错误与题目证明错误分开。

**库修改边界（硬规则）**：只有当这次独立库预检明确显示 `library_final.lit` 自身未通过 Litex 检验时，才允许修复该指定库的真实错误；预检通过后，任何题目的翻译、形式化或证明遇到困难，都禁止为了方便修改库。此时只能修改本题的 `predicate.lit`、`theorem.lit`、单问 `solution.lit` 或多问 `solution_part_*.lit` 及题目配置；不得添加库谓词、放宽库前提、改库调用语义或换用副本。库预检失败时也只能修复已定位的库错误，修复后必须重新独立 strict 验收，再开始或继续题目证明。

```bash
cd <YOUR_WORK_DIR>/IMO/Litex/geo
<YOUR_LITEX_REPO>/<YOUR_LITEX_REPO>/golitex/target/release/litex -runner -r . -all -strict -json > /tmp/library_final_strict.json
jq '{result, ok, error, target}' /tmp/library_final_strict.json
```

只有 `result=success` 且 `ok=true` 才能继续。库中的带定义域函数（例如 `angle_cos_num/den`）必须在调用它们的谓词中先显式提供全部非退化条件；遇到 `not well-defined` 时，沿错误链检查函数签名和前提，不要先改题目证明。

---

## 📋 第 1 阶段：提取题目（2 分钟）

### 使用提取脚本

```bash
cd <YOUR_WORK_DIR>/IMO

# 提取题目并生成完整模板结构
python3 /path/to/memory/Litex/extract_problem.py <problem_id>

# 仅查看题目不生成模板
python3 /path/to/memory/Litex/extract_problem.py <problem_id> --no-template
```

**输出**（在 `solutions/problem_X/` 目录下）：
- `solution.lit` - 主解答模板（包含翻译规范提醒）
- `predicate.lit` - 自定义谓词模板
- `theorem.lit` - 自定义定理模板
- `litex.config` - 与 `problem_1` 一致的模块导入和导出顺序
- `README.md` - 题目信息和说明

提取脚本会自动生成以下模块配置，`.lit` 模板内不再写文件内导入；生成已有题目会覆盖该题模板文件，务必先检查目标目录，避免覆盖已完成的证明：

```toml
[hierarchy]
module

[import]
geo = "../../Litex/geo"

[export]
predicate = "./predicate.lit"
theorem = "./theorem.lit"
solution = "./solution.lit"
```

`Litex/geo/litex.config` 的 `[export] main = "./library_final.lit"` 指向唯一准用的几何库原文件；不要直接将 `.lit` 路径填进 `[import]`，不要改用副本或硬链接别名。保留 `geo` 命名空间、`predicate → theorem → solution` 导出顺序；按第 4 阶段执行完整模块验证，并单独报告严格模式与受信任导入。

提取后先读完整题面并识别小问数量。多问任务从开始就让每问使用独立答案文件和独立 export（如 `solution_part_a.lit`、`solution_part_b.lit`），共享定义和引理仍放在 `predicate.lit`、`theorem.lit`；不得先把一问写入 `solution.lit`，再用后一问覆盖。每份答案文件头按用户要求保留完整题面，但该文件只形式化并证明对应小问。

继续已有答案前，先记录正式 `.lit` 源码哈希；新增小问时新增 export，不改写既有小问答案。完成后既要按第 4 阶段验收包含全部小问的正式模块，也要在需要证明分问独立性时生成对应的分问证据；所有新报告使用未占用且语义准确的文件名，不覆盖已有问或整题报告。

---

## 📋 第 2 阶段：形式化（15-30 分钟）

### 2.1 定义几何对象

```litex
have a, b, c cart(R, R):
    # NL: Points A, B, C
```

### 2.2 定义实数参数

```litex
have r, rho R:
    # NL: circumradius r, inradius rho
    r > 0
    rho > 0
```

### 2.3 形式化条件为 prop

```litex
prop conditions(a, b, c, r, rho cart(R, R)):
    # NL: Triangle ABC is isosceles with AB = AC
    distance_sq(a, b) = distance_sq(a, c)
```

### 2.4 形式化目标为 prop

```litex
prop statement(o, i, r, rho cart(R, R)):
    # NL: d = sqrt(r(r - 2*rho))
    distance_sq(o, i) = r * (r - 2 * rho)
```

**关键规则**：
- 每行 NL 注释对应一行 Litex 代码
- 不在 prop 中写推理，只翻译给定事实
- 唯一允许的几何库源文件是 IMO 下 `Litex/geo/library_final.lit`；可直接复用的现成几何谓词只来自这个文件，不得换成其他库、同内容副本或硬链接别名；缺少所需谓词时在本题 `predicate.lit` 新建。
- Litex 的 `[import]` 接受模块目录，不接受 `.lit` 文件路径；导入前核对目标模块的 `[export]` 确实指向上述原文件。若原目录模块配置不能加载，先报告阻塞并征得项目代码修改许可，不得私自改用 其他任何库。

---

## 📋 第 3 阶段：证明（30-60 分钟）

### 3.1 构建主定理

```litex
thm problem_X:
    forall a, b, c, r, rho cart(R, R):
        conditions(a, b, c, r, rho) => statement(...)
--
    # Proof here
```

### 3.2 证明策略
**综合几何路线优先**

**综合几何路线**：
1. 使用几何谓词（已有的直接用，没有的创建进predicate.lit后再用）
2. 引用库中已有定理（已有的直接用，没有的创建进theorem.lit后再用）

**坐标几何路线**：
1. 建立坐标系
2. 计算坐标
3. 化简

### 3.3 证明模式（参考 litex_proof_writing_sop.md）

## 示例：
```litex
have fact_1: some_property
    by thm some_theorem

claim step_1:
    target_equation
    --
    # detailed proof
```

---

## 📋 第 4 阶段：验证（10-30 分钟）

### 4.1 运行验证并保存输出 ⚠️ **关键！**

**唯一的题目模块验收入口（2026-09-22 在 problem_1 实测）**：

1. 从 IMO 目录确认 `solutions/problem_X/litex.config` 的 `[export]` 包含本题全部 `.lit`，且依赖文件排在引用它的文件之前；逐一确认单问 `solution.lit` 或全部 `solution_part_*.lit` 的命名空间与各自导出名一致。
2. 在题目目录执行下面的命令。`-r .` 递归检查模块的全部导出；`-f FILE` 只运行到该文件为止，不能替代模块验收。`-isolated` 不加载模块配置；`-target` 仅用于有意缩小调试范围，不能作为整题验收。

```bash
cd <YOUR_WORK_DIR>/IMO/solutions/problem_X/
<YOUR_LITEX_REPO>/<YOUR_LITEX_REPO>/golitex/target/release/litex -runner -r . -all -json > litex_verified.json
```

**普通模式与严格模式不可混称**：普通模式成功仅说明本题导出在所列受信任导入下通过。`-all` 显示信任警告，不会消除信任。若任务要求零信任，仍在上述题目目录另运行同模块的严格检查，并单独保留结果：

```bash
<YOUR_LITEX_REPO>/<YOUR_LITEX_REPO>/golitex/target/release/litex -runner -r . -all -strict -json > litex_strict.json
jq '{result, ok, error, target}' litex_strict.json
jq -r '.trace' litex_strict.json
```

逐项检查严格结果和全部预期导出。`-strict` 也检查配置导入；如失败发生在原库中，应报告原库阻断，不能宣称严格证明完成，也不要靠换入口消除错误。严格运行生成的 `litex_strict.json` 是单独的验证证据，不应覆盖普通模式的 `litex_verified.json`。

#### 多问任务的两层验收（2026-09-23 在 problem_2 实测）

1. **整题模块验收是必需项**：正式 `litex.config` 导出共享依赖和全部 `solution_part_*.lit`，按上面的普通、strict 命令分别生成 `litex_verified.json` 与 `litex_strict.json`。它证明所有小问可以在正式模块中共同加载，但不能据此声称某一问被独立验证。
2. **分问独立验收按需执行**：当需要证明某问不依赖其他问时，在 `solutions/` 下创建与 `problem_X/` **并列**的一次性临时模块。该模块只包含未改动的共享 `predicate.lit`、`theorem.lit` 和目标 `solution_part_N.lit`，配置只导出这些文件。不要把临时模块放进正式题目目录；problem_2 实测中嵌套模块发生父配置边界冲突，并列模块成功隔离。
3. 在临时模块分别运行普通与 strict 全模块检查，将结果写回正式题目目录的 `litex_part_N_verified.json` 和 `litex_part_N_strict.json`。分问证据不能覆盖整题证据。
4. **文件名不是证据**：每份 JSON 都必须检查 `result=success`、`ok=true` 和完整 `trace`。目标小问的全部预期定理名必须出现，其他小问的主定理和专属辅助定理必须不出现；否则不能命名或描述为该问的独立报告。普通报告中的导入 trust 警告与 strict 报告分开解释。
5. 临时验证前后核对正式 `.lit` 文件 SHA-256；确认哈希不变后，仅删除本轮创建的临时模块。保留正式源码和四类证据，不按通配符清理。

### 4.2 检查结果

```bash
cd <YOUR_WORK_DIR>/IMO/solutions/problem_X/

# 检查结构化结果；再阅读 trace 中的受信任依赖及实际检查的定理
jq '{result, ok, error, target}' litex_verified.json
jq -r '.trace' litex_verified.json
# 只有 result=success 且 ok=true，并确认全部预期导出/定理通过，才算普通模式验收。
# 不允许仅凭答案文件中没有 trust 就声称整个证明零信任。
```

### 4.3 调试错误

**使用错误解析工具提取完整错误链**：

```bash
cd <YOUR_WORK_DIR>/IMO/solutions/problem_X/

# 自动提取并格式化错误信息（递归显示所有 previous_error）
python3 '<YOUR_LITEX_REPO>/generic agent/memory/Litex/parse_litex_error.py' litex_verified.json
```

**常见错误类型**（参考 litex_proof_decision_rules.md）：
- **"cannot prove goal"** → 检查证明步骤是否完整
- **"unknown fact"** → 检查是否引用了不存在的 fact
- **"type mismatch"** → 检查谓词参数类型
- **"module not found"** → 检查 import 路径是否正确

---

## 📋 第 5 阶段：停止记录并归档（5 分钟）

### 5.1 核对题目文件与依赖的信任边界

```bash
cd <YOUR_WORK_DIR>/IMO/solutions/problem_X/
# 仅检查题目源文件中是否有直接 trust；不能由此推出导入的库也零信任
grep -n 'trust' -- solution*.lit predicate.lit theorem.lit 2>/dev/null
```

检查第 4 阶段的 JSON trace，报告所有受信任导入。需要全量零信任时，须对同一模块另做严格验收；若原库先报错，如实记录阻断，不将普通模式成功写成零信任。

### 5.2 停止日志记录

在运行日志脚本的终端按 **Ctrl+C** 停止记录。

若包装器在后台运行、无法向原终端发送 Ctrl+C，先用进程父子关系定位该包装器唯一的 `imo_litex_log.py capture` 子进程，再只向这个 capture 子进程发送 `SIGINT`。不要只向 `start_full_logging.py` 包装器发送定向 `SIGINT`：包装器阻塞在 `subprocess.call` 时可能不会把信号转发给 capture。停止后必须确认 capture 与包装器都已退出，并在短暂等待后复查日志大小不再增长。

### 5.3 清理调试文件 ⚠️
归档前先枚举候选文件，逐个确认是否为本题产生的临时调试产物；不要按文件名模式批量删除，尤其不要清理 IMO 根目录的其他题目或共享工具。

```bash
# 从任意目录运行；只列候选，不删除
find <YOUR_WORK_DIR>/IMO/solutions/problem_X -maxdepth 1 -type f \( \
  -name 'DEBUGGING_*.md' -o -name 'VERIFICATION_*.md' -o \
  -name 'temp_*' -o -name 'test_*' -o -name '*_DEBUG*.md' \
\) -print
```

检查每个候选文件的内容和用途；从 IMO 目录运行 `git status --short -- solutions/problem_X` 核对改动。仅在确认其为可丢弃的本题调试文件后逐个清理。若候选包含用户文件、正式测试、日志或来源不明的改动，先保留并询问，不执行通配删除。

### 5.4 最终文件清单

在 IMO 目录执行 `ls -la solutions/problem_X/`。单问题确认 `solution.lit`，多问确认全部 `solution_part_*.lit` 与对应 exports；同时保留 `litex.config`、整题 `litex_verified.json`、本题用到的 `predicate.lit`、`theorem.lit`、日志和题目信息文件。执行过 strict 或分问独立验收时，还要保留语义准确的 `litex_strict.json`、`litex_part_N_verified.json`、`litex_part_N_strict.json`，包括失败及原库阻断证据。若旧报告的 trace 与文件名不符，将其标为 superseded，确认已有正确替代证据且不被引用后再询问或逐个删除；其他文件也不得因文件名不在清单内就删除。

### 5.5 质量检查

1. 按第 4 阶段用 `jq` 查看结构化 JSON 的 `result`、`ok`、`error`、`trace`，核对每个预期导出和定理；不要统计含 `success` 的文本行数代替验收。
2. 做题过程中产生的经验应归并到本目录已有的通用语法、翻译、跨文件或工作流文档；不要为每道题继续创建独立 lessons/SOP 文件。题目目录只保留题目源码、验证证据和必要日志；历史调试快照中的轮数、旧命令和旧成功数字不能替代当前验证。
3. 任何语法或证明结构不确定时，先查 `litex_syntax_quick_reference.md`，再用单一特性的最小探针确认解析、普通验证和 strict 行为；不要从一次报错泛化完整语法规则。
4. 按 5.1 核对本题直接 trust 与导入信任，分别报告普通模式和严格模式结果。
5. 检查日志是否完整并已停止记录；如有未解决的验证失败，保留错误证据并如实说明，不能以“目录干净”宣布完成。

---

## 📋 第 6 阶段：回看日志并沉淀经验（完成题目后必做）

本阶段不是可选的题目总结，而是每道题结束时的知识维护步骤。必须在第 5 阶段确认日志已停止后执行；不要在日志仍写入时读取或修改经验文档。

### 6.1 回看本题日志

日志通常位于：

```text
<agent_root>/temp/Litex/result_simplify/verified/problem_<id>/agent_session.log
```

从日志中提取本题实际发生的内容，不凭记忆补写。至少检查：

1. 首次失败的错误、当时使用的命令和最终确认有效的修正。
2. 任何导致返工的错误假设，例如把局部 `-f` 成功当作整题通过、覆盖多问答案、混淆普通与 strict 验证，或误用未经验证的语法。
3. 经当前 Litex 二进制或成功工具调用确认、且未来其他题仍可复用的规则。
4. 尚未解决的失败、原库阻断或只适用于本题的偶然细节。

只把第 3 类作为候选经验；第 1、2 类用于判断归类，第 4 类保留在题目日志和验证证据中，不写成通用规则。

### 6.2 归并到已有文档

经验按主题写入现有文档，禁止创建 `problem_<id>_lessons_learned.md`、独立 lessons 文件或新的重复 SOP：

| 经验主题 | 唯一归档位置 |
|---|---|
| 语法、解析、变量、证明语法边界 | `litex_syntax_quick_reference.md` |
| 自然语言翻译、谓词选择、主定理接口 | `litex_formalization_sop.md` 或 `litex_solution_translation_spec.md` |
| 几何建模陷阱、坐标表示 | `litex_geometry_pitfalls.md` 或 `litex_coordinate_solving_sop.md` |
| 跨文件引用、导出、配置、路径 | `litex_cross_file_reference_mechanism.md` 或 `litex_path_and_environment.md` |
| 局部证明步骤、证明策略、自动推理边界 | `litex_proof_writing_sop.md`、`litex_proof_decision_rules.md` 或 `litex_builtin_verification_skills.md` |
| Session/REPL 增量调试 | `litex_session_verification_sop.md` 或 `litex-repl-try-workflow.md` |
| 整题流程、日志、验收、归档、经验回写 | 本文件 |

若一条经验看似属于多个文件，只选择一个最具体、最稳定的归属，并在其他文档添加引用而不是复制全文。历史题号、调试轮数、临时路径和只对单题成立的桥定理不应进入通用 SOP。

### 6.3 写入前后核验

1. 读取目标文档当前内容和末尾，确定插入位置，避免覆盖既有经验或重复条目。
2. 只写入已由日志和工具结果共同支持的简短规则；不把猜测、失败尝试或未验证语法写成事实。
3. 写入后重新读取新增段落，并检查 `git diff -- memory/Litex`；确认没有新建题目 lessons/SOP 文件。
4. 若没有可复用的新规则，只记录本题验证证据，不修改知识文档。

完成第 6 阶段后，题目才算完成。下一题仍从第 0 阶段启动新的日志，并重新按本文件路由所需技能。

---

## 📚 速查文档（做题中按需查阅）

### 遇到验证错误时
- **litex_proof_writing_sop.md** - 证明模式和调试清单
- **litex_proof_decision_rules.md** - "cannot prove goal" 决策树
- **litex_builtin_verification_skills.md** - 自动推理能力查询

### 特殊场景
- **litex_coordinate_solving_sop.md** - 坐标几何专用
- **litex_session_verification_sop.md** - Session 模式和 trust 管理
- **litex-repl-try-workflow.md** - REPL 交互式调试
