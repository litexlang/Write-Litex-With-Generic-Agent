# Litex Incremental Debugging Guide

**Purpose**: Unified reference for incremental verification workflows, combining session mode, REPL-try pattern, trust debt management, and proof-block journaling.  
**Replaces**: litex_session_verification_sop.md + litex-repl-try-workflow.md

---

## Overview: Two Debugging Approaches

### Approach 1: Session Mode (File-Based)
- Verify one `try:` block at a time from a registered `.lit` file
- Maintain session state between blocks
- Use for multi-file projects with dependencies

### Approach 2: REPL-Try Pattern (Fragment-Based)
- Send proof fragments directly to a persistent session process
- Keep journal in JSON, materialize to `.lit` at checkpoints
- Use for rapid iteration on a single file

---

## 1. Session-Based Verification Mode

### File Naming Convention ⚠️

**Standard filenames** (enforced 2026-09-01):
- **Solution file**: `solution.lit` (NOT `proof.lit`)
- **Verification output**: `*.log` files contain JSON stream (one object per line), NOT `*.json`

Example:
```bash
litex -compact -f solution.lit > solution_verify.log 2> solution_verify.err
```

### Why Session Mode?

**Problem with full-file verification**:
- Every error requires re-running the entire file
- Slow feedback loop
- Hard to isolate which block is failing

**Solution: Session mode**:
- Verify one `try:` block at a time
- Maintain session state between blocks
- Only retry the failing block
- Successful blocks are committed to the current Runtime and recorded in the proof-block journal; assemble the `.lit` file explicitly at the end

### Command Syntax

```bash
# Session mode with -before flag
litex -compact -session -before <file.lit>

# After each try: block submission
# - If PASS → the whole block commits to the current Runtime; record it in the journal
# - If FAIL → the whole block rolls back; fix and resubmit only that block
```

### Workflow

```text
1. Open session: litex -compact -session -before problem_XXX.lit

2. Submit one top-level proof block at a time in dependency order:
   try:
     have step1: ... by <justification>

   → If PASS: the whole block commits; mark it accepted and continue
   → If FAIL: the whole block rolls back; diagnose and resubmit only that block
   → Earlier accepted blocks remain available after a failed block

3. Each submission creates a proof-block journal entry (see Section 3).

4. If only the unaccepted current block changes, keep the session and retry it.

5. If an accepted upstream block, the `-before` file, an import, or a same-name declaration changes, restart the session and replay all still-valid accepted blocks in journal order.

6. When all blocks pass, assemble the formal `.lit` files, normally remove debugging `try:` wrappers, then verify from `solutions/problem_X/` in a fresh Runtime:
   litex -runner -r . -all -json > litex_verified.json

7. Complete only after the JSON result, trace, and every configured export/theorem have been checked; `-f`/session success is local debugging, not final acceptance. Consult `litex_problem_solving_workflow.md` Stage 4 for strict-mode boundaries.
```

---

## 2. Trust Debt Management

### Core Principle

**Trust is NOT a skip button** - it is a **technical debt marker** that must be:
1. Used only when genuinely blocked
2. Scoped as narrowly as possible
3. Recorded with exact debt type and discharge plan

### When to Use Trust

**✅ Use trust when**:
1. **Proof blocker**: Proof is correct but verifier times out or cannot find the path
2. **Library blocker**: Need a theorem not yet in library (add later)
3. **Inference blocker**: Verifier's inference engine cannot bridge obvious steps
4. **Syntax blocker**: Language limitation prevents expressing the proof
5. **Formulation blocker**: Problem statement issue, not proof issue

**❌ DO NOT use trust for**:
- "I don't know how to prove this" → That's not trust, that's stuck (→ Stage 5)
- "This is tedious to write" → Write it anyway or find the missing abstraction
- "I'll come back to this later" → No. Either prove now or record specific blocker

### Trust Scope Rules

```litex
# ❌ BAD: Overly broad trust
trust thm large_theorem: ... by trust  # trusts entire theorem

# ✅ GOOD: Narrow source trust
thm large_theorem: ...
  proof:
    have step1: ... by thm geom::helper1(...)
    have step2: ... by trust  # only this step is trusted
    have step3: ... by calc
    qed by step1, step2, step3
```

