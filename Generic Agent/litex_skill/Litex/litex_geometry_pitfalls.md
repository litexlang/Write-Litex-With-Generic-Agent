# Litex Geometry Pitfalls and Best Practices

## 概述
本文档记录在使用litex进行几何定理形式化验证时遇到的常见陷阱和最佳实践。

---

## 0. 变量命名规则（关键！）

### 保留变量清单

**🔴 Critical**: `e` 是 Litex 保留变量（可能是数学常数 e = 2.71828）

**症状**：
```litex
thm test:
    ? forall a, b, c, d, e, f, g cart(R, R):  # ❌ 报错！
        ...
```
错误：`ParseError: name 'e' is already active in this scope and cannot be rebound`

**验证**：改用 `pt_e` 或其他多字母名称即可通过解析。

### 问题描述
Litex 对变量名有严格限制，某些字母被保留或预定义，使用它们会导致 "name X is already active" 错误。

### 保留字母
- **大写字母全部避免**：`A`, `B`, `C`, `D`, `E`, `Q`, `R` 等可能被用作类型变量或其他用途
- **单字母 `e`**：自然对数底数 e（2.71828...）
- **单字母 `R`**：实数类型名

### 正确命名约定
✅ **推荐做法**：
- 使用小写字母：`a, b, c, d` 而不是 `A, B, C, D`
- 使用多字母名称：`pe, pa, pb, pc` 而不是 `e, a, b, c`
- **对于点变量**：使用 `ptA, ptB, ptC, ptD` 而不是 `A, B, C, D`（推荐前缀 `pt`）
- 避免单字母变量（除了常见的如 `a, b, c, d, p, q, r, s, t, u, v, w, x, y, z`）

❌ **错误示例**：
```litex
thm problem:
  ? forall A, B, C, D, E cart(R, R):  # 错误：大写字母
      ...
```
错误信息：`name 'C' is already active in this scope and cannot be rebound`

✅ **正确示例**：
```litex
thm problem:
  ? forall ptA, ptB, ptC, ptD cart(R, R):  # 正确：使用 pt 前缀
      ...
```

### 调试技巧
如果遇到 "name X is already active" 错误：
1. 检查是否使用了大写字母 → 改为小写或添加前缀（如 `ptA`）
2. 检查是否使用了单字母 `e` → 改为 `pe`, `point_e` 等
3. 优先使用描述性的多字母名称

---

## 1. WellDefinedError: 类型系统污染

### 问题描述
当定理使用复杂的嵌套表达式作为目标公式时，可能导致后续定理出现WellDefinedError。

### 症状
```
Error: "obj unified::vec(p1, q1) is not in C"
Phase: verify_well_definedness (类型检查阶段)
```

### 根本原因
Litex的类型系统无法正确处理在目标公式中同时使用以下组合的表达式：
- 函数调用（如`vec(p, q)`）
- 索引操作（如`[1]`, `[2]`）
- 元组构造（如`(a, b)`）
- 算术运算（如`+`, `*`）

例如：
```litex
❌ 错误示例：
thm vec_add_path:
    ? forall p, q, r cart(R, R):
        vec(p, r) = (vec(p, q)[1] + vec(q, r)[1], vec(p, q)[2] + vec(q, r)[2])
```

这种复杂表达式会"污染"类型环境，导致后续定理中的简单表达式（如`vec(p1, q1)`）被错误判定为"不在类型集合C中"。

### 解决方案

**方案A：拆分为分量定理**（推荐）
```litex
✅ 正确示例：
thm vec_add_path_x:
    ? forall p, q, r cart(R, R):
        vec(p, r)[1] = vec(p, q)[1] + vec(q, r)[1]

thm vec_add_path_y:
    ? forall p, q, r cart(R, R):
        vec(p, r)[2] = vec(p, q)[2] + vec(q, r)[2]
```

**方案B：使用辅助函数**
如果库中有向量加法函数，可以使用：
```litex
thm vec_add_path:
    ? forall p, q, r cart(R, R):
        vec(p, r) = vec_add(vec(p, q), vec(q, r))
```

### 调试方法
1. **二分查找**：逐步注释定理，定位导致WellDefinedError的具体定理
2. **简化测试**：创建只包含必要定义和问题定理的最小测试文件
3. **类型检查**：优先检查目标公式的复杂度，而非变量名

### 案例研究
- **问题定理**：L478 `vec_add_path`
- **影响范围**：导致L500 `cosine_law`出现WellDefinedError
- **调查时间**：70+轮二分查找
- **解决方案**：拆分为`vec_add_path_x`和`vec_add_path_y`
- **验证结果**：WellDefinedError完全消失

