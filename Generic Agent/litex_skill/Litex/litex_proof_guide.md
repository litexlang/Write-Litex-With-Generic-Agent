# Litex Proof Guide

**Purpose**: Unified proof writing reference combining core mechanisms, decision rules, and patterns  
**Replaces**: litex_proof_writing_sop.md + litex_proof_decision_rules.md

---

## Core Verification Mechanism

Litex verifies theorems through **equality substitution**, NOT algebraic manipulation.

### What Works ✅
1. **Direct extraction from A-B=0**: `A - B = 0` → write `A = B` (OK)
2. **Equality substitution**: Replace subexpressions using known equalities
3. **Polynomial expansion/simplification**: Auto-handled by litex
4. **Add-and-subtract technique**: `C = C + A - A` to construct needed form

### Nested Substitution Boundary
When a known equality changes a variable inside a larger expression, do not expect strict verification to recurse through the entire expression automatically. Use an explicit atomic chain:

1. Derive the same-shape structural equality first, including each coordinate or component when the expression is coordinate-based.
2. Substitute that equality into the outer expression as a separate fact.
3. Normalize the resulting expression with a final pure polynomial/rational equality step.

Split mixed structural substitution and algebraic normalization into separate bridge facts. This makes the verifier's equality-matching boundary explicit and keeps each proof step independently checkable.

### What Fails ❌
1. **Mid-proof extraction**: `f(x)-g(x)=0` → `f(x)=g(x)` then use (NO)
2. **Basic rearrangement**: `A+B=0` → `A=-B` (NO)
3. **Factorization**: `a²-b²=(a-b)(a+b)` (NO)
4. **Reverse factorization**: Regrouping sum into products (NO)

---

## Verification Order (Critical!)

Litex tries these routes **in sequence**:
1. Reuse already known fact (includes equality transport)
2. Evaluate closed expression directly
3. Try bounded builtin mathematical rule
4. Try applicable `forall` fact
5. Try concrete definition
6. Try registered predicate property
7. Try enabled user strategy

**IMPLICATION**: 
- If step N fails, DON'T expect litex to chain multiple rules
- Expose 1-2 intermediate facts to bridge the gap
- For polynomial equality differing only by commuted factors/sign, derive scalar equality first (e.g., `U - V = 0` → `U = V`), state single-factor commutations, then scale/subtract and expand
- Manual says: "goal-directed verification, not unrestricted search"

---

## Decision Rules by Goal Type

### Route Selection

**IF** goal is `exist x S st {facts}`  
→ **THEN** use `witness exist x S st {facts} from <value>: <body>`

**IF** goal is `exist! x S st {facts}` (unique existence)  
→ **THEN** use `witness exist! x S st {facts} from <value>: <body>` + prove uniqueness

**[EMPIRICAL - current Litex binary]:** For a multi-variable goal such as `exist! x, y, z S st {facts}`, uniqueness is a tuple equality between two satisfying tuples. After proving the corresponding component equalities, conclude `(x1, y1, z1) = (x2, y2, z2)`.

**IF** goal is `forall x S: assumptions =>: conclusion`  
→ **THEN** write proof body that derives conclusion from assumptions

**IF** goal needs case analysis  
→ **THEN** use `by cases: case <cond1>: ... case <cond2>: ...`

**IF** goal needs contradiction  
→ **THEN** use `by contra: ... impossible <contradictory_fact>`

**IF** goal is set/function equality  
→ **THEN** use `by extension: ? A = B` (proves both subset directions)

**IF** goal is finite enumeration universal  
→ **THEN** use `by enumerate finite_set: ? forall x S: ...`

**IF** goal matches known theorem exactly  
→ **THEN** use `by thm <theorem_name>(<args>)`

**IF** goal is definition of concrete prop  
→ **THEN** use `by def $PropName(args)` (explicitly unfolds definition)

### Using `obtain`

**IF** you have known `exist x S st {facts}`  
→ **THEN** use `obtain x_name from exist x S st {facts}`  
→ **RESULT**: `x_name $in S` + all facts in body