**Principle**: Trust the **narrowest scope** that unblocks progress.

### Recording Trust Debt

Every trust must have a comment documenting:
1. **Debt type**: proof/library/inference/syntax/formulation
2. **Exact blocker**: Why can't this be proved now?
3. **Discharge path**: How will this be resolved?

```litex
# Example 1: Inference blocker
have parallel_transitive: 
  parallel(AB, CD) ∧ parallel(CD, EF) → parallel(AB, EF)
  by trust  
  # DEBT(inference): Verifier cannot chain parallel transitivity
  # DISCHARGE: Wait for verifier inference upgrade or add as library theorem

# Example 2: Library blocker
have angle_bisector_equal:
  angle_bisector(AD, ∠BAC) → angle(∠BAD) = angle(∠CAD)
  by trust
  # DEBT(library): Missing angle_bisector_creates_equal_angles theorem
  # DISCHARGE: Add theorem to unified_euclidean_geometry.lit after problem solved
```

---

## 3. Proof-Block Journal

### Purpose

Track each verification attempt for:
- Debugging patterns
- Learning from failures
- Documenting what was tried

### Journal Structure

```json
{
  "problem": "problem_XXX",
  "session_start": "2026-08-27T10:00:00",
  "blocks": [
    {
      "block_id": 1,
      "attempt": 1,
      "status": "pass",
      "block_content": "have step1: midpoint(M, AB) by thm geom::midpoint_def(...)",
      "timestamp": "2026-08-27T10:05:00"
    },
    {
      "block_id": 2,
      "attempt": 1,
      "status": "fail",
      "error": "Type mismatch: expected Point, got R × R",
      "block_content": "have step2: distance(A, M) = distance(M, B) by calc",
      "timestamp": "2026-08-27T10:08:00"
    },
    {
      "block_id": 2,
      "attempt": 2,
      "status": "pass",
      "fix": "Added type annotation: M: Point",
      "block_content": "have M: Point by ... \n have step2: ...",
      "timestamp": "2026-08-27T10:12:00"
    }
  ],
  "total_attempts": 5,
  "blocks_verified": 3,
  "trust_count": 1
}
```

### Journal Location

```
temp/litex_skill/problem_XXX/
├── problem_XXX.lit
├── problem_XXX_nl_proof.md
├── problem_XXX_journal.json  ← verification journal
└── problem_XXX_session.log   ← raw session output
```

---

## 4. Integration with Stage 4 Loop

### Updated Stage 4 Workflow

```
Stage 4: Check Loop (session-based)
├─ Initialize session: litex -session -before problem_XXX.lit
│
├─ For each proof block (attempt ≤ MAX_ATTEMPTS):
│  ├─ Submit try: block
│  ├─ Record attempt in journal
│  │
│  ├─ Result?
│  │  ├─ PASS → materialize block, continue to next
│  │  ├─ FAIL (fixable) → diagnose, fix, retry same block
│  │  └─ FAIL (blocker) → add trust + record debt, continue
│  │
│  └─ Check escalation:
│     ├─ Block attempts ≥ 10 → Stage 5
│     └─ Non-fixable + non-trustable → Stage 5
│
└─ All blocks verified → Complete
```

### Fixable Errors (retry in session)

- Syntax errors (typos, formatting)
- Missing proof steps (add intermediate steps)
- Wrong theorem references (search and correct)
- Type mismatches (add type annotations)
- **[Extensible - add more during problem-solving]**

### Trust-Worthy Blockers

- Proof correct but verifier timeout (inference blocker)
- Need theorem not in library (library blocker)
- Syntax limitation (syntax blocker)

**Action**: Add trust with debt record, continue session

### Escalation Triggers (→ Stage 5)

- Same block fails 10 times despite fixes
- Blocker is not fixable AND not trust-worthy
- Fundamental method failure (after adding all theorems)

---

## 5. Module System Configuration and Verification Commands

### Critical Discovery (2026-08-29)