---

## 2. 等式替换的局限性

### 问题描述
Litex不会自动进行等式两边的变量替换或复杂的代数变换。

### 症状
```
已知: a = 5, b = 10
已知: a + b = c
无法直接推导: c = 15
```

### 解决方案
- 每个推导步骤必须显式写出
- 使用已证明的定理进行替换
- 避免依赖"显而易见"的代数恒等式
- 若在复合函数项中直接重写或移项得到 `unknown result`，先对 `R` 上的标量变量证明通用代数引理；证明体用逐步等式链（如同加、同减、再除），再以复合函数项实例化该引理。此模式已由 `cosine_law` → `dot_from_cosine_law` 的 strict 验证确认。

### 特殊情况：函数上下文中的等式包装

**问题**：已知 `A = B`，想证明 `f(A) = f(B)`（如 `-A = -B` 或 `dot(vec(...), A) = dot(vec(...), B)`），直接跳跃会失败。

**症状**：
```litex
已知: (a-b)*(c-d) + (a'-b')*(c'-d') = -((b-a)*(c-d) + (b'-a')*(c'-d'))
目标: dot(vec(b,a), vec(c,d)) = -dot(vec(a,b), vec(c,d))
验证: verification failed  # 无法直接从坐标等式跳到函数包装
```

**解决方案**：需要两个显式桥接步骤
```litex
# Step 1: 左侧包装
coordinate_expr_left = -coordinate_expr_right
f(left_args) = -coordinate_expr_right       # 左侧替换

# Step 2: 右侧包装  
-coordinate_expr_right = -f(right_args)     # 右侧替换

# Step 3: 传递
f(left_args) = -f(right_args)
```

**案例**：`dot_neg_left` (KB L688-700)
- 需要3行而非1行：先包装左侧dot，再包装右侧dot，最后传递
- 已验证：添加两条中间等式后从axiom成功转换为theorem

---

## 3. 复杂表达式的证明策略

### 最佳实践
1. **分层证明**：将复杂定理拆分为多个简单的辅助定理
2. **避免嵌套**：目标公式保持简洁，使用多个定理代替单个复杂定理
3. **显式展开**：每个推导步骤都要完整写出，不能跳步

### 示例
```litex
# ❌ 不推荐：一次性证明复杂公式
thm complex_formula:
    ? forall x, y: f((g(x)[1] + h(y)[2], g(x)[2] - h(y)[1])) = result

# ✅ 推荐：拆分为多个简单定理
thm step1: ? forall x, y: temp1 = g(x)[1] + h(y)[2]
thm step2: ? forall x, y: temp2 = g(x)[2] - h(y)[1]
thm step3: ? forall x, y: f((temp1, temp2)) = result
```

---

## 4. Axiom vs Theorem

### 原则
- **禁止使用axiom逃避验证**
- Axiom仅用于以下情况：
  1. 真正的数学公理（如加法交换律）
  2. 基础定义的性质（如距离的非负性）
  3. 无法用litex表达的推理步骤（需明确标注原因）

### 验证
- Axiom在litex中是"直接给过"的（不进行验证）
- 所有可以证明的定理都应该使用`thm`而非`axiom`

---

## 5. 调试工具和技巧

### 二分查找法
当遇到WellDefinedError且不确定原因时：
1. 备份当前文件
2. 创建只包含前半部分定理的测试文件
3. 验证测试文件，确定问题在前半还是后半
4. 重复步骤2-3，直到定位到单个定理

### 最小复现
创建包含最少内容的测试文件：
- 只包含必要的定义（函数、类型）
- 只包含问题定理
- 验证问题是否复现

### 库文件局部排错命令
```bash
# 定位库文件中的错误，不等于题目模块的完整验收
litex -f your_library.lit > verify_result.txt 2>&1

grep "WellDefinedError" verify_result.txt
grep '"result": "error"' verify_result.txt | wc -l
```
题目模块的完整验收须按 `litex_problem_solving_workflow.md` 第 4 阶段执行，并检查全部导出及 JSON trace。

---

## 6. 经验总结

### Litex能做什么
✅ 简单的代数替换和展开  
✅ 基于定义的展开  
✅ 已证明定理的引用  
✅ 逐步推导（每步显式写出）  

### Litex不能做什么
❌ 复杂的代数变换（需要拆分为多个简单步骤）  
❌ 自动的等式两边替换  
❌ 处理复杂嵌套表达式作为目标公式  
❌ "显而易见"的推理（必须显式证明）  

### 核心原则
1. **保持简洁**：目标公式越简单越好
2. **逐步推导**：每一步都要显式写出
3. **分层构建**：用简单定理构建复杂定理
4. **避免嵌套**：函数调用、索引、元组构造不要同时使用

