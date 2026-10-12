# Litex Solution 翻译规范

**基于 IMO 1960 Problem 3 调试过程的完整总结**

---

## 🎯 核心原则

### 1. 唯一几何库源文件：Litex/geo/library_final.lit

**规则**：
- 翻译自然语言题目时，唯一允许导入的几何库源文件是 IMO 下的 `Litex/geo/library_final.lit`；可直接使用的现成几何谓词只能来自该文件，不得取自其他库、同内容副本或硬链接别名。
- 如果该文件中已有对应谓词，必须使用；若没有，则在本题 `predicate.lit` 新建，不能换一个库寻找。
- 只有唯一库自身独立 `-strict` 预检失败且错误定位在库文件时，才允许修复 `library_final.lit`；库预检通过后，禁止因某道题的翻译或证明困难而改库，必须在本题文件中处理。
- 不要在主定理中直接展开为坐标表达式或代数等式；展开只在证明体中进行。
- Litex 的 `[import]` 指向模块目录；先检查目标模块的 `[export]` 是否指向上述源文件。如果配置不支持导入，报告阻塞，不能私自换用 `Litex/library_final_ref`。

**示例**：

❌ **错误做法**（直接展开）：
```litex
thm imo_1960_problem_3:
    ? forall A, B, C Point, bx, By, cx, cy, a R:
        # Right angle at A (直接展开)
        bx * cx + By * cy = 0,
        ...
```

✅ **正确做法**（使用库中的谓词）：
```litex
thm imo_1960_problem_3:
    ? forall A, B, C Point, bx, By, cx, cy, a R:
        # Right angle at A (使用库中的谓词)
        $geo::is_right_angle(A, B, C),
        ...
```

**查找库中谓词的方法**：
```bash
# 搜索关键词
cd <YOUR_WORK_DIR>/IMO
grep -n "prop is_right_angle" Litex/geo/library_final.lit
grep -n "prop distance" Litex/geo/library_final.lit
grep -n "prop collinear" Litex/geo/library_final.lit
```

---

## 📝 主定理的结构要求

### 标准结构

```litex
thm problem_name:
    # 量词部分：声明所有变量
    ? forall x, y, z R, A, B, C Point:
        # 前提部分：使用谓词（不展开）+ 逐句 NL 注释
        $geo::is_right_angle(A, B, C),    # Right angle at A
        $geo::distance_sq(B, C, a * a),   # BC² = a²
        ...
        =>:
            # 结论部分：使用谓词或表达式 + NL 注释
            result_expression                 # Natural language description
    
    # 证明部分：在这里展开谓词和推导
    # Step 1: Expand predicates
    ...
    # Step 2: ...
    ...
```

### 前提部分的要求

**规则**：
- **只使用谓词形式**，不展开为坐标或代数表达式
- **翻译时同步添加行尾 NL 注释**，每个前提条件、每个结论都在同一行行尾用 `#` 标注对应的自然语言描述
- **注释即翻译对照表**：翻译一句 NL，立即在同行标注原文或含义，避免事后补充时遗漏或不一致
- 如果库中没有对应谓词，创建新谓词放在 `predicate.lit` 中

### 充要条件且禁止整题包装时

当自然语言要求“当且仅当”，但接口契约禁止用 `conditions(...)`、`statement(...)` 或 criterion 一类整题包装谓词时，不要为了适配语法而改变题意，也不要把包装谓词放进主定理前提。将公开结论拆成两个直接定理：

- `..._necessity`：逐句、原样重复全部公共 NL 前提，再把等价式左侧作为一个带 NL 注释的直接前提，结论写右侧。
- `..._sufficiency`：逐句、原样重复同一组公共 NL 前提，再把右侧作为直接前提，结论写左侧。
- 两个方向都必须在 theorem header 中保留完整原子前提，不能用辅助 proposition 代替；辅助谓词或引理只可服务证明体，不能改变公开翻译接口。
- 分别对两个方向做项目级 ordinary 与 strict 验收，并在 trace 中确认两个 theorem identifier 都实际出现。

这是“不封装”契约下对 iff 的接口保持方式；如果允许包装，则可使用语法参考中的 universal equivalence wrapper 模式。

**示意**：
```litex
thm criterion_necessity:
    ? forall x S:
        $common_condition_1(x),  # NL common premise 1
        $common_condition_2(x),  # NL common premise 2
        $left(x)                 # NL left side
        =>:
            $right(x)            # NL right side

thm criterion_sufficiency:
    ? forall x S:
        $common_condition_1(x),  # NL common premise 1
        $common_condition_2(x),  # NL common premise 2
        $right(x)                # NL right side
        =>:
            $left(x)             # NL left side
```

**示例对比**：

