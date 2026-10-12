# Litex Syntax Quick Reference
# Extracted from Manual.md L2169-2268 +实战经验
# Purpose: Fast lookup for common syntax patterns and pitfalls

## Critical Syntax Rules (from experience)

### ⚠️ Chained Equality Pitfall (IMO 1960 Problem 3)
**[EMPIRICAL - Problem 1 Redux] - Chained equality causes variable rebinding:**

```litex
❌ FAILS - Chained equality not supported:
have BC_sq R = (0 - 3) * (0 - 3) + (4 - 0) * (4 - 0) = 9 + 16 = 25
# Error: name `BC_sq` is already active in this scope and cannot be rebound

✅ WORKS - Single value definition:
have BC_sq R = 25

✅ WORKS - Stepwise calculation (if needed):
have BC_sq_calc R = (0 - 3) * (0 - 3) + (4 - 0) * (4 - 0)
have BC_sq_step1 R = 9 + 16
have BC_sq R = 25
```

**Key rules:**
1. **No equality chains**: `have x = a = b = c` is parsed as multiple bindings
2. **One value per statement**: Each `have` should define exactly one value
3. **Use comments for reasoning**: Document calculation steps in comments, not in code

### ⚠️ Verification Statement Pitfall (IMO 1960 Problem 3)
**[EMPIRICAL - Problem 1 Redux] - have check: fact can cause rebinding:**

```litex
❌ FAILS - Verification statement causes conflict:
have BC_sq R = 25
have a_sq R = 25
have BC_len_check: BC_sq = a_sq  # Error: BC_sq already active

✅ WORKS - Implicit equality through same values:
have BC_sq R = 25
have a_sq R = 25
# Litex automatically recognizes they are equal

✅ WORKS - Use comments to document equality:
have tan_alpha R = 18/25
have formula_result R = 18/25
# Both equal 18/25, proving the formula
```

**Key rules:**
1. **Avoid `have name: x = y`**: If x or y are already defined, may cause rebinding error
2. **Implicit verification**: Define both sides to the same value instead of explicit check
3. **Document with comments**: Use comments to explain why values are equal

### ⚠️ Reserved Variable Names (IMO 1960 Problem 3)
**[EMPIRICAL - Problem 1 Redux] - Single-letter capitals often reserved:**

```litex
❌ FAILS - Reserved variable names:
have C cart(R, R) = (0, 4)  # Error: name `C` is already active
have e R = 2.71828           # Error: `e` is a math constant

✅ WORKS - Use descriptive prefixes:
have ptC cart(R, R) = (0, 4)
have epsilon R = 0.01
```

**Known reserved names:**
- `e` - Mathematical constant (2.71828...)
- `C`, `A`, `B`, `D`, `E`, `Q` - Single-letter capitals (often reserved)
- `Z`, `N`, `Q`, `R` - Type names for integers, naturals, rationals, reals
- Type constructors and module names in scope

**Best practice:**
- Use descriptive names: `ptA`, `ptB`, `ptC` for points
- Avoid single-letter capitals: Use `pt_x` instead of `X`
- When in doubt, use longer names

**[EMPIRICAL - golitex 1.0.5-beta] - Extended reserved names:**
```litex
❌ FAILS - More reserved single-letter capitals:
have A cart(R, R, R) = (1, 0, 0)  # Error: A is reserved
have B cart(R, R, R) = (0, 1, 0)  # Error: B is reserved
have D cart(R, R, R) = (0, 0, 1)  # Error: D is reserved

✅ WORKS - Use lowercase or prefixes:
have a cart(R, R, R) = (1, 0, 0)
have b cart(R, R, R) = (0, 1, 0)
have d cart(R, R, R) = (0, 0, 1)
# OR
have ptA cart(R, R, R) = (1, 0, 0)
```

### Scope and variable naming

**[EMPIRICAL - verified during a multi-file geometry proof]:** A name already active in the current scope cannot be rebound. Avoid reusing active single-letter capitals, type names, module names, or earlier local names as new variables. When a name conflict occurs, read the complete error and rename the local variable descriptively; do not infer a broader syntax restriction from one collision.

For helper theorems, keep `forall` binders unique within their scope and make the call use the exact same parameter count, order, and types as the declaration.