---

## 7. 极简证明策略：只用by thm调用

### 问题背景
在cosine_law证明中发现：即使拆分了定理（vec_add_path_x/y），如果在证明步骤中**显式写出中间等式**（特别是包含`vec()[1]`的tuple表达式），仍会触发WellDefinedError。

### 症状
```litex
❌ 触发WellDefinedError的写法：
by thm vec_neg(p1, q1)
vec(q1, p1) = (-(vec(p1, q1)[1]), -(vec(p1, q1)[2]))  # 显式写出结论
```

即使`by thm`调用的定理本身是正确的，显式写出的等式会被litex的预扫描器（pre-scanner）检查，导致WellDefinedError。

### 解决方案：极简证明策略

**✅ 只用by thm调用，不写显式等式：**
```litex
thm cosine_law:
    ? forall p1, q1, r1 cart(R, R):
        distance_sq(p1, r1) = distance_sq(p1, q1) + distance_sq(q1, r1) - 2 * dot(vec(q1, p1), vec(q1, r1))
    
    # 只调用定理，让litex自己推导
    by thm vec_dot_self_is_distance(p1, r1)
    by thm vec_add_path_x(p1, q1, r1)
    by thm vec_add_path_y(p1, q1, r1)
    by thm dot_square_sum(vec(p1, q1), vec(q1, r1))
    by thm vec_dot_self_is_distance(p1, q1)
    by thm vec_dot_self_is_distance(q1, r1)
    by thm vec_neg(p1, q1)
    
    # 最后写出目标结论
    distance_sq(p1, r1) = distance_sq(p1, q1) + distance_sq(q1, r1) - 2 * dot(vec(q1, p1), vec(q1, r1))
```

### 关键原则
1. **删除所有中间等式**：只保留`by thm`调用和最终目标结论
2. **信任litex的推导能力**：litex能从定理调用自动推导到目标结论
3. **避免手写tuple表达式**：任何包含`vec()[1]`的显式等式都会触发预扫描错误

### 案例研究
- **问题定理**：cosine_law（L516-541，27轮失败）
- **根本原因**：显式写出了包含`vec()[1]`的中间等式（L533-540）
- **解决方案**：删除所有显式等式，只保留9行`by thm`调用
- **验证结果**：✅ WellDefinedness通过！新错误是定理顺序问题

---

## 8. 定理顺序管理

### 问题描述
Litex按文件顺序从上到下验证定理。如果定理A引用定理B，但B在A之后定义，会导致"theorem not defined"错误。

### 症状
```
Error: "by thm: theorem `unified::vec_neg` is not defined"
Phase: verify_process (证明验证阶段)
```

注意：这个错误发生在**verify_process阶段**，而非verify_well_definedness阶段。这说明类型检查通过了，但定理引用失败。

### 解决方案
**检查依赖定理的位置，确保按依赖顺序排列：**

```litex
# ✅ 正确顺序：基础定理在前，依赖定理在后
L398:  thm dot_square_sum           # 基础定理
L479:  thm vec_add_path_x          # 基础定理
L491:  thm vec_add_path_y          # 基础定理
L504:  thm vec_dot_self_is_distance # 基础定理
L603:  thm vec_neg                 # 基础定理
L605:  thm cosine_law              # 依赖上述所有定理
L634:  thm dot_from_cosine_law     # 依赖cosine_law
```

### 连锁依赖问题
修复一个定理的顺序问题，可能暴露下游定理的顺序问题：

**案例：cosine_law的连锁反应**
1. **第一个顺序问题**：cosine_law(L516)在vec_neg(L634)之前
   - 解决：将cosine_law移动到L620
2. **第二个顺序问题**：dot_from_cosine_law(L517)在cosine_law(L620)之前
   - 解决：将dot_from_cosine_law移动到L634

### 调试技巧
1. **查找定理位置**：`grep -n "^thm XXX" file.lit`
2. **检查所有依赖**：列出定理中所有`by thm`调用的定理
3. **系统性移动**：移动定理时使用sed或脚本，避免手动编辑错误

---

## 9. 综合案例：cosine_law的完整修复历程

### 问题背景
cosine_law是余弦定理的向量形式，证明需要多个基础定理支持。

### 修复历程（27轮）

**Phase 1: WellDefinedError困境（Turn 1-4）**
- **问题**：证明中包含`vec()[1]`索引在tuple中
- **错误**：WellDefinedError
- **尝试**：用高层定理替换手写tuple → 失败