**Problem**: `[import] datasets = ["KB"]` is **NOT valid syntax**. Many verification failures were caused by incorrect module configuration.

### Correct Module Configuration

**For each problem directory** (`problem_XXX/`):

1. **Create `litex.config`** declaring it as a module:

```ini
[hierarchy]
module

[import]
KB = "../../../KB"

[export]
main = "./solution.lit"
```

**Key points**:
- Must declare `[hierarchy] module` to use `[import]`
- Import path must be relative: `KB = "../../../KB"`
- Only `[hierarchy] module` can declare non-standard package imports

2. **Ensure KB is properly configured** (`KB/litex.config`):

```ini
[hierarchy]
module

[export]
unified = "./unified_euclidean_geometry.lit"
euclidean_geometry = "./euclidean_geometry.lit"
predicates = "./predicates.lit"
primitives = "./primitives.lit"
theorems = "./theorems.lit"
```

**Critical requirement**: **ALL .lit files in a module directory MUST be listed in [export]**. Litex will error on unexported files.

3. **Use correct module path in solution.lit**:

```litex
# ❌ WRONG - using non-existent namespace
geom::unified::distance_sq(p, a)

# ✅ CORRECT - using imported module name
KB::unified::distance_sq(p, a)
```

**Path syntax**: `<module_name>::<export_name>::<symbol>`
- `KB` = module name from `[import] KB = "..."`
- `unified` = export name from KB's `[export] unified = "..."`
- `distance_sq` = function/theorem name

### Verification Commands

```bash
# Incremental debugging only: -f can stop before later exports.
litex -compact -f solution.lit

# Final acceptance from solutions/problem_X/ (all configured exports):
litex -runner -r . -all -json > litex_verified.json
```

Inspect `result`, `ok`, `error`, and `trace` in the JSON and confirm every expected export/theorem was checked. A successful single-file or session run is not final acceptance. For strict verification and trusted dependency boundaries follow `litex_problem_solving_workflow.md` Stage 4.

### Common Pitfalls

1. **"configuration paths must be quoted strings"**
   - Cause: Using invalid syntax like `[import] datasets = ["KB"]`
   - Fix: Use `[import] KB = "../path/to/KB"`

2. **"unexported Litex module path `X.lit`"**
   - Cause: `.lit` file exists but not in `[export]`
   - Fix: Add all `.lit` files to `[export]` section

3. **"function `geom::unified::X` not defined"**
   - Cause: Wrong namespace path
   - Fix: Use correct module name from `[import]`, e.g., `KB::unified::X`

4. **"-isolated mode can run but KB functions not found"**
   - Cause: `-isolated` mode does NOT load module system
   - Fix: Use `-f` with proper `litex.config`, not `-isolated`

5. **Sibling export namespace is undefined although both files are exported**
   - Cause: `[export]` is evaluated in order, or the dependent file is checked alone with `-f`; a later sibling export is not available to an earlier/dependent export.
   - Fix: List dependency exports before their consumers and verify the configured module tree with `litex -r <module_directory>`.

6. **Strict mode stops before the local target**
   - Cause: `-strict -r` also checks configured imports and may reject a pre-existing user `axiom` in an imported KB.
   - Fix: Inspect structured error `source`/`path`; report imported dependency trust failure separately from local target verification, and never claim whole-tree strict success.

7. **Strict verification may run with high CPU and empty logs**
   - Do not classify an active strict process as failed solely because stdout/stderr remain empty; monitor the exact PID, CPU usage, and elapsed time, and do not launch a duplicate verifier.
   - If an external timeout requires terminating that exact PID before the verifier returns, record that no verifier exit code was captured; do not claim strict success or convert the timeout into a proof error.

### Verification Checklist

Before running Litex verification:
- [ ] `problem_XXX/litex.config` exists with `[hierarchy] module`
- [ ] `[import] KB = "..."` path is correct (test with `ls ../../../KB`)
- [ ] `KB/litex.config` has ALL .lit files in `[export]`
- [ ] If one local export references another, the dependency appears first in `[export]` and verification uses `litex -r <module_directory>`
- [ ] `solution.lit` uses the configured import/export namespace, not a guessed namespace
- [ ] Golitex binary path is correct (usually `../../../tool/<YOUR_LITEX_REPO>/golitex/target/release/litex`)
- [ ] Audit structured result records; exit code `0` alone is insufficient