### Module System & litex.config ⚠️
**[EMPIRICAL - Problem 228 Redux] - Module import is MANDATORY for geom::zero functions:**

```bash
# ❌ FAILS with "forall fact is not well defined"
$ litex -isolated -f problem.lit
# Error: geom::zero::distance_sq undefined

# ✅ Local debugging with proper litex.config (NOT whole-module acceptance)
$ litex -compact -f problem.lit  # Can stop before subsequent exports
# Final acceptance from the problem module directory:
$ litex -runner -r . -all -json > litex_verified.json
```

**litex.config structure:**
```toml
[hierarchy]
module

[import]
geom = "../../../Euclidean_Geometry"  # Relative path to geom module

[export]
solution = "./solution.lit"
```

**Critical rules:**
1. **Standalone vs nested hierarchy**: An ordinary `[hierarchy] module` must not sit beneath a parent module. A directory exported by a parent and carrying its own `litex.config` must use `[hierarchy] submodule`.
2. **Export everything**: In a normal module, all public `.lit` files and subdirs in the module folder MUST be listed in `[export]`.
3. **Normal-module import path**: If module alias `p` exports `main = "./solution.lit"`, consumers call public declarations as `p::main::name`; only flattened modules omit the export key (`p::name`).

**⚠️ 实战陷阱（IMO 2024）**：

**模块命名空间层级问题**
```litex
❌ 错误：
import "../../Litex/geo_module" as geo
geo::is_right_angle(...)         # 缺少 main:: 中间层

✅ 正确：
import "../../Litex/geo_module" as geo
geo::main::is_right_angle(...)   # 完整命名空间

说明：当模块的 litex.config 使用 `main = "./solution.lit"` 导出时，
调用方必须使用 module::main::function 三层命名空间。
```
4. **Use `-f` not `-isolated -f`**: -isolated mode ignores imports.
5. **"forall fact not well defined" often means**: Missing module imports, not syntax error.

**Nested self-contained submodule (empirically kernel-verified):**
```toml
# parent litex.config
[hierarchy]
module

[export]
main = "./solution.lit"
geo = "./geo"
```

```toml
# geo/litex.config
[hierarchy]
submodule

[export]
main = "./main.lit"
```

- Do **not** combine `[hierarchy] submodule` with `[module] flatten = true`; the verifier rejects that configuration.
- With the layout above, declarations exported from `geo/main.lit` are referenced from `solution.lit` as `geo::main::name` (or `$geo::main::predicate(...)`).

**Flattened module (empirically kernel-verified):**
```toml
[hierarchy]
module

[module]
flatten = true

[export]
main = "./main.lit"
```

- A flattened module must have exactly one public `.lit` export.
- If imported as `geo`, consumers write `geo::name` or `$geo::predicate(...)`, not `geo::main::name`.
- Verifier output may still display the internal path `geo::main::name`; this does not change source syntax.
- Extra split maintenance `.lit` files cannot remain in the public module root unexported. Keep them outside that root's public scan, for example under `.drafts/`, while `main.lit` remains the sole export.

---

### ⚠️ Axiom/Theorem Statement Syntax (golitex 1.0.5-beta)
**[EMPIRICAL - IMO 1966 P3] - Predicate calls require $ prefix in premises:**

```litex
❌ FAILS - Missing $ prefix on predicates:
axiom test:
    ? forall a, b cart(R, R):
        is_collinear(a, b)      # Error: expected comparison operator or `$prop`
        =>
        ...

✅ WORKS - Use $ prefix and =>: for implications:
axiom test:
    ? forall a, b cart(R, R):
        $is_collinear(a, b)     # ✓ Predicate with $
        =>:                      # ✓ Use =>: not =>
            ...
```

**Critical rules:**
1. **Predicate calls in premises need $ prefix**: `$is_regular(...)`, `$is_collinear(...)`
2. **Use `=>:` not `=>`**: When axiom/thm has premises followed by conclusion
3. **Conclusion must be single line**: Cannot span multiple lines
4. **Function definitions must be single line**: No multi-line tuple expressions
5. **`--` separator is NOT required**: Modern syntax allows direct transition from statement to proof strategy (e.g., `? forall ... =>: ...` directly followed by `by contra:` or other proof strategies)
6. **`by contra:` restrictions** (see litex_proof_guide.md for details):
   - Must be indented 4 spaces (inside theorem body, same level as `? forall`)
   - Must start with `? <goal>` that restates the conclusion
   - Body can ONLY contain direct equation/inequality chains and final `impossible`
   - CANNOT use `have`, `obtain`, `release`, `by def`, `by thm` in body