**Phase 2: 极简证明策略突破（Turn 5-8）**
- **策略**：删除所有显式等式，只保留`by thm`调用
- **结果**：✅ WellDefinedness通过！
- **新错误**：`theorem 'vec_neg' is not defined`

**Phase 3: 定理顺序问题1（Turn 9-15）**
- **发现**：cosine_law(L516)在vec_neg(L634)之前
- **解决**：将cosine_law移动到L620
- **结果**：✅ cosine_law验证通过！

**Phase 4: 连锁反应（Turn 16-24）**
- **新问题**：dot_from_cosine_law(L517)在cosine_law(L620)之前
- **解决**：将dot_from_cosine_law移动到L634
- **结果**：✅ 两个定理都验证通过！

### 关键经验
1. **极简证明策略**是绕过WellDefinedError的有效方法
2. **定理顺序管理**是litex验证的关键约束
3. **连锁依赖处理**需要系统性思考和验证

### 最终成果
```litex
thm cosine_law:  # L605-632，只用by thm调用
thm dot_from_cosine_law:  # L634-647，依赖cosine_law
```

---

## 10. 纯代数证明策略：midpoint定理案例

### 问题背景
两个中点定理（`midpoint_equidistant`和`midpoint_half_distance`）最初使用`by thm`桥接坐标展开式，导致证明链条断裂。

### 失败的混合策略
```litex
❌ 错误示例（by thm桥接）：
thm midpoint_half_distance:
    ? forall a, b, m cart(R, R):
        m[1] = (a[1] + b[1]) / 2, m[2] = (a[2] + b[2]) / 2
        =>: distance_sq(a, m) = distance_sq(a, b) / 4
    
    by thm distance_sq_coordinate_formula(a, m)  # ❌ 桥接断开代数链条
    m[1] - a[1] = (b[1] - a[1]) / 2
    # ... 代数推导 ...
    distance_sq(a, m) = distance_sq(a, b) / 4  # ❌ 失败："atomic fact unknown"
```

**失败原因**：
1. `by thm`引入知识后，litex无法将其应用到后续代数推导
2. 代数链条和函数形式之间存在gap
3. 最终结论直接断言函数等式，litex无法验证

### 成功的纯代数策略

**核心原则**：
1. **直接断言函数展开式**（不用`by thm`）
2. **完整代数链条**（每一步都是纯代数等式）
3. **显式子表达式替换**（litex不会自动替换）
4. **传递性连接结论**

**成功示例**：
```litex
✅ 正确示例（纯代数）：
thm midpoint_half_distance:
    ? forall a, b, m cart(R, R):
        m[1] = (a[1] + b[1]) / 2, m[2] = (a[2] + b[2]) / 2
        =>: distance_sq(a, m) = distance_sq(a, b) / 4
    
    # Step 1: 直接断言函数展开式（不用by thm）
    distance_sq(a, m) = (m[1] - a[1])^2 + (m[2] - a[2])^2
    distance_sq(a, b) = (b[1] - a[1])^2 + (b[2] - a[2])^2
    
    # Step 2: 纯代数替换链条
    (m[1] - a[1])^2 + (m[2] - a[2])^2 = ((a[1] + b[1]) / 2 - a[1])^2 + ((a[2] + b[2]) / 2 - a[2])^2
    ((a[1] + b[1]) / 2 - a[1])^2 + ... = ((b[1] - a[1]) / 2)^2 + ((b[2] - a[2]) / 2)^2
    ((b[1] - a[1]) / 2)^2 + ... = (b[1] - a[1])^2 / 4 + (b[2] - a[2])^2 / 4
    (b[1] - a[1])^2 / 4 + ... = ((b[1] - a[1])^2 + (b[2] - a[2])^2) / 4
    
    # Step 3: 显式子表达式替换（关键！）
    ((b[1] - a[1])^2 + (b[2] - a[2])^2) / 4 = distance_sq(a, b) / 4
    
    # Step 4: 传递性连接最终结论
    distance_sq(a, m) = distance_sq(a, b) / 4  # ✅ 通过！
```

### 关键技术点

**1. 显式子表达式替换**
Litex不会自动识别和替换等式中的子表达式。

❌ **错误假设**：
```
已知：distance_sq(a, b) = (b[1] - a[1])^2 + (b[2] - a[2])^2
推导到：((b[1] - a[1])^2 + (b[2] - a[2])^2) / 4
期望：litex自动知道这等于 distance_sq(a, b) / 4
```

✅ **正确做法**：
```litex
# 必须显式写出替换步骤
((b[1] - a[1])^2 + (b[2] - a[2])^2) / 4 = distance_sq(a, b) / 4
```

**2. 避免by thm桥接**
在纯代数证明中，`by thm`会断开传递性链条。