**IF** you have concrete prop `$P(args)` with single exist clause  
→ **THEN** use `obtain x_name from $P(args)`  
→ **RESULT**: unfolds definition + extracts witness

**IF** theorem returns existential  
→ **THEN** use `obtain x_name from thm <name>(<args>)`  
→ **RESULT**: applies theorem + extracts its existential conclusion

### Redundancy Avoidance

**IF** fact already proved by `forall` matching  
→ **THEN** DON'T add redundant `by thm` call  
→ **REASON**: Keep explicit restatement only when verifier shows bridge fact needed

**IF** `by thm <name>(args)` already stored conclusions  
→ **THEN** DON'T repeat the conclusion as next statement

---

## Proof Patterns

### Pattern 1: Transform goal to precondition combination
```litex
# Goal: C = 0  |  Preconditions: A = 0, B = 0
C = C + A - A          # Add-subtract technique
  = (C + A) - A        # Regroup
  = B - A              # Substitute using equalities
  = 0 - 0 = 0         # Replace with preconditions
```

### Pattern 2: Expand and simplify
```litex
# Goal: complex_expr = simple_expr
complex_expr = ...     # Step-by-step expansion
             = ...     # Polynomial simplification (auto)
             = simple_expr
```

### Pattern 3: Case analysis on order
```litex
by cases:
    case a <= b:
        # Derive conclusion under this case
    case b < a:
        # Derive conclusion under complementary case
```

### Pattern 4: Contradiction
```litex
by contra:
    ? <goal>  # Must redeclare the goal
    # Derive contradiction through direct equation/inequality chains
    impossible <contradictory_fact>
```

**Critical Syntax Constraints**:
- **Indentation**: Must be at 4 spaces (inside theorem body, same level as `? forall`)
- **Goal redeclaration**: Must start with `? <goal>` that restates the conclusion to prove
- **Body restrictions**: Can ONLY contain:
  - Direct equation chains (e.g., `a = b = c`)
  - Direct inequality chains
  - Final `impossible <fact>` statement
- **Forbidden in body**: `have`, `obtain`, `release`, `by def`, `by thm`
  - These will cause parse error: `expected 'impossible', got '<statement>'`

**Example with universal quantifier**:
```litex
thm example:
    ? forall x, y R:
        x > 0
        y > 0
        =>:
            x + y > 0
    by contra:
        ? x + y > 0  # Redeclare goal
        # Direct contradiction derivation
        x + y <= 0
        x <= -y
        impossible x > 0  # Contradicts premise
```

---

## Strategy-Specific Rules

### Universal Quantifiers

**IF** universal over `range(a, b)` or `closed_range(a, b)`  
→ **THEN** use `by for: ? forall i range(a, b): ...`

**IF** universal over finite Cartesian product  
→ **THEN** use `by for: ? forall (x, y) S × T: ...`

**IF** universal over displayed finite set  
→ **THEN** use `by enumerate finite_set: ? forall x {v1, v2, ...}: ...`

### Recursive Weighted Sums and Finite Chains

When no verified finite-sum API is available, encode the sum as a recursive prefix function instead of importing an unproved summation declaration:

1. Define `S(0) = 0` and `S(m) = S(m - 1) + term(m)` for positive `m`.
2. Define the companion variation prefix recursively, for example `V(0) = 0` and `V(m) = V(m - 1) + drop(m) * weight(m)`.
3. Prove the Abel/summation-by-parts identity for every natural `m` by induction. Put the required range restriction inside a local predicate as an implication such as `m <= n => identity(m)`; this lets induction range over all naturals while each use remains bounded.
4. Prove separately that every variation term is nonnegative. If one drop is strict and its weight is positive, use a second offset induction to propagate `V(s + offset) > 0` to the final prefix.
5. Use the endpoint weight equation and the zero weighted sum to derive `V(n) = 0`; contradiction then excludes every strict adjacent drop.
6. Convert adjacent equality to arbitrary finite-chain equality with an offset induction from the first index, then join two entries through that common value.