**Examples:**
```litex
# ✓ Axiom with predicate premises
axiom circumcenter_property:
    ? forall a, b, c, o cart(R, R, R):
        $is_regular_tetrahedron(a, b, c, d)
        $is_circumcenter(o, a, b, c, d)
        =>:
            dist_sq3d(o, a) = dist_sq3d(o, b)

# ✓ Theorem with proof
thm dist_symmetric:
    ? forall a, b cart(R, R, R):
        dist_sq3d(a, b) = dist_sq3d(b, a)
    dist_sq3d(a, b) = dot3d(vec3d(a, b), vec3d(a, b))
    dist_sq3d(b, a) = dot3d(vec3d(b, a), vec3d(b, a))
    (b(1) - a(1)) * (b(1) - a(1)) = (a(1) - b(1)) * (a(1) - b(1))

# ❌ FAILS - Multi-line function definition
have fn centroid4(a, b, c, d cart(R, R, R)) cart(R, R, R) = (
    (a(1) + b(1) + c(1) + d(1)) / 4,
    (a(2) + b(2) + c(2) + d(2)) / 4
)

# ✓ WORKS - Single line
have fn centroid4(a, b, c, d cart(R, R, R)) cart(R, R, R) = ((a(1) + b(1) + c(1) + d(1)) / 4, (a(2) + b(2) + c(2) + d(2)) / 4, (a(3) + b(3) + c(3) + d(3)) / 4)

# ❌ FAILS - Multi-line conclusion
thm test:
    ? forall ...
        =>:
            expr1 + expr2 <
            expr3 + expr4

# ✓ WORKS - Single line conclusion
thm test:
    ? forall ...
        =>:
            expr1 + expr2 < expr3 + expr4
```

---

### -strict Mode Requirements ⚠️
**[EMPIRICAL - Problem 228 Strict] - Strict mode rejects axiom-based imports:**

```bash
# ❌ FAILS: geom library has axioms
$ litex -strict -f solution.lit  
# Error: "strict mode rejects user axiom statements"

# ✅ WORKS: Self-contained with local definitions
$ litex -strict -f solution_strict.lit
```

**Strict mode constraints:**
1. **No axiom dependencies**: All imported modules must be fully proven (no `axiom` statements)
2. **Explicit return types**: Function definitions MUST have return types
   ```litex
   ❌ have fn vec(A, B cart(R, R)) = (B[1] - A[1], B[2] - A[2])
   ✅ have fn vec(A, B cart(R, R)) cart(R, R) = (B[1] - A[1], B[2] - A[2])
   ```
3. **Self-contained proofs**: Define all helper functions locally to avoid axiom imports

**When to use -strict:**
- ❌ Daily proof work (use `-f` mode instead, trust standard libraries)
- ✅ Foundational library development (verify from first principles)
- ✅ Demonstrating complete verification without axioms

**Workaround for geom imports:**
Create self-contained versions by defining vec/dot/distance_sq locally:
```litex
have fn vec(A, B cart(R, R)) cart(R, R) = (B[1] - A[1], B[2] - A[2])
have fn dot(u, v cart(R, R)) R = u[1] * v[1] + u[2] * v[2]
have fn distance_sq(A, B cart(R, R)) R = dot(vec(A, B), vec(A, B))
```

---

### exist Statement Syntax ⚠️
**[EMPIRICAL - Problem 205 Redux] - exist MUST be single-line:**

```litex
❌ FAILS - Multi-line exist not supported:
exist d_ab, d_ac R st {
    d_ab >= 0,
    d_ac >= 0,
    d_ab * d_ab = distance_sq(a, b)
}

✅ WORKS - Single-line exist:
exist d_ab, d_ac R st {d_ab >= 0, d_ac >= 0, d_ab * d_ab = geom::unified::distance_sq(a, b)}
```