---

## 6. Session Commands Cheatsheet

```bash
# Start session
litex -compact -session -before problem_XXX.lit

# Submit block (interactive or from file)
# In session REPL:
try:
  have step: ... by ...

# Check session state
# (Successful blocks are automatically materialized)

# End session
# Exit REPL or complete all blocks

# Final module acceptance after session success, from solutions/problem_X/
litex -runner -r . -all -json > litex_verified.json
```

---

## 6. Best Practices

### ✅ DO

1. **Submit small blocks**: Each try: block should be 1-3 statements
2. **Record every trust**: Comment with debt type and discharge plan
3. **Narrow trust scope**: Trust single statement, not entire theorem
4. **Use journal**: Track attempts to learn from patterns
5. **Test before promote**: Try direct fact before wrapping in theorem

### ❌ DON'T

1. **Don't trust blindly**: Every trust must have documented blocker
2. **Don't overly broad trust**: Trust entire proof blocks
3. **Don't skip journaling**: Verification history is valuable
4. **Don't rerun full file**: Use session mode for iteration
5. **Don't promote without test**: Check if builtin can handle it first

---

## 7. Example Session

```bash
$ litex -compact -session -before problem_228.lit

Litex session started. Submit blocks:

> try:
    have M: Point by exists_midpoint(A, B)
    have midpoint_M: midpoint(M, AB) by thm geom::midpoint_def(A, B, M)

✅ Block verified and materialized

> try:
    have equal_dist: distance(A, M) = distance(M, B) by thm geom::midpoint_equal_distance(...)

❌ Error: Theorem geom::midpoint_equal_distance not found

> try:
    have equal_dist: distance(A, M) = distance(M, B) by trust
    # DEBT(library): Need midpoint_equal_distance theorem
    # DISCHARGE: Add to library after problem complete

✅ Block verified with trust (1 debt recorded)

> try:
    qed by midpoint_M, equal_dist

✅ Block verified. All blocks complete!

Session summary:
- Total blocks: 3
- Attempts: 4
- Trust count: 1
- Time: 8 minutes
```

---

## 8. When NOT to Use Session Mode

Session mode is NOT needed for:
- Simple problems (≤ 5 proof steps)
- First-time full verification after NL→Litex translation
- Final release verification (from the problem module directory use `litex -runner -r . -all -json > litex_verified.json`, then check JSON results and trace; `-f` only checks a prefix)

**Use session mode for**:
- Debugging failing proofs (Stage 4 loop)
- Complex proofs with many blocks
- Iterative refinement

---

## 9. Production Suffix Verification and Known-Later-Error Isolation

Use this only for library work where earlier declarations must be loaded but the target theorem itself must remain strictly checked.

1. Run direct file mode; do not combine `-runner` with `-trust-before-line` (the CLI rejects that combination):
   ```bash
   litex -compact -f <library.lit> -trust-before-line <N>
   ```
2. Set `<N>` at a **top-level statement header before the target proof region**, never inside the target theorem. A misplaced boundary can put part or all of the target inside the trusted prefix.
   - Do not text-splice an existing theorem into an `axiom` merely to bypass an earlier failure: theorem declarations may contain multiple `?` goal blocks, while an axiom accepts exactly one. Prefer `-trust-before-line` at an exact top-level boundary.
3. Treat exit code alone as insufficient. Audit the structured output for the target theorem and require:
   - no target `error` result;
   - `execution_ok: true` and `direct_trust: 0` **when those fields are emitted** (some direct file runs omit both);
   - the `trusted_prefix.first_verified_statement_line` equals the target's top-level header line, proving the target starts outside the trusted prefix.
   - When replacing an `axiom` with a theorem, audit the entire trusted prefix for **all semantically equivalent axioms**, not only the same declaration name. Remove equivalent aliases from the temporary verification copy; otherwise automation may prove the target from a renamed axiom while still reporting `verified` and `direct_trust: 0`.