❌ **错误**（前提中直接展开）：
```litex
thm imo_1960_problem_3:
    ? forall bx, By, cx, cy, a R:
        bx * cx + By * cy = 0,  # 直接展开的坐标表达式
        (bx - cx) * (bx - cx) + (By - cy) * (By - cy) = a * a,
        =>: ...
```

✅ **正确**（前提中使用谓词）：
```litex
thm imo_1960_problem_3:
    ? forall A, B, C Point, a R:
        $geo::is_right_angle(A, B, C),  # 使用库中的谓词
        $geo::distance_sq(B, C, a * a),
        =>: ...
```

### 证明部分的要求

**规则**：
- 在 proof body 中**可以展开**谓词
- 使用 `have` 语句引入坐标系和中间变量
- 添加清晰的注释说明每一步推导
- 使用 `by thm` 引用辅助定理

**示例**：
```litex
thm imo_1960_problem_3:
    ? forall A, B, C Point, a R:
        $geo::is_right_angle(A, B, C),
        =>: result
    
    # Proof: Introduce coordinate system
    have A = (0, 0), B = (bx, By), C = (cx, cy)
    
    # Expand is_right_angle predicate
    # From $geo::is_right_angle(A, B, C), we get:
    bx * cx + By * cy = 0
    
    # Continue proof...
    ...
```

---

## 🚫 常见错误和解决方案

### 错误 1：忽略 library_final.lit 中的谓词

**错误场景**（IMO 1960 Problem 3 的教训）：
- 用户问："我明明有直角谓词你为什么不用呢？"
- Agent 直接使用了 `bx * cx + By * cy = 0` 而不是 `$geo::is_right_angle(...)`

**原因**：
- Agent 没有先查阅 `library_final.lit`
- 直接将自然语言翻译成坐标表达式

**解决方案**：
1. **翻译前必须先读** `library_final.lit`
2. 搜索相关关键词（right angle, distance, collinear 等）
3. 如果找到对应谓词，**必须使用**谓词形式

### 错误 2：在主定理前提中使用展开形式

**错误代码**：
```litex
thm main_theorem:
    ? forall bx, By, cx, cy R:
        # 这是展开后的形式，不应该出现在前提中
        bx * bx + By * By = cx * cx + cy * cy,
        =>: ...
```

**正确做法**：
```litex
thm main_theorem:
    ? forall A, B, C Point:
        # 使用谓词描述几何关系
        $geo::equal_distance(O, A, O, B),
        =>: ...
```

### 错误 3：混淆"翻译"和"证明"的界限

**错误理解**：
- "翻译时就应该展开所有谓词"

**正确理解**：
- **翻译时**（主定理的前提和结论）：使用谓词形式
- **证明时**（proof body）：可以展开谓词

**类比**：
- 主定理 = 数学定理的陈述（应该清晰、抽象）
- 证明 = 定理的证明过程（可以具体、计算）

---

## 📐 几何题目的翻译流程

### Step 1: 读取自然语言题目

```json
{
  "problem": "In a given right triangle ABC, the hypotenuse BC, of length a, ..."
}
```

### Step 2: 查阅 library_final.lit

```bash
cd <YOUR_WORK_DIR>/IMO
grep -i "right" Litex/geo/library_final.lit
grep -i "triangle" Litex/geo/library_final.lit
grep -i "distance" Litex/geo/library_final.lit
```

**找到的谓词**：
```litex
prop is_right_angle(A, B, C Point): ...
prop distance_sq(A, B Point, d_sq R): ...
```

### Step 3: 使用谓词形式化前提

```litex
thm imo_1960_problem_3:
    ? forall A, B, C Point, a R:
        # Right triangle with right angle at A
        $geo::is_right_angle(A, B, C),
        # Hypotenuse BC has length a
        $geo::distance_sq(B, C, a * a),
        =>: ...
```

### Step 4: 在证明中展开和推导

```litex
    # Introduce coordinate system
    have A = (0, 0), B = (bx, By), C = (cx, cy)
    
    # Expand is_right_angle predicate
    bx * cx + By * cy = 0
    
    # Continue proof...
```

---

## 🎯 新创建谓词的要求

### 何时创建新谓词

- 库中没有对应的谓词
- 题目中反复出现的几何关系
- 可以提高主定理可读性的抽象

### 新谓词的放置位置

**规则**：
- 放在 `predicate.lit` 中
- 在 `litex.config` 中配置 `[export] predicate = "./predicate.lit"`
- 在 `solution.lit` 中使用 `$predicate::prop_name(...)` 引用

**示例**：

```litex
# predicate.lit
prop is_midpoint(M, A, B Point):
    ? forall mx, my, ax, ay, bx, by R:
        M = (mx, my), A = (ax, ay), B = (bx, by)
        =>:
            mx = (ax + bx) / 2,
            my = (ay + by) / 2

# litex.config
[export]
predicate = "./predicate.lit"

# solution.lit
thm main_theorem:
    ? forall M, A, B Point:
        $predicate::is_midpoint(M, A, B),
        =>: ...
```