**Key rules:**
1. **Single line only**: All constraints in `{...}` must be on one line
2. **Comma-separated**: Use `,` between constraints
3. **Full namespace**: Functions need `geom::unified::` prefix
4. **No $ prefix**: Functions don't use `$` (only predicates do)

### Theorem application argument layout ⚠️
**[EMPIRICAL - orthocenter_third_altitude] - Long `by thm` argument lists must stay on one line:**

A multiline argument layout can produce a `ParseError` before proof checking. Keep the complete application on one line, even when the following equality chain is multiline:
```litex
❌ FAILS:
by thm subtract_equalities(
    lhs2, rhs2,
    lhs1, rhs1
)

✅ WORKS:
by thm subtract_equalities(lhs2, rhs2, lhs1, rhs1)
```

---

### Forall Constraint Syntax ⚠️
**[EMPIRICAL - Problem 228, 205 Redux] - forall body restrictions:**

```litex
✅ ALLOWED:
? forall a, b cart(R, R):
    $defs::is_midpoint(c, a, b)    # Predicate calls
    a != b                           # Inequalities
    a $in S                          # Membership
    =>: goal

❌ NOT ALLOWED - Coordinate component constraints (VERIFIED):
? forall e cart(R, R):
    e[1] = 2 * d[1] - a[1]          # ❌ Error: "name `e` is already active and cannot be rebound"
    e[2] = 2 * d[2] - a[2]          # Even in axiom! Litex treats coord constraints as rebinding

? forall a cart(R, R):
    a[1] = 0                        # ❌ Bare equality (rejected in practice)
    a = [0, 0]                      # ❌ Direct assignment
```

**Root cause (Problem 205):** Litex interprets coordinate equality constraints in forall premises as attempting to rebind the parameter, even for axioms. This makes "construct point E satisfying e[1]=..." patterns impossible.

**Workaround:** 
1. Define predicates or use `let` instead of `forall`
2. For geometric constructions needing coord constraints, keep as axiom without trying to add constraints
3. Or pass constructed point as additional forall parameter with constraints in conclusion

**Note:** Not explicitly documented in Manual - based on Problem 228, 205 debugging.

---

## Operator Precedence

```
^  >  (* /)  >  (+ -)
```

**Examples:**
- `a + b * c^2` = `a + (b * (c^2))`
- `a / b * c` = `(a / b) * c` (left-to-right)

---

## Binder Syntax (Parameter Declaration)

| Form | Meaning | Example |
|------|---------|---------|
| `x S` | x in set S | `x R` |
| `S set` | S is a set | `S set` |
| `S nonempty_set` | S is nonempty | `S nonempty_set` |
| `S finite_set` | S is finite | `S finite_set` |
| `x, y R` | Multiple in same domain | `a, b, c cart(R, R)` |
| `x R: x != 0` | Domain with condition | `x R: x > 0` |

---

## Common Object Syntax

### Arithmetic
```litex
a + b, a - b, a * b, a / b, a ^ b, a % b
abs(x), sqrt(x), min(a, b), max(a, b)
floor(x), ceil(x), sign(x), factorial(n)
exp(x), ln(x), log(base, x)
gcd(a, b), lcm(a, b)
```

### Sets
```litex
{1, 2, 3}                      # Display
{x R: x > 0}                   # Builder (comprehension)
union(A, B)                     # A ∪ B
intersect(A, B)                 # A ∩ B
diff(A, B)                      # A \ B
cart(A, B)                      # A × B (Cartesian product)
powerset(S)                     # 𝒫(S)

# Standard sets
N, Z, Q, R, C                   # Number sets
N+, Z+, Q+, R+                  # Positive
Z-, Q-, R-                      # Negative
Z*, Q*, R*, C*                  # Nonzero
```

### Functions
```litex
fn f(x R) R = x^2              # Named function
fn(x R) R: x^2                 # Anonymous
f(3)                            # Application
fn_range(f, S)                  # Image of S under f
```

### Structured Data
```litex
cart(R, R)                      # R²
[1, 2]                          # Tuple/point
a[1], a[2]                      # Index access (1-based!)
proj(1, p)                      # First coordinate
```

---

## Common Fact Syntax

### Atomic Facts
```litex
a = b                           # Equality
a < b, a <= b, a > b, a >= b   # Order
a != b                          # Inequality
a $in S                         # Membership
A $subset B                     # Subset ⊆
A $proper_subset B              # Proper subset ⊂
```