- ✅ 直接断言：`distance_sq(a, m) = (m[1] - a[1])^2 + ...`
- ❌ by thm桥接：`by thm distance_sq_coordinate_formula(a, m)`

**3. 传递性连接**
Litex的传递性推理非常强大，能自动连接等式链条：
```
A = B
B = C
C = D
---
A = D  # ✅ litex自动推导
```

但前提是整个链条都是同类型的等式（都是代数等式，或都是函数等式）。

### 成果统计
- **midpoint_equidistant**: ✅ 通过（L516-539）
- **midpoint_half_distance**: ✅ 通过（L541-565）
- **验证改进**：从196成功 → 229成功（+33个）

### 适用场景
纯代数证明策略适用于：
1. 坐标几何定理（涉及`[1]`, `[2]`索引）
2. 需要多步代数化简的证明
3. 函数形式和代数形式混合的证明

### 关键经验
1. **代数链条完整性**：每一步都必须是可验证的等式
2. **显式优于隐式**：litex不会自动应用子表达式替换
3. **传递性是核心**：保持等式链条连续，避免跳跃
4. **混合策略的边界**：`by thm`导入函数展开后，不能直接跳到函数结论；若最终连续等式链显式包含函数端点与完整标量中间式，则可混用。

---

## 11. 拆分 KB 的完整性审计

模块文件与某个本地“源文件”字节一致，只能证明复制无误，不能证明该源文件本身完整。若文件末尾停在新章节标题处，不要立即补写内容；先检查：

1. `litex.config` 的全部导出模块；
2. 疑似缺失的 `prop`、`have fn` 或 `thm` 实际定义在哪个模块；
3. 各文件声明清单与模块职责是否一致；
4. 从远端全新克隆后，使用仓库内依赖实际运行调用该 KB 的题目。

已验证案例中，`definitions.lit` 末尾的下一节标题是拆分残留，而对应的 `is_midpoint` 已在 `predicates.lit`，因此正确修复是清除误导标题并明确模块边界，而不是重复定义谓词。

---

## 12. 左乘常数等式的消元

已知 `2 * x = 2 * y` 时，不要先改写成 `x * 2 = y * 2` 再调用只匹配右乘形式的消元定理；Litex 可能无法验证这一步乘法交换。

已验证可用的连续等式链：
```litex
x = (2 * x) / 2 = (2 * y) / 2 = y
```

该写法利用传递性直接消去左乘常数，适合由距离公式先得到“二倍点积相等”的证明。

---

## 13. 坐标等式解元与仿射换向

Litex 不一定自动把 `d = a + c - b` 重排为 `c = d + b - a`。稳健做法是先建立同加后的中间式，再用等式同减定理并保持完整传递链：
```litex
d + b = (a + c - b) + b = a + c
(d + b) - a = (a + c) - a by thm geo::subtract_equalities(d + b, a + c, a, a)
c = (a + c) - a = (d + b) - a = d + b - a
```

仿射点需要从反方向使用时，也不要期待端点自动交换。先逐分量证明新参数形式，再展开定义并调用距离定理：
```litex
p[1] = (1 - u) * c[1] + u * b[1]
p[2] = (1 - u) * c[2] + u * b[2]
by def $geo::is_affine_combination(p, c, b, u)
by thm geo::affine_combination_distance_sq(c, b, p, u)
```

---

## 14. 定义型比例目标必须显式封装正实数见证

即使上下文已分别证明距离平方和比例等式，`by def` 也不会自动构造定义中的 `exist ... R+`。应显式给出所有正实数见证及定义体事实：
```litex
witness exist ab, cd R+ st {
    ab^2 = distance_sq(c, e),
    cd^2 = distance_sq(b, c),
    4 * ab = cd
} from side / 4, side:
    (side / 4)^2 = distance_sq(c, e)
    side^2 = distance_sq(b, c)
    4 * (side / 4) = side
```

见证表达式必须已能被内核判为 `R+`；优先从定义展开时取得的正长度见证构造。

见证体中的事实应按存在目标的表达式顺序显式给出：即使上下文已有 `x + y > z`，目标见证要求 `y + x > z` 时也可能不会自动用加法交换律完成实例化。应先写出交换等式及目标顺序的不等式，再提交 witness；该模式已由 `triangle_inequality` 的三距离见证严格验证。

---

## 15. 嵌套向量展开与正比例保序

若 `dot(vec(a,p), vec(d,p))` 不能直接展开，先分别声明两个 `vec` 等式及四个分量等式，再按 `dot` 定义连接分量乘积；仅把 `vec(a,a)` 整体替换为 `(0,0)` 也可能失败，改用坐标公式逐分量代入。