Keep the discrete identity, sign argument, endpoint simplification, and finite-chain propagation as separate theorems. This decomposition passed full-module strict verification without `trust`; it also avoids asking the verifier to perform summation algebra or transitive chain closure implicitly.

### Equality and Definition

**IF** set equality goal  
→ **THEN** use `by extension` (proves both membership directions)

**IF** folding a proved predicate body  
→ **THEN** use `by def $P(args)` (default one-line form)

**IF** verifier evidence or syntax requires goal block  
→ **THEN** use `by def: ? $P(args)`

**[EMPIRICAL - current Litex binary]:** `by def` unfolds proposition definitions, but it does not unfold a `have fn` definition. To expose a named function during a proof, first assert its full defining equality explicitly, then use that equality in the algebraic replacement chain.

### Theorem Application

**IF** theorem produces one atomic fact you need  
→ **THEN** select it directly: `by thm theorem_name(args) => fact`

**IF** theorem produces multiple facts or none match target  
→ **THEN** use bare `by thm theorem_name(args)` to instantiate all

**IF** theorem result needs intermediate facts  
→ **THEN** use goal-block form with helper derivations

### Finite-Sum Function Substitution

For `finite_set_sum_substitution`, an anonymous summand expression may not be matched even when a pointwise equality is already available. The verified pattern is:

1. Name both summand functions on the exact same index set.
2. Prove their pointwise equality and derive `$fn_eq`.
3. Invoke `finite_set_sum_substitution` on the two named sums.
4. State the final result as one explicit adjacent equality chain; do not rely on implicit transitivity across separate sum facts.

---

## Debugging Checklist

1. Check error line number
2. Verify previous step output format
3. Split complex steps into atomic equality chains
4. Confirm `by thm` arguments match theorem signature
5. For "not found" errors, check spelling and file imports
6. For verification failures, add intermediate bridge facts
7. If all else fails, read the actual error from `parse_litex_error.py` output

---

## Anti-Patterns (Common Mistakes)

1. **Commenting out required theorem** - Defeats verification purpose
2. **Assuming mid-proof rearrangement** - `A+B=0` does NOT auto-derive `A=-B`
3. **Chaining multiple builtins** - Expose intermediate steps explicitly
4. **Redundant theorem calls** - If `forall` already matched, don't re-invoke
5. **Guessing syntax from other languages** - Always check `litex_syntax_quick_reference.md` or working examples
6. **Multi-step inequality inference** - `u<1/3, v<1/3` does NOT auto-derive `u+v<2/3`; use one-at-a-time addition: `u+v<1/3+v`, then `1/3+v<1/3+1/3`, transitivity gives `u+v<2/3`
7. **Negation transforms in inequalities** - `1-w<2/3 => -w<-1/3 => w>1/3` fails; instead add `w` to both sides: `u+v+w<2/3+w`, substitute `u+v+w=1`, then subtract `2/3` to get `1/3<w`

---

## Reference

- Library: `LItex_vs_Lean_new-2/IMO/Litex/geo/library_final.lit`
- Solutions output: `LItex_vs_Lean_new-2/IMO/solutions/`
- Verification binary: `<YOUR_LITEX_REPO>/golitex/target/release/litex`
- Syntax reference: `litex_syntax_quick_reference.md`
- Builtin skills: See appendix in `litex_syntax_quick_reference.md`

---

## Quick Verification Commands

From the IMO directory, first inspect `solutions/problem_X/litex.config` for expected exports and dependency order. Then run full module check from problem directory:

```bash
cd solutions/problem_X/
/path/to/litex -runner -r . -all -json > litex_verified.json
jq '{result, ok, error, target}' litex_verified.json
jq -r '.trace' litex_verified.json
```

Inspect structured results for all expected exports, including warnings and trusted imports. Neither text counts of `success` nor `-f FILE` prove full module passed. Ordinary check trusts imported library results; for zero-trust requirement, run separate strict check. Consult `litex_problem_solving_workflow.md` Stage 4 for acceptance criteria and error handling.
