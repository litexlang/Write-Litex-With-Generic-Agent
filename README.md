# Write Litex With Generic Agent

使用 [Generic Agent](https://github.com/lsdefine/GenericAgent) 进行 Litex 数学证明的技能包和配置。

> **重要**: 本项目使用 [Generic Agent](https://github.com/lsdefine/GenericAgent) 作为 AI Agent 框架，不是独立开发的 agent。Generic Agent 是一个通用的 AI 代理系统，本仓库提供的是让 Generic Agent 掌握 Litex 证明语言的技能包（Skills）和记忆配置（Memory）。

## 📋 项目简介

本项目包含：
- **`generic agent/`**: 配置好的 Generic Agent 实例，包含 Litex 做题所需的记忆结构
- **`litex_skill/`**: Litex 证明语言的完整技能包（SOP 和工具）

通过这些配置，Generic Agent 可以：
- ✅ 使用 Litex 语言形式化数学问题
- ✅ 编写和验证几何证明
- ✅ 处理 IMO 级别的数学竞赛题目
- ✅ 自动调试 Litex 代码并修复错误

## 🚀 快速开始

### 前置要求

1. **安装 Generic Agent**
   ```bash
   # 参考官方文档
   # https://github.com/lsdefine/GenericAgent
   ```

2. **安装 Litex 编译器**
   - 获取 golitex 可执行文件（`golitex/target/release/litex`）
   - 确保编译器版本 >= 1.0.5-beta

### 配置步骤

#### 方法 1: 使用预配置的 Generic Agent

```bash
# 1. 克隆本仓库
git clone https://github.com/litexlang/Write-Litex-With-Generic-Agent.git
cd Write-Litex-With-Generic-Agent

# 2. 将 litex_skill 复制到 generic agent 的 memory
cp -r litex_skill/* "generic agent/memory/"

# 3. 配置路径占位符
# 编辑以下文件，将占位符替换为你的实际路径：
# - generic agent/memory/Litex/extract_problem.py (LITEX_PATH)
# - 其他包含 <YOUR_LITEX_REPO> 和 <YOUR_WORK_DIR> 的文件

# 4. 启动 Generic Agent
cd "generic agent"
# 按照 Generic Agent 的启动方式运行
```

#### 方法 2: 为现有 Generic Agent 添加 Litex 技能

```bash
# 1. 克隆本仓库
git clone https://github.com/litexlang/Write-Litex-With-Generic-Agent.git

# 2. 复制技能包到你的 Generic Agent 的 memory 目录
cp -r Write-Litex-With-Generic-Agent/litex_skill/Litex /path/to/your/generic_agent/memory/

# 3. 更新 memory/global_mem.txt 或 global_mem_insight.txt
# 添加以下内容：
echo "L3: Litex/ (Litex 做题技能包)" >> /path/to/your/generic_agent/memory/global_mem_insight.txt

# 4. 配置路径
# 编辑 memory/Litex/ 中的文件，替换路径占位符
```

### 路径配置说明

技能包中使用了以下占位符，需要替换为你的实际路径：

- **`<YOUR_LITEX_REPO>`**: Litex 仓库根目录
  - 例如: `/path/to/LITEX-Geo/original/Geometry-Codex`
  - golitex 可执行文件应位于: `<YOUR_LITEX_REPO>/golitex/target/release/litex`

- **`<YOUR_WORK_DIR>`**: 做题工作目录
  - 例如: `/path/to/LItex_vs_Lean_new-2/IMO`
  - 应包含: `Math_Problem/problems_natural_language.json` 和 `solutions/` 目录

## 💡 使用示例

配置完成后，直接与 Generic Agent 对话即可开始做题：

### 示例 1: 做一道题

```
User: 用 Litex 做 IMO 题目，problem 16

Agent: [自动执行]
1. 启动完整对话日志
2. 提取题目并生成模板
3. 形式化问题和证明
4. 验证并生成报告
```

### 示例 2: 查找未完成的题目

```
User: 找一道还没做过的平面几何 medium 题

Agent: [搜索 problems_natural_language.json]
找到符合条件的题目 X...
现在开始形式化...
```

### 示例 3: 调试 Litex 代码

```
User: solutions/problem_16/solution.lit 验证失败了，帮我调试

Agent: [读取错误日志]
发现问题：...
修复方案：...
[自动修复并重新验证]
```

## 📁 技能包结构

### `litex_skill/Litex/` 核心文档

**主流程**:
- `litex_problem_solving_workflow.md` - 完整的 6 阶段做题流程（**唯一入口**）
- `START_HERE.md` - 文档导航索引

**语法与翻译**:
- `litex_syntax_quick_reference.md` - Litex 语法速查（含 builtin）
- `litex_solution_translation_spec.md` - 自然语言到 Litex 的翻译规范
- `litex_geometry_pitfalls.md` - 几何形式化的常见陷阱

**证明与调试**:
- `litex_proof_guide.md` - 证明策略和机制（核心）
- `litex_incremental_debugging_guide.md` - 增量调试指南
- `litex_coordinate_solving_sop.md` - 坐标几何求解 SOP

**跨文件引用**:
- `litex_cross_file_reference_mechanism.md` - 模块系统和路径规则

**工具脚本**:
- `extract_problem.py` - 题目提取脚本
- `start_full_logging.py` - 完整对话日志脚本
- `parse_litex_error.py` - 错误解析工具

### `litex_skill/reference_resources/` 参考资源

- `citation.lit` - 实际证明示例（来自 Litex 官方教程）
- `library_final.lit` - 几何库（公理和定义）
- `problems_natural_language.json` - 题目数据源

## 🎯 工作流程

Generic Agent 遵循以下 6 阶段流程：

1. **阶段 0**: 启动完整对话日志（`start_full_logging.py`）
2. **阶段 1**: 提取题目（`extract_problem.py` → 生成 `solutions/problem_X/`）
3. **阶段 2-3**: 形式化和证明（编辑 `solution.lit`）
4. **阶段 4**: 验证（`litex -f solution.lit`）
5. **阶段 5**: 停止记录并归档（保存日志和报告）
6. **阶段 6**: 回看日志并沉淀经验（更新技能文档）

详见 `litex_skill/Litex/litex_problem_solving_workflow.md`

## 📊 已验证成果

使用本技能包，Generic Agent 已完成：
- ✅ IMO 1968 Problem 4 (四面体边长三角不等式)
- ✅ 多道平面几何题目的形式化和验证
- ✅ 发现并记录了 Litex 语言的多项语法规则

查看 `experiment2(IMO)/solutions/` 目录了解具体案例。

## 🔗 相关链接

- **Generic Agent 框架**: https://github.com/lsdefine/GenericAgent
- **Litex 语言**: https://github.com/litexlang
- **实验数据**: https://github.com/litexlang/litex-ai-experiments1

## 📝 许可证

本项目遵循与 Generic Agent 相同的许可证。技能包（litex_skill）中的内容为 Litex 证明语言的使用指南和示例，可自由使用和修改。

## 🙏 致谢

- 感谢 [Generic Agent](https://github.com/lsdefine/GenericAgent) 提供强大的 AI 代理框架
- 感谢 Litex 社区提供优秀的证明语言工具

## 📮 反馈

如有问题或建议，请在 GitHub Issues 中提出。