从 `0 < x` 推出正比例时，不要期待一步闭合。对正整数常数可显式暴露：
```litex
0 < 3
0 < 4
0 < 3 * x
0 < 3 * x / 4
```
再通过等式链把目标量连接到 `3*x/4`；`x/4` 同理。

---

## 16. 复杂平方等式的共同项消去与显式移项

把坐标距离平方完全展开后，若两侧都有同一共同项，先把表达式规范成 `A + C = B + C`，再调用 `addition_cancel(A, B, C)`；不要期待内核从不同结合顺序中自动识别共同项。

从 `A - X = B - Y` 构造目标差式时，可先用 `add_equalities` 对两边同加 `X`。但不要直接断言复合式 `(A - X) + X = A` 与其余替换同时完成；先用 `sub_add_cancel(A, X)` 建立该桥，再保持连续等式链。随后用 `subtract_equalities` 对两条已线性化等式作差，最后把分配律/结合律恒等式单独写成一步。

该模式已由 `power_of_point_difference` 的严格验证确认，适用于两组等距离平方展开后求线性式之差。

---

## 17. 函数定义展开与普通角等式约分

值函数不能写成独立证明指令 `by def f(args)`；该形式可触发 ParseError。需要展开时，直接写函数值等式，例如 `angle_cos_den(...) = distance_sq(...) * distance_sq(...)`，再用连续等式链连接。

处理共享 `are_angles_congruent` 的平方余弦等式时，不要过早把嵌套表达式展开成 `dot(vec(...),vec(...))`。先停留在 `angle_cos_num/angle_cos_den` 层：证明两分母的比例及非零性，消去共同分母；再结合谓词给出的分子同号条件，用标量选根引理由平方比例推出分子比例；最后才展开 `angle_cos_num` 为点积。该顺序已由 Problem 214 的源码与归档独立零错误验证。

---

## 18. 商消去与存在见证的具体表达式桥接

定义比例参数 `t = target / s` 后，不要期待内核同时展开局部定义并消去除法。先显式证明 `s != 0`，再建立规范式：
```litex
(target / s) * s = target
t * s = (target / s) * s = target
```
即把“商消去”和“代入 `t`”拆成两层；该模式已在 `s = sqrt(distance_sq(a,b))` 的点构造定理中严格验证。

对 `witness exist g ... from <concrete tuple>:`，即使证明体已经得到关于局部名 `g` 的函数等式，存在目标也可能不自动把它实例化到实际 tuple。应追加具体表达式桥：
```litex
distance_sq(g, b) = target^2
distance_sq(<concrete tuple>, b) = distance_sq(g, b) = target^2
```
这能让 witness 的目标事实直接匹配具体见证。该模式已由 `test_point_on_line_with_distance` 的主库验证确认。

---

## 19. AAS 复合代换与缩放同号桥
在 AAS 的平方余弦链中，已知反向边等式时，Litex 可能不会在乘积、幂或嵌套乘积中自动完成代换。应先把两侧规范成相同的复合 RHS，再逐步连接：
```litex
X * old_rhs = X * normalized_rhs
X * normalized_rhs = new_lhs * normalized_rhs
```
不要直接跳过复合项；该 RHS-to-RHS 桥模式已随 `triangle_congruence_AAS` 的主库严格验证确认。

对由谓词得到的 `u * v >= 0`，若目标是 `(2 * u) * (2 * v) >= 0`，不要依赖内核自动归一化双倍乘积。先显式推出 `4 * (u * v) >= 0`，再写出 `4 * (u * v) = (2 * u) * (2 * v)` 的代数恒等桥；该模式已在 AAS 主库完整回归中验证。

---

## 20. 中点对顶射线的方向校验与坐标分项

把中点处的“对顶角”写成点积前，必须逐条检查有向射线：若 `d` 是 `a,c` 的中点，则 `vec(d,a) = -vec(d,c)`；只反转这一条射线会使点积变号。正确的双反向形式可写为：
```litex
dot(vec(d, b), vec(d, a)) = dot(vec(d, c), vec(b, d))
```
不要写成右侧仍使用 `vec(d,b)` 的形式；该错误已被具体坐标反例检出。

展开 dot 后，若内核不能一次验证含两个坐标项的双负号乘积和，先分别证明 x、y 单项等式（将乘法交换及两个负因子拆成连续桥），再用 `add_equalities` 合并。该路径已在 `vertical_angles_dot_equal` 的目标前缀与完整主库验证中确认。

---

## 21. 共同因子提升与距离和的显式分配桥

