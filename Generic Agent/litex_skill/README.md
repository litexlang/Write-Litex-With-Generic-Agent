# Litex Problem Solving - SOP & Skills Package

打包时间: 2026-10-12 09:21:16
任务: Problem 16 (IMO 1968 P4) - 四面体边长三角不等式

## 📁 目录结构

### Litex/ (核心 SOP 和工具)
完整的 Litex 做题流程文档和工具集：

**主流程和路由**:
- `litex_problem_solving_workflow.md` - 唯一主流程（6 阶段）
- `START_HERE.md` - 文档路由索引

**语法与翻译**:
- `litex_syntax_quick_reference.md` - 语法速查（含 builtin 附录）✨ 已更新
- `litex_solution_translation_spec.md` - 解答翻译规范
- `litex_geometry_pitfalls.md` - 几何陷阱和保留变量

**证明与调试**:
- `litex_proof_guide.md` - 证明指南（核心机制与决策规则）✨ 已更新
- `litex_coordinate_solving_sop.md` - 坐标求解 SOP
- `litex_incremental_debugging_guide.md` - 增量调试指南（Session+REPL）

**跨文件与路径**:
- `litex_cross_file_reference_mechanism.md` - 跨文件引用机制（含路径速查）

**工具脚本**:
- `extract_problem.py` - 题目提取脚本（生成完整子文件夹结构）
- `start_full_logging.py` - 完整对话日志脚本（做题前必须启动）
- `parse_litex_error.py` - 错误解析工具（递归提取完整错误链）

### reference_resources/ (参考资源)
本次任务用到的关键参考文件：

- `citation.lit` - 实际证明示例（来自 The-Mechanics-of-Litex-Proof）
- `library_final.lit` - 几何库（纯公理定义，无证明）
- `problems_natural_language.json` - IMO 题目数据源

## 🆕 本次任务的重要更新

### litex_proof_guide.md - Pattern 4 (Contradiction)
- ✅ 添加了 `by contra:` 的完整语法约束
- ✅ 明确了 body 中不能使用 have/obtain/release 的限制
- ✅ 添加了与 `? forall ... =>:` 结合使用的完整示例

### litex_syntax_quick_reference.md - Critical rules
- ✅ 添加了 `--` 分隔符不再必需的说明（现代语法已弃用）
- ✅ 补充了 `by contra:` 的关键限制摘要
- ✅ 交叉引用到 litex_proof_guide.md 获取详细信息

## 🎯 核心发现

通过 Problem 16 的实战，发现了以下之前文档中**未明确记录**的关键知识：

1. **`by contra:` 的严格语法限制**:
   - 必须在定理体内（4空格缩进，与 `? forall` 同级）
   - 后面必须跟 `? <goal>` 重新声明目标
   - body 中只能包含等式/不等式推导链和最后的 `impossible`
   - **不能使用** `have`、`obtain`、`release`、`by def`、`by thm` 等语句

2. **`--` 分隔符已过时**:
   - library_final.lit 中完全不使用
   - 现代语法可以直接从定理声明跳到证明策略

3. **参考示例的位置**:
   - library_final.lit 是纯公理库，不包含任何证明
   - 需要查看 citation.lit 等 textbook 文件获取实际证明模式

## 📊 使用说明

1. **做题入口**: 每次做题唯一入口是 `Litex/litex_problem_solving_workflow.md`
2. **查找文档**: 使用 `Litex/START_HERE.md` 作为路由索引
3. **参考示例**: 遇到语法不确定时，查看 `reference_resources/citation.lit`
4. **工具脚本**: 按顺序使用 start_full_logging.py → extract_problem.py → parse_litex_error.py

## 🔗 路径配置

**重要**: 打包中的文档使用了占位符，使用前需要替换为你自己的路径。

### 占位符说明

- **`<YOUR_LITEX_REPO>`** → 你的 Litex 仓库根目录
  - 示例: `/path/to/LITEX-Geo/original/Geometry-Codex`
  - golitex 可执行文件位于: `<YOUR_LITEX_REPO>/golitex/target/release/litex`

- **`<YOUR_WORK_DIR>`** → 你的做题工作目录
  - 示例: `/path/to/LItex_vs_Lean_new-2/IMO`
  - 包含: `Math_Problem/problems_natural_language.json` 和 `solutions/` 目录

### 需要修改的文件

以下文件中包含占位符，使用前请手动替换：

1. **`Litex/extract_problem.py`** (第5行左右)
   - 修改 `LITEX_PATH` 变量

2. **`Litex/litex_cross_file_reference_mechanism.md`**
   - 文档中的示例路径

3. **`Litex/litex_problem_solving_workflow.md`**
   - 工作流程中的路径示例

### 标准目录结构

配置完成后，你的目录结构应该类似：

```
<YOUR_LITEX_REPO>/
├── golitex/target/release/litex  (可执行文件)
└── ...

<YOUR_WORK_DIR>/
├── Math_Problem/
│   └── problems_natural_language.json
├── Litex/geo/
│   └── library_final.lit
└── solutions/
    └── problem_X/
```

---

生成于 Problem 16 (IMO 1968 P4) 完成后