4. If the full monolithic file fails only at a known later statement, create a temporary prefix copy ending immediately after the new theorem and verify that prefix with zero errors.
   - In a configured/flattened module, do not place an unexported temporary `.lit` as a direct child: module discovery rejects it before proof checking. Use an independent system temporary directory and copy the required valid config/source dependencies there.
   - For split maintenance sources that mix qualified references (for example `definitions::x`) with bare imported calls, do not validate by raw concatenation or by running the dependent file alone. Reconstruct the dependency modules in an independent temporary tree, preserve `[module] flatten = true`, declare each `[import]`, and list dependencies under `[allow bare import]` when the source uses their symbols bare; truncate only the final dependent module at the next top-level declaration.
   - Then also run the full file to prove that every reported error is later and pre-existing.
5. Report the two facts separately: **target/prefix strictly verified** and **full file still has known later errors**. A clean prefix is not evidence that the whole source is clean.

This workflow was action-verified while replacing axioms in split and monolithic geometry libraries: target prefixes passed with zero errors and zero direct trust, while full sources independently reproduced only later existing failures.

### Archive documentation semantics

For a verified problem archive, keep the roles distinct:
- `PROBLEM_STATEMENT.md`: preserve the complete NL problem and show the one-by-one NL condition → `forall` premise and NL request → `=>` conclusion mapping.
- `FORMALIZATION_CHECKPOINT.md`: record frozen theorem contracts, verification command/evidence, trust boundary, and unresolved verification limitations.
- `SESSION_SUMMARY.md`: summarize reusable mathematical modeling, Litex formalization, and debugging lessons learned from solving that problem. It is not a file manifest and should not duplicate the verification report.
- When copying a verified module into a deeper or shallower archive directory, recompute every relative `[import]` path from the archive location and confirm it with `realpath`; do not require `litex.config` byte identity across directory depths. Verify the staged archive from its own directory before the atomic swap, then run one final fresh verification from the installed archive path.
- For an additive showcase migration, first back up and hash-audit the existing entries, then copy each new module's `litex.config` plus only the `.lit` files referenced by that configuration; exclude unreferenced probes and verifier logs. Independently full-verify any changed shared dependency, run a representative importing module from the staged and final installed paths, and finish by auditing old-entry hashes, config references, file cleanliness, and the expected module count.

### Structured-output audit notes

