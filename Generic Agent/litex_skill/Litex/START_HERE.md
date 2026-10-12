# Litex 做题文档导航

本文件只负责**路由**。Litex 做题的唯一主流程是
`litex_problem_solving_workflow.md`；它负责六个阶段、日志生命周期、整题验收和做题后经验回写。任何专项文档都不能替代主流程或定义另一套顺序。

## 入口

- 主流程：`litex_problem_solving_workflow.md`
- 题目提取工具：`extract_problem.py`
- 完整对话日志：`start_full_logging.py`
- 错误解析工具：`parse_litex_error.py`

按主流程开始；不要先按本索引逐篇通读。遇到对应阶段或具体问题时，再从下表打开技能文档。

---

## 主流程六阶段与对应技能文档

| 阶段 | 技能文档 |
|------|----------|
| 第 0 阶段：启动日志 | `start_full_logging.py` |
| 第 1 阶段：提取题目 | `extract_problem.py` |
| 第 2 阶段：形式化 | `litex_syntax_quick_reference.md`（含 builtin 附录）、`litex_solution_translation_spec.md`（含库定理精确匹配规则）、`litex_geometry_pitfalls.md`（含保留变量清单）、`litex_cross_file_reference_mechanism.md`（含路径速查） |
| 第 3 阶段：证明 | `litex_proof_guide.md`（整合核心机制与决策规则） |
| 第 4 阶段：验证 | `parse_litex_error.py` |
| 第 5 阶段：停止记录并归档 | - |
| 第 6 阶段：回看日志并沉淀经验 | 归并到上述对应阶段的技能文档；不新建题目专属 SOP |

## 专项场景技能

只在遇到对应问题时查阅，不作为必读流程：

- **坐标几何**：`litex_coordinate_solving_sop.md`
- **增量调试**：`litex_session_verification_sop.md`、`litex-repl-try-workflow.md`

## 文档使用原则

1. 主流程定义唯一顺序；专项文档被主流程按需引用，不定义独立的"开始前必读"清单。
2. 遇到具体阶段或错误时再查阅对应技能文档；不要先通读全部索引。
3. 做题后第 6 阶段必须回看 `agent_session.log`，只把经日志和工具共同验证的可复用经验归并到已有主题文档。
4. 禁止为单题创建独立的 lessons/SOP 文件；历史题号、调试轮数和临时桥定理不应进入通用知识库。

---

**更新日期**：2026-09-23  
**维护者**：请在每次添加/删除文档后更新主流程和本索引