从标量恒等式提升到距离平方时，先用 `multiply_both_sides` 乘共同因子（例如 `ux^2 + uy^2`），不要期待内核自动把因子分配到两项。合并多个距离闭式时，先用 `add_equalities` 得到两项之和，再单独写出分配律等式，最后用连续等式链连接目标；该模式已在 Problem 229 的完整审计中以 264 条记录、零错误验证。

---

## 22. 图示角等式的方向语义

公共无向角相等若只由余弦关系表达，会同时容纳正、负两个转角分支。原题文字借助“如图”明确选择同一转动方向，而该方向又会影响 SAS 等后续推导时，不能只保留无向角谓词，也不能把待证的目标夹角直接补成前提。

可复用的形式化方式是定义真正的有向角概念：保留公共无向角相等，并要求两角对应有向面积（行列式）的乘积非负，例如：
```litex
$geo::are_angles_congruent(p, q, r, u, v, w)
geo::det(geo::vec(q, p), geo::vec(q, r)) * geo::det(geo::vec(v, u), geo::vec(v, w)) >= 0
```
仅当原 NL/图示确实承载该同向信息时使用，并在题面边界说明方向信息来自哪里；该谓词属于可复用数学概念，可放入 translation，而题号专用的推导桥仍应留在 solution。

---

## 23. 同被减数等式的消去

已知 `c - x = c - y` 时，`subtraction_cancel` 不适用（它消去的是相同减数）。也不要先把两边乘 `-1` 再期待内核自动归一化。可定义并复用以下连续等式链：
```litex
thm cancel_same_minuend:
    ? forall c, x, y R:
        c - x = c - y
        =>:
            x = y
    x = c - (c - x)
    y = c - (c - y)
    c - (c - x) = c - (c - y)
    x = y
```
该模板已通过 fresh normal 与 full-dependency strict 验证。

---

## 24. IMO 2024 实战语法陷阱集锦

本章节记录在 IMO 1960 Problem 3 形式化过程中发现的 9 个关键语法错误，经过 34 轮调试验证。

### 24.1 模块命名空间问题

❌ **错误**：
```litex
import "../../Litex/geo_module" as geo
geo::is_right_angle(...)  # 错误：缺少 main:: 层级
```

✅ **正确**：
```litex
import "../../Litex/geo_module" as geo
geo::main::is_right_angle(...)  # 正确：完整命名空间
```

**原因**：当模块的 `litex.config` 导出格式为 `main = "./solution.lit"` 时，调用方必须使用 `module_alias::export_key::name` 的三层命名空间。

### 24.2 顶层 have 语句错误

❌ **错误**：
```litex
# 文件顶层
have x = 5  # 错误：have 只能在证明体内使用
```

✅ **正确**：
```litex
thm my_theorem:
    ? goal
    have x = 5  # 正确：have 在 thm 证明体内
    ...
```

**错误信息**：`name 'have' is already active in this scope and cannot be rebound`

### 24.3 prop 参数语法

❌ **错误**：
```litex
prop conditions(ptA: cart(R, R), a: R):  # 错误：使用冒号
    ...
```

✅ **正确**：
```litex
prop conditions(ptA, ptB cart(R, R), a, h R):  # 正确：逗号分隔，类型后置
    ...
```

**规则**：prop 参数使用逗号分隔，同类型变量放在一起，类型标注放在最后。

### 24.4 prop 内部约束连接

❌ **错误**：
```litex
prop conditions(...):
    ptA != ptB and ptB != ptC  # 错误：使用 and 关键字
```

✅ **正确**：
```litex
prop conditions(...):
    ptA != ptB
    ptB != ptC  # 正确：直接换行，无需 and
```

**规则**：prop 内部的多个约束直接换行书写，不使用 `and` 连接词。

### 24.5 prop 内部调用其他 prop

❌ **错误**：
```litex
prop statement(...):
    conditions(ptA, ptB, ...)  # 错误：缺少 $ 前缀
```

✅ **正确**：
```litex
prop statement(...):
    $conditions(ptA, ptB, ...)  # 正确：调用其他 prop 需要 $ 前缀
```

同样适用于 thm 的 forall 子句中调用 prop。

### 24.6 几何库函数：distance vs distance_sq

❌ **错误**：
```litex
geo::main::distance(ptA, ptB) = a  # 错误：库中没有 distance 函数
```

✅ **正确**：
```litex
geo::main::distance_sq(ptA, ptB) = a^2  # 正确：使用平方距离
```

**原因**：geo_module 库只提供 `distance_sq`（平方距离）函数，避免处理平方根。所有距离相关的等式都应该使用平方形式。

### 24.7 几何库谓词：altitude vs foot