- Litex may append an isolated REPL banner/prompt after the final JSON object; parse the JSON stream first and treat that suffix as non-record output.
- Verifier output is a stream of pretty-printed JSON values, not guaranteed line-delimited JSON; parse with a streaming decoder (`raw_decode`-style) rather than `json.loads` per line.
- The final summary object may omit `type` entirely; do not require `type: "summary"`. In current compact output it can identify itself as `output_type: "run summary"`; otherwise use summary-only fields such as `execution_ok`, `trusted_prefix`, `direct_trust`, or `proof_method_counts`, then audit those values. Inspect actual keys before coding the parser.
- A theorem record's `statement` payload may be a plain string rather than an object. Resolve the target by the record's real theorem identifier or a normalized statement-string header; never assume nested statement fields.
- Exit code `0` is insufficient: count structured `error` records and inspect the target theorem plus summary fields (`verification_status`, `direct_trust`, `trusted_object_assumptions`, `unverified_imports`).
- When reporting recursive result totals, count every JSON object that contains a `result` field, including successful `unverified import warning` summary records. Report warning records and structured errors separately; do not subtract warnings from the result-node total.
- Treat verification evidence as content-addressed: after any change to an archived source, imported translation/configuration, or even source comments that shift recorded lines, the prior fresh log, source hash, theorem line references, and reports derived from them are stale. Rerun every affected full file in a fresh Runtime, then regenerate the structured audit and hashes from the new artifacts before claiming completion.
- When validating a replacement source, use an isolated temporary module whose config exports only that candidate. Adding the candidate beside existing exports makes a full `-f` run verify all exported siblings and can duplicate theorem counts; leaving it unexported can fail module discovery before parsing. Derive expected JSON-object counts from the actual structured stream and stable semantic totals, not from the candidate's declaration count alone, because imported dependencies also emit records.
- With `-compact` redirected to files, stdout/stderr may remain at zero bytes until a long full-file run exits. Do not infer a hang from empty output alone; monitor the exact verifier PID/child, elapsed CPU activity, and a separately written exit-status file, and do not launch a duplicate verifier while the original is active. When detecting an existing verifier, avoid `ps ... | grep <full command>` because the probe shell may contain and match that text itself; first filter by the process executable/`comm`, then inspect its arguments.
- When comparing source statements with verifier records, normalize equivalent unary-minus forms such as `-(x)` and `-1 * x`; do not reject a verified theorem on formatting alone.
- Generate publication-document hashes from the final archived bytes and independently recompute them before the final audit; manual digest transcription can invalidate an otherwise verified archive.
- Keep audit text predicates aligned with the actual problem statement and formalization contract; a wording mismatch is an audit-script failure, not evidence that verification failed.
- If full-dependency strict verification remains CPU-saturated and sampling shows object cloning or quantifier-fact expansion, preserve the process evidence, terminate only the exact verifier PID, and report the full run as incomplete. For a publishable result, extract the current-KB transitive dependency closure with source/hash provenance and require fresh normal+strict verification of that independent minimal module; never present the reduced-module result as full-KB strict verification.
- Resolve the target by its actual theorem identifier and inspect structured records separately from source text. Apply forbidden-token scans only to source files; summary JSON fields such as `axioms` and `direct_trust` are audit metadata, not source constructs.
- For a self-contained replay archive, do not make the importing problem module the parent of its imported KB: LiteX rejects an `[import]` that points to a descendant of the current module root. Place the problem and KB as sibling modules, set the problem module to import `../KB`, and run verification from the problem module.

---

## Integration Points

- **Stage 4**: Primary usage - iterative debugging loop
- **Stage 3**: After NL→Litex translation, first verification attempt (can use session or full)
- **Journal**: Analyzed in failure reports (Stage 8) to understand error patterns


---

## 10. REPL-Try Pattern (Fragment-Based Workflow)

### Overview

Build once with `cargo build --release`, then use one persistent `target/release/litex -compact -session -before <current-file.lit>` process for iterative proof debugging of a registered file. Never use the debug binary for this workflow.

`-before` executes the ordered project prefix strictly before the target, skips the target's current contents and everything after it, and accepts source fragments in the target file's environment. The same loop applies when the target is empty, partial, or failing.

### Recommended Loop

1. Start release `-session -before <current-file.lit>` once and wait for `{"event":"ready","mode":"project"}`.
2. Initialize one persistent JSON proof-block journal for the target before sending the first candidate.
3. Send the target's first top-level statement as literal Litex wrapped in one outermost `try:` session frame.
4. If it fails, keep the same process. Record the materially distinct candidate, verifier evidence, diagnosis, and next smallest change in JSON, then send only the corrected current statement in another outermost `try:`.
5. If it succeeds, record the accepted statement without the wrapper, dependencies, and reusable lesson in JSON before sending the next source statement. Do not edit the target `.lit` file yet.
6. If a real blocker is identified, keep the intended statement, use the narrowest legal `trust`, record the debt, and continue.
7. At a coherent theorem or file checkpoint, materialize accepted blocks from JSON into `.lit` in source order and run release `-f <current-file.lit>`. Record the clean file-gate result in the journal.

### JSON Proof-Block Journal

First resolve the working repository: use the repository that owns the target `.lit` file or the task's output artifacts. This is not automatically the golitex source checkout that supplies the Litex binary or skill, and it is not determined merely by the shell's current directory. If a task spans repositories, use the repository that owns the target being journaled.