---

## ✅ 最佳实践总结

### 翻译时的检查清单

- [ ] 已查阅 `library_final.lit`，确认是否有对应谓词
- [ ] 主定理的前提使用谓词形式（不展开）
- [ ] 每个前提都有清晰的注释说明自然语言含义
- [ ] 如需新谓词，已放在 `predicate.lit` 中
- [ ] 证明部分再展开谓词和进行推导

### 主定理的可读性要求

**目标**：
- 读主定理的前提和结论，应该能直接理解题目的自然语言含义
- 不需要看证明过程，就能知道在证明什么

**反例**：
```litex
# ❌ 看不懂这在证明什么几何定理
thm problem:
    ? forall x1, y1, x2, y2, x3, y3 R:
        x1 * x2 + y1 * y2 = 0,
        (x2 - x3)^2 + (y2 - y3)^2 = a^2,
        =>: ...
```

**正例**：
```litex
# ✅ 一眼看出是直角三角形的定理
thm problem:
    ? forall A, B, C Point, a R:
        $geo::is_right_angle(A, B, C),
        $geo::distance_sq(B, C, a * a),
        =>: ...
```

---

## 🎓 总结

1. **翻译前必须先查阅 library_final.lit**
2. **主定理前提使用谓词形式，不展开**
3. **证明部分可以展开谓词并进行推导**
4. **新谓词放在 predicate.lit 中**
5. **主定理应该具有良好的可读性**

**记住：翻译 ≠ 展开，翻译 = 使用谓词抽象表达几何关系。**

## 🔧 证明实现经验：显式桥定理

Litex 的代数推理较保守。对非平凡的等式变形、代入、缩放、展开或坐标计算，不要假设证明器会自动完成全部中间步骤；应创建接口清晰、参数顺序固定的辅助定理，并在 `theorem.lit` 中按功能组织，再由主证明通过 `by thm theorem::name(...)` 调用。

调用辅助定理前，逐字核对其 `forall` 参数的数量、顺序和类型。优先使用少量可复用引理，避免把题目专属的坐标展开直接写进主定理陈述。



---

## 🎯 核心规则：库定理形式精确匹配

**[EMPIRICAL - Problem 205]** - 使用 `by thm` 时，定理结论必须与库定理的形式完全一致。

### ⚠️ The Golden Rule

**当使用 `by thm` 时，你的定理结论必须与库定理的结论形式完全匹配。**

**示例：median_inequality_distance**

```litex
# ❌ 失败 - 库定理返回 exist，你写的是直接不等式
thm problem_205:
    ? forall a, b, c, d cart(R, R):
        $geom::unified::is_midpoint(d, b, c),
        not $geom::unified::is_collinear(a, b, c)
        =>:
            geom::unified::distance_sq(a, b) + geom::unified::distance_sq(a, c) 
            > 2 * geom::unified::distance_sq(a, d)
    by thm geom::unified::median_inequality_distance(a, b, c, d)
    # Error: "cannot prove then-clause"

# ✅ 成功 - 完全匹配库定理的 exist 形式
thm problem_205:
    ? forall a, b, c, d cart(R, R):
        $geom::unified::is_midpoint(d, b, c),
        not $geom::unified::is_collinear(a, b, c)
        =>:
            exist d_ab, d_ac, d_ad R st {
                d_ab >= 0, d_ac >= 0, d_ad >= 0,
                d_ab * d_ab = geom::unified::distance_sq(a, b),
                d_ac * d_ac = geom::unified::distance_sq(a, c),
                d_ad * d_ad = geom::unified::distance_sq(a, d),
                d_ab + d_ac > 2 * d_ad
            }
    by thm geom::unified::median_inequality_distance(a, b, c, d)
```

### 为什么重要

1. **库公理返回 exist**: 你的结论必须使用 exist
2. **直接不等式 ≠ exist 形式**: 即使数学上等价，litex 不会自动转换
3. **需要手动桥接**: 如果想要不同形式，必须手动证明（不能只依赖 by thm）

### 策略

1. **查库先行**: 查找库定理的**精确结论形式**
2. **完全匹配**: 完全复制 exist/forall/约束结构
3. **参数顺序也是形式的一部分**: 即使谓词在数学上对称，也不要假设 Litex 会自动交换线段端点或其他实参；先按已有事实/定理的参数顺序调用，确需换序时显式使用对称定理或展开定义证明
4. **命名空间**: 在 exist 块中使用 `geom::unified::` 前缀
5. **by thm 直达**: 只有在形式完全匹配时才使用 `by thm`