### Compound Facts
```litex
fact1 and fact2                 # Conjunction
a < b < c                       # Chain (auto-expands to a<b and b<c)
fact1 or fact2                  # Disjunction
```

**[EMPIRICAL - current Litex binary]:** When a disjunction is one fact (for example, a theorem conclusion, a `by cases` target, or a branch's concluding fact), keep the complete `p or q or r` expression on one physical line. Starting a continuation line with `or` was rejected with `Expected operator or $prop in fact`; the single-line forms passed ordinary and strict verification.

### Quantifiers
```litex
exist x S st { fact1, fact2 }   # Existential
exist! x S st { ... }           # Unique existence
forall x S: cond =>: goal       # Universal
not exist x S st { ... }        # Negated exist
not forall x S: ...             # Negated forall
```

---

## Common Statement Syntax

### Definitions
```litex
let x = value                   # Local binding
def pred(x S, y T) = fact       # Predicate definition (deprecated)
def fn f(x S) T = expr          # Function definition
```

**⚠️ 实战陷阱（IMO 2024）**：

1. **prop 参数语法（多参数同类型）**
   ```litex
   ❌ 错误：
   prop name(a: R, b: R, c: R):  # Python 风格参数声明
       ...
   
   ✅ 正确：
   prop name(a, b, c R):         # Litex 风格：逗号分隔，类型在最后
       ...
   
   ✅ 混合类型：
   prop name(p, q cart(R,R), a, b R):  # 同类型参数分组
       ...
   ```

2. **prop 内部约束连接**
   ```litex
   ❌ 错误：
   prop conditions(x, y R):
       x > 0 and y > 0 and x + y = 1  # 错误：不能用 and 连接多个约束
   
   ✅ 正确：
   prop conditions(x, y R):
       x > 0                           # 直接换行
       y > 0                           # 每行一个约束
       x + y = 1                       # 自动视为 and 连接
   ```

3. **prop 内部调用其他 prop**
   ```litex
   prop statement(x R):
       other_prop(x)                   # ❌ 错误：缺少 $ 前缀
       $other_prop(x)                  # ✅ 正确：调用 prop 需要 $
   ```

### Assertions
```litex
have fact                       # Assert and add to context
have name: fact                 # Named assertion
```

**⚠️ 实战陷阱（IMO 2024）**：

**have 语句只能在 thm 证明体内使用，不能在顶层**
```litex
❌ 错误：
import "geo_module" as geo

have pi > 0                     # 错误：顶层 have 语句不允许

prop conditions(x R):
    ...

✅ 正确：
import "geo_module" as geo

prop conditions(x R):           # 顶层只能有 import/prop/thm
    ...

thm example:
    ? forall x R: ...
    have pi > 0                 # 正确：have 在 thm 证明体内
    ...
```

### Proofs
```litex
witness exist x S st {...} from value:
    # Prove body facts

obtain x from exist_fact:
    # Use x in following proofs

by cases:
    case cond1: ...
    case cond2: ...

by contra:
    ? goal_fact
    # The negation of goal_fact is installed in this scope
    impossible contradiction_fact

claim name: fact:
    # Nested proof
```

### Proof Syntax Verification Discipline

**[EMPIRICAL - current Litex binary]:** Keep these three layers separate:

1. **Reference shorthand** describes the intended construct, but may omit required proof-block lines.
2. **Parser acceptance** only proves that the source has valid syntax.
3. **Verifier capability** determines whether that valid construct can prove the particular goal.

For any uncertain proof construct:

1. Look here first; use full repository examples only when this reference omits the complete structure.
2. Build a minimal probe of at most about 10 lines that tests one new construct only.
3. Confirm parsing, then ordinary verification, then strict verification with the current binary.
4. Do not infer a general grammar rule from one error; vary only the disputed form when diagnosing it.
5. Use a construct in the full proof only after the same structural form has passed the current binary.

**Verified boundaries:**

- `by contra:` requires an explicit indented `? goal_fact` block before its proof body.
- The current verifier cannot build the logical negation of a three-term disjunction such as `p or q or r` for `by contra`; use `by cases` or another constructive route.
- In a contradiction body, prefer `impossible contradiction_fact` where that single fact directly conflicts with a fact already in context. The attempted form `impossible (fact1) and (fact2)` failed to parse; that single failure does not establish a general grammar rule for every conjunction form.
- For a conditional universal bridge, use the verified `claim: ? forall ... =>:` proof block. Do not invent an `arbitrary` proof form: in the current binary, the attempted conditional `arbitrary` form without an exact `st {...}` body failed, while the anonymous-`forall` claim passed strict verification.
- Keep long `by thm` calls with many arguments on one physical line when the surrounding parser rejects their multiline form. This is a parser-boundary workaround verified on the current binary, not a mathematical requirement.

### Theorem Declaration
```litex
thm name:
    ? goal_fact
    # proof body

thm name:
    ? forall params: assumptions =>: conclusion
    # proof body
```

**⚠️ 实战陷阱（IMO 2024）**：

1. **thm 必须有证明体**
   ```litex
   ❌ 错误：
   thm problem:
       ? forall x R: P(x) =>: Q(x)
       # 空证明体 - 会导致 "Unexpected end of tokens"
   
   ✅ 正确（信任声明）：
   thm problem:
       ? forall x R: P(x) =>: Q(x)
       trust $Q(x)  # 使用 trust 声明信任结论
   
   ✅ 正确（完整证明）：
   thm problem:
       ? forall x R: P(x) =>: Q(x)
       have step1 = ...
       $Q(x)
   ```

2. **thm 中调用 prop 需要 $ 前缀**
   ```litex
   ❌ 错误：
   thm problem:
       ? forall x R:
           conditions(x) =>: statement(x)  # 缺少 $ 前缀
   
   ✅ 正确：
   thm problem:
       ? forall x R:
           $conditions(x) =>: $statement(x)  # 调用 prop 需要 $
   ```

3. **注意 =>: 的冒号位置**
   ```litex
   ❌ 错误：assumptions => conclusion
   ✅ 正确：assumptions =>: conclusion
   ```

### Universal equivalence wrapper (empirically strict-verified)

A theorem target cannot directly use a `forall ... <=> ...` body: the theorem parser accepts an ordinary universal implication, not a universal iff. Preserve the full equivalence by defining one proposition with both implication clauses, proving each complete clause as a scoped anonymous-`forall` claim, then unfolding the proposition:

```litex
prop criterion(x S):
    forall:
        $left(x)
        =>:
            $right(x)
    forall:
        $right(x)
        =>:
            $left(x)

thm criterion_theorem:
    ? forall x S:
        assumptions(x)
        =>:
            $criterion(x)
    claim:
        ? forall:
            $left(x)
            =>:
                $right(x)
        by thm left_implies_right(x)
    claim:
        ? forall:
            $right(x)
            =>:
                $left(x)
        by thm right_implies_left(x)
    by def:
        ? $criterion(x)
```

Do not merely invoke the two direction theorems sequentially in the outer proof: the antecedent of each definition clause is not automatically in that outer scope. The anonymous-`forall` claims establish the complete implication facts needed by `by def`. This pattern passed isolated/full strict verification without trust or axioms.

---

## Delimiters

| Symbol | Meaning |
|--------|---------|
| `[]` | Index access |
| `()` | Function call, grouping |
| `{}` | Set display or builder |
| `st { ... }` | Existential body |
| `#` | Line comment |
| Indentation | Block structure |

---

## Unicode Aliases (preview)

```litex
∀ = forall        ∃ = exist        ∃! = exist!
→ = =>            ↔ = <=>
∧ = and           ∨ = or           ¬ = not
∈ = $in           ∉ = not ... $in
⊆ = $subset       ⊂ = $proper_subset
∪ = union         ∩ = intersect    × = cart
ℕ = N    ℤ = Z    ℚ = Q    ℝ = R    ℂ = C
π = pi            ∅ = {}
```

---

## Common Pitfalls

### 1. Indexing is 1-based
```litex
a = [3, 4]
a[1]  # = 3 (first element)
a[2]  # = 4 (second element)
```

### 2. Function call vs set display
```litex
f(x)     # Function application
{x}      # Singleton set
```

### 3. Multiplication operator required
```litex
2x       # ❌ Error
2 * x    # ✅ Correct
```

### 4. Set builder restrictions
```litex
# Only atomic facts or simple boolean combinations
{x R: x > 0 and x < 10}          # ✅ OK
{x R: forall y R: x > y}         # ❌ Nested quantifier not allowed
```

### 5. Existential body restrictions (same as set builder)
```litex
exist x R st { x > 0, x < 10 }   # ✅ OK
exist x R st { exist y R st {...} }  # ❌ Nested quantifier
```

---

## Well-Definedness Requirements

### Division
```litex
a / b    # Requires: b != 0
```

**⚠️ 实战陷阱（IMO 2024）**：

**除法和三角函数需要显式声明非零约束**
```litex
❌ 错误（缺少约束）：
prop statement(alpha, n, a R):
    tan(alpha) = ...                    # 错误：tan 需要 cos(alpha) != 0
    ... / (n * n - 1) = ...             # 错误：分母需要非零
    ... / a = ...                       # 错误：a 需要非零

✅ 正确（显式约束）：
prop statement(alpha, n, a R):
    cos(alpha) != 0                     # tan 的定义域约束
    n * n - 1 != 0                      # 等价于 n != 1 and n != -1
    a != 0                              # 除数非零约束
    tan(alpha) = ...
    ... / (n * n - 1) = ...
    ... / a = ...

说明：
- tan(x) 需要 cos(x) != 0
- 所有除法 a/b 需要 b != 0（包括复杂分母表达式）
- Litex 不会自动推断定义域，必须显式声明
```

### Square Root
```litex
sqrt(x)  # Requires: x >= 0
```

**Ordered-conclusion pattern**: When a theorem declares `sqrt(t)` in one conclusion but `t >= 0` can be derived, list the domain certificate as the first conclusion:

```litex
thm main:
    ? forall ...:
        assumptions
        =>:
            t >= 0           # First: well-definedness certificate
            y = sqrt(t)      # Second: original conclusion using sqrt
    ... proof derives both in order
```

Litex processes conclusions under the same `=>:` sequentially; the first establishes the domain for the second.

### Logarithm
```litex
ln(x)    # Requires: x > 0
log(b, x)  # Requires: b > 0, b != 1, x > 0
```

### Trigonometry
```litex
sin(x), cos(x), tan(x), cot(x)
arcsin(x), arccos(x), arctan(x)
```

**Well-definedness requirements**: See Manual L900+ for complete rules.  
Known from Manual: `arcsin(x)` and `arccos(x)` require `-1 <= x <= 1`.

---

## Quick Lookup: "How do I write X?"

**Define a predicate:**
```litex
def is_midpoint(m cart(R,R), a cart(R,R), b cart(R,R)) =
    m = [(a[1] + b[1]) / 2, (a[2] + b[2]) / 2]
```

**Prove existence:**
```litex
witness exist x R st { x > 0, x^2 = 4 } from 2:
    have 2 > 0
    have 2^2 = 4
```

**Use an existential:**
```litex
obtain m from exist_fact:
    # Now m is available
    have m > 0
```

**Case analysis:**
```litex
by cases:
    case x >= 0:
        # proof for x >= 0
    case x < 0:
        # proof for x < 0
```

**Proof by contradiction:**
```litex
by contra:
    ? goal_fact
    # The negation of goal_fact is available in this scope
    have contradiction_fact
    impossible contradiction_fact
```

For a three-term disjunction goal, do not use `by contra` with the current verifier; split into supported cases instead.

---

## For Complete Reference

- **Full object syntax** (72 forms): Manual.md L2188-2198
- **Full fact syntax** (52 forms): Manual.md L2199-2208
- **Full statement syntax** (64 forms): Manual.md L2209-2217
- **Builtin verification rules**: Manual.md L2700+


---

## Appendix: Builtin Verification Skills

*Extracted from Manual.md - Concrete mathematical patterns litex recognizes automatically*

### Algebraic Simplification Patterns

**Polynomial Identity Recognition**
```litex
# Litex recognizes these automatically:
(a + b)^2 = a^2 + 2*a*b + b^2
(a - b)^2 = a^2 - 2*a*b + b^2
(a + b) * (a - b) = a^2 - b^2
```

**Absolute Value**
```litex
# Automatic rules:
abs(x * y) = abs(x) * abs(y)
0 <= abs(x)
x <= abs(x)
-x <= abs(x)
-abs(x) <= x
abs(x + y) <= abs(x) + abs(y)
abs(x - y) <= abs(x) + abs(y)
abs(x) - abs(y) <= abs(x - y)

# With nonzero premise:
forall x R: x != 0 =>: 0 < abs(x)

# Sign-based selection:
forall x R:
    x >= 0 => abs(x) = x
    x <= 0 => abs(x) = -x
```

### Nonzero Closure

```litex
# Automatic closure:
forall a, b R:
    a != 0
    b != 0
    =>:
        a * b != 0
        a / b != 0  # Also checks b != 0 for well-definedness
```

**Note**: Division requires denominator nonzero for well-definedness AND for quotient nonzero.

### Order Combination

**Addition Order**
```litex
# weak + weak = weak
a <= b, c <= d  =>  a + c <= b + d

# strict + strict = strict
a < b, c < d  =>  a + c < b + d

# weak + strict = strict
a <= b, c < d  =>  a + c < b + d
a < b, c <= d  =>  a + c < b + d

# Nonnegative summands:
forall a, b, c, d R:
    a <= b, c >= 0, d >= 0 =>: a + c + d <= b + c + d
```

**Multiplication Order**
```litex
# Both sides nonnegative:
a >= 0, b >= 0, c >= 0, d >= 0, a <= b, c <= d  =>  a*c <= b*d

# Strict multiplication (at least one strict):
a >= 0, b >= 0, c > 0, d > 0, a < b, c <= d  =>  a*c < b*d
a >= 0, b >= 0, c >= 0, d >= 0, a < b, c < d  =>  a*c < b*d
```

### Inequality Chains

```litex
# Transitivity:
a < b, b < c  =>  a < c
a <= b, b <= c  =>  a <= c
a < b, b <= c  =>  a < c
a <= b, b < c  =>  a < c
```

### Square and Power Rules

```litex
# Square nonnegative:
forall x R: 0 <= x^2

# Square sum:
forall a, b R: 0 < a^2 + b^2  IF  (a != 0  OR  b != 0)

# Strict positivity:
forall x R: x != 0 =>: 0 < x^2
```

### Triangle Inequality

```litex
# Euclidean norm:
forall x, y R: abs(x + y) <= abs(x) + abs(y)
forall x, y R: abs(abs(x) - abs(y)) <= abs(x - y)
```

### AM-GM Inequality (Built-in for n=2)

```litex
# Two nonnegative numbers:
forall a, b R:
    a >= 0, b >= 0 =>: sqrt(a * b) <= (a + b) / 2

# Equality condition:
forall a, b R:
    a >= 0, b >= 0, sqrt(a * b) = (a + b) / 2 =>: a = b
```

### Division and Reciprocal

```litex
# Sign preservation:
forall a, b R:
    a > 0, b > 0 =>: a / b > 0
    a < 0, b > 0 =>: a / b < 0

# Order reversal (reciprocal):
forall a, b R:
    0 < a, a < b =>: 1/b < 1/a
    0 < a, a <= b =>: 1/b <= 1/a
```

### Sqrt Rules

```litex
# Domain:
forall x R: sqrt(x) defined  =>  x >= 0

# Nonzero:
forall x R: sqrt(x) != 0  <=>  x > 0

# Monotonicity:
forall a, b R:
    0 <= a, a <= b =>: sqrt(a) <= sqrt(b)
    0 <= a, a < b =>: sqrt(a) < sqrt(b)
```

### Well-Definedness Checks

**Division**: `a / b` requires `b != 0`

**Sqrt**: 
- `sqrt(t)` requires `t >= 0`
- `sqrt(t) != 0` requires `t > 0`

**Trigonometric**:
- `tan(x)`, `sec(x)` require `cos(x) != 0`
- `cot(x)`, `csc(x)` require `sin(x) != 0`
- `arcsin(x)`, `arccos(x)` require `-1 <= x <= 1`

**Set operations**:
- `finite_set_size(S)` requires `$is_finite_set(S)`

---

**Usage Notes**:
- These patterns work automatically in equality chains and inequality derivations
- For complex cases, state intermediate facts explicitly rather than expecting multi-step chaining
- Check `litex_proof_guide.md` for verification order and strategy selection