Use the source- or task-owned working area's existing machine-artifact or experience directory. If none exists, use `<source-workspace>/proof_journals/<target-relative-path>.json`, replacing path separators with `__`. For a textbook module under `scripts/<Workspace>/textbook/`, the source workspace is `scripts/<Workspace>/`. Never create `<golitex-root>/proof_journals/`, even for a golitex-owned target, and never put a journal in the textbook module tree. If the owning workspace is ambiguous, resolve it before sending the first candidate rather than guessing a root-level fallback. Keep the journal out of mathematical `.lit` source. Do not use `/tmp` for its only copy: the journal is the recoverable staging artifact and later blocks should be able to reuse it.

Use one valid JSON object with this minimum shape:

```json
{
  "schema_version": 1,
  "target": "relative/path/to/file.lit",
  "session_command": "target/release/litex -compact -session -before relative/path/to/file.lit",
  "proof_spine": ["first mathematical move", "second mathematical move"],
  "attempts": [
    {
      "statement_index": 0,
      "candidate": "try:\n  have step1: ... by ...",
      "outcome": "fail",
      "error": "...",
      "diagnosis": "..."
    },
    {
      "statement_index": 0,
      "candidate": "try:\n  have step1: ... by ...",
      "outcome": "pass",
      "accepted_source": "have step1: ... by ...",
      "lesson": "..."
    }
  ],
  "checkpoints": [
    {
      "file_verify_command": "target/release/litex -compact -f file.lit",
      "result": "pass",
      "timestamp": "..."
    }
  ]
}
```

Checkpoint after every 5–10 accepted statements or before ending a session. On checkpoint failure, diagnose the first file-level inconsistency before adding more fragments. Do not continue with new mathematical steps until the file gate is clean.

### Anti-Patterns

- Do not restart the session process after every failure. Transaction-based `try:` should not leak facts into the parent environment.
- Do not use Python-side `sandbox_run()` as the primary workflow when direct Litex `try:` is available.
- Do not rerun `target/release/litex -compact -f long_file.lit` for every small candidate proof edit. Use project-aware `-f` only for file baseline, checkpoint, and final file verification. Use release `-r` only for an explicit complete-module gate.
- Optionally use `target/release/litex -compact -f <current-file.lit> -trust-before-line <X>` for a disk-first suffix preview. `X` must be the exact physical top-level statement header of the first changed or not-cleanly-verified statement. Statements before `X` skip well-definedness and proof verification; a suffix that depends on them is `indirect_trust`, so this run is never `checkable`. Move `X` backward after any earlier edit and always finish with clean `-f`.
- Never use default-profile `cargo test` as the Litex verifier. Use the release CLI; use `cargo test --release` only when a Rust-only harness is required.
- Remember that `try:` is transactional, not an optimizer: it saves time by preserving an already-loaded context after failure.
- When evaluating speed, include failure-heavy trials; the benefit is largest when many candidate fragments are wrong before the final one verifies.

### Disposable Probes and Cleanup Gate

Create every disposable proof copy, isolated config, liveness probe, raw transcript, or scratch module in a unique directory made with `mktemp -d "<golitex-root>/private/<task>.XXXXXX"`. Keep the exact directory path and remove that exact task-owned directory in the same turn, including after a failed or interrupted check. Do not manually use `/tmp` or `/private/tmp` unless the user explicitly requires that absolute location. Never create `.codex_tmp_*` or probe directories elsewhere in the repository, never put a probe in a canonical `.lit` tree, and never mutate a production `litex.config` merely to register a probe.

Before reporting completion, inspect the repository root and every touched source/module directory for task-created `proof_journal*`, `.codex_tmp_*`, probe, scratch-copy, transcript, and temporary-config residue. Remove only artifacts owned by the current task. If any remain, report their exact paths and do not claim that cleanup is complete.

---

## Choosing Between Approaches

| Criterion | Session Mode (File-Based) | REPL-Try Pattern (Fragment-Based) |
|-----------|---------------------------|-----------------------------------|
| **Best for** | Multi-file projects with dependencies | Single-file rapid iteration |
| **Journal format** | Internal session state | Explicit JSON journal |
| **Checkpoint strategy** | After each `try:` block | Every 5-10 statements |
| **File materialization** | Edit `.lit` directly | Defer until checkpoint |
| **Use when** | Dependencies across files | Experimenting with proof structure |