❌ **错误**：
```litex
geo::main::is_altitude(ptH, ptA, ptB, ptC)  # 错误：库中没有 is_altitude
```

✅ **正确**：
```litex
geo::main::is_foot(ptH, ptC, ptA, ptB)  # 正确：使用 is_foot（垂足）
```

**语义**：`is_foot(h, p, a, b)` 表示 h 是从点 p 到线段 ab 的垂足。高度（altitude）的概念需要用垂足来表达。

### 24.8 除法和三角函数的非零约束

❌ **错误**：
```litex
prop statement(...):
    tan(alpha) = 4 * n * h / ((n * n - 1) * a)  # 缺少非零约束
```

✅ **正确**：
```litex
prop statement(alpha, n, h, a R):
    cos(alpha) != 0      # tan 定义域约束
    n * n - 1 != 0       # 分母非零约束
    a != 0               # 分母非零约束
    tan(alpha) = 4 * n * h / ((n * n - 1) * a)
```

**错误信息**：
- `tan(alpha) is not well defined` → 缺少 `cos(alpha) != 0`
- `divisor '(n * n - 1) * a' cannot be verified to be non-zero` → 缺少分母约束

**规则**：所有除法和三角函数都必须显式声明定义域/非零约束。库中带定义域的函数被谓词调用时同样适用：例如 `angle_cos_num/den(p, q, r)` 要先给出 `p != q` 与 `r != q`；若同一谓词调用第二个角，还要给出对应的 `u != v` 与 `w != v`。这类约束缺失会在全模块 `-strict` 预检中先于题目证明报错。

### 24.9 thm 证明体：trust 语法

❌ **错误**：
```litex
thm problem_1:
    ? forall x R: P(x) =>: Q(x)
    # 错误：空证明体或只有 trust 关键字
```

✅ **正确方案 A（信任声明）**：
```litex
thm problem_1:
    ? forall x R: P(x) =>: Q(x)
    trust $Q(x)  # 正确：trust + 结论事实
```

✅ **正确方案 B（完整证明）**：
```litex
thm problem_1:
    ? forall x R: P(x) =>: Q(x)
    # 实际的证明步骤
    have step1 = ...
    have step2 = ...
    $Q(x)
```

**规则**：
- `?` 标记的 thm 必须有证明体，不能只有 goal
- 如果暂时无法提供完整证明，使用 `trust <fact>` 声明信任该事实
- `trust` 后面必须跟具体的事实（通常是结论），不能单独使用

### 调试总结

这 9 个语法问题在 34 轮调试中依次解决，最常见的错误模式：
1. **命名空间层级错误**：忘记 `main::` 中间层
2. **类型约束遗漏**：除法/三角函数的定义域检查严格
3. **prop 调用前缀**：内部调用需要 `$` 标记
4. **库函数映射**：需要查阅库文档确认实际可用的函数名

**推荐调试流程**：
1. 遇到 "fact not defined" → 检查命名空间和库文档
2. 遇到 "not well defined" → 添加相关的非零/定义域约束
3. 遇到 "Unexpected token" → 检查 prop/thm 的参数和连接语法
4. 使用 `parse_litex_error.py` 工具递归提取完整错误链

---

## 版本历史
- 2026-09-12: 添加同被减数等式的双重减法消去模板
- 2026-09-07: 添加图示角等式的有向语义建模规则
- 2026-09-05: 添加共同因子提升与距离和显式分配桥模式
- 2026-09-04: 添加中点对顶射线方向校验与 dot 坐标分项合并模式
- 2026-09-04: 添加 AAS 复合 RHS 代换与双倍同号缩放桥模式
- 2026-09-21: 添加章节 24 "IMO 2024 实战语法陷阱集锦"（9个子章节：模块命名空间、变量命名、have限制、prop语法、约束连接、库函数映射、非零约束、thm证明体）
- 2026-09-03: 添加商消去分层与存在见证具体表达式桥接模式
- 2026-09-01: 添加函数定义展开限制与普通角平方余弦约分模式
- 2026-09-01: 添加复杂平方等式的共同项消去与显式移项模式
- 2026-09-01: 添加嵌套向量分量展开及正比例逐级保序模式
- 2026-09-01: 添加坐标解元、仿射换向及定义型比例的正实数见证模式
- 2026-08-31: 添加左乘常数等式的除法链消元模式
- 2026-08-29: 添加拆分 KB 的完整性审计规则
- 2026-08-28: 初始版本，记录vec_add_path导致WellDefinedError的案例
- 2026-08-28: 添加极简证明策略、定理顺序管理、cosine_law完整案例研究
- 2026-08-28: 添加纯代数证明策略和midpoint定理成功案例
