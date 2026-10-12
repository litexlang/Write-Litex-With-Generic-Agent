#!/usr/bin/env python3
"""
Litex Problem Extractor
Extract problem statement from problems_natural_language.json and generate solution template
"""

import json
import sys
import os
from pathlib import Path

# Default paths (relative to IMO directory)
PROBLEMS_JSON = "Math_Problem/problems_natural_language.json"
SOLUTIONS_DIR = "solutions"
GOLITEX_PATH = "<YOUR_LITEX_REPO>/<YOUR_LITEX_REPO>/golitex/target/release/litex"

def extract_problem(problem_id, json_path=PROBLEMS_JSON, output_dir=SOLUTIONS_DIR, generate_template=True):
    """
    Extract problem by ID and generate solution templates in subdirectory
    
    Args:
        problem_id: int or str, the problem ID
        json_path: path to problems_natural_language.json
        output_dir: base directory for solutions
        generate_template: whether to generate solution templates
    
    Returns:
        dict: problem data
    """
    # Load JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    
    # Find problem by ID
    problem = None
    for p in problems:
        if p['id'] == int(problem_id):
            problem = p
            break
    
    if not problem:
        print(f"❌ Problem ID {problem_id} not found!")
        print(f"Available IDs: 1-{len(problems)}")
        sys.exit(1)
    
    # Print problem info
    print("=" * 80)
    print(f"📝 PROBLEM {problem['id']}: {problem['name']}")
    print("=" * 80)
    print(f"\n📌 Source: {problem['source_title']}")
    print(f"📌 Topic: {problem['topic']}")
    print(f"📌 Difficulty: {problem['difficulty']}")
    
    print(f"\n{'─' * 80}")
    print("📖 PROBLEM STATEMENT (Natural Language)")
    print(f"{'─' * 80}")
    print(problem['problem'])
    
    print(f"\n{'─' * 80}")
    print("🎯 CONDITIONS (Given)")
    print(f"{'─' * 80}")
    print(problem['conditions'])
    
    print(f"\n{'─' * 80}")
    print("🎯 STATEMENT (To Prove)")
    print(f"{'─' * 80}")
    print(problem['statement'])
    print("=" * 80)
    
    # Generate templates if requested
    if generate_template:
        problem_dir = Path(output_dir) / f"problem_{problem['id']}"
        problem_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate all template files
        templates = generate_all_templates(problem)
        
        for filename, content in templates.items():
            file_path = problem_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Created: {file_path}")
        
        print(f"\n📋 Next steps:")
        print(f"   1. cd {Path(output_dir).parent}")
        print(f"   2. Start full logging: python3 ../memory/Litex/start_full_logging.py {problem['id']}")
        print(f"   3. Edit files in {problem_dir}/")
        print(f"   4. cd {problem_dir} && {GOLITEX_PATH} -runner -r . -all -json > litex_verified.json")
    
    return problem

def generate_all_templates(problem):
    """Generate all template files for a problem"""
    
    templates = {}
    templates['litex.config'] = """[hierarchy]
module

[import]
geo = "../../Litex/geo"

[export]
predicate = "./predicate.lit"
theorem = "./theorem.lit"
solution = "./solution.lit"
"""
    
    # ===== solution.lit =====
    templates['solution.lit'] = f"""# {problem['source_title']}
# {problem['name']}
# Difficulty: {problem['difficulty']}
# Topic: {problem['topic']}

# ⚠️ TRANSLATION RULES ⚠️
# 1. 一句 NL 对照一句 Litex（One NL sentence → One Litex statement）
# 2. 不要封装（No abstraction/encapsulation in problem translation）
# 3. 不要在翻译中加入推理（No reasoning in translation, translate as-is）
# 4. 结论也直接翻译（Translate conclusion directly, no derivation）
# 5. 有需要的谓词和定理放在 predicate.lit 和 theorem.lit

# ============================================================================
# PROBLEM STATEMENT (Natural Language)
# ============================================================================
# {problem['problem'].replace(chr(10), chr(10) + '# ')}

# ============================================================================
# CONDITIONS (Given)
# ============================================================================
# {problem['conditions'].replace(chr(10), chr(10) + '# ')}

# ============================================================================
# STATEMENT (To Prove)
# ============================================================================
# {problem['statement'].replace(chr(10), chr(10) + '# ')}

# ============================================================================
# FORMALIZATION
# ============================================================================

# TODO: Define geometric objects
# Example:
# have a, b, c cart(R, R):
#     # NL: Points A, B, C
#     pass

# TODO: Define real parameters
# Example:
# have r R:
#     # NL: radius r
#     r > 0

# ============================================================================
# CONDITIONS AND STATEMENT
# ============================================================================
# ⚠️ 一句 NL 对照一句 Litex，不要合并或推理 ⚠️

# TODO: Formalize conditions as prop
prop conditions(...):
    # NL: [copy condition 1 here]
    # Litex: [translate condition 1 here]
    #
    # NL: [copy condition 2 here]  
    # Litex: [translate condition 2 here]
    pass

# TODO: Formalize statement as prop
prop statement(...):
    # NL: [copy statement here]
    # Litex: [translate statement here, no derivation]
    pass

# ============================================================================
# MAIN THEOREM
# ============================================================================

thm problem_{problem['id']}:
    forall ...:  # TODO: Add quantifiers
        conditions(...) => statement(...)
--
    # TODO: Write proof here
    # Proof strategy:
    # 1. 
    # 2. 
    # 3.
"""

    # ===== predicate.lit =====
    templates['predicate.lit'] = f"""# Custom Predicates for Problem {problem['id']}
# {problem['name']}

# ⚠️ PREDICATE RULES ⚠️
# 1. 只定义本题专用的谓词（Only problem-specific predicates）
# 2. 尽量使用库中已有的谓词（Prefer library predicates when possible）
# 3. 谓词定义要清晰明确（Clear and explicit definitions）

# ============================================================================
# CUSTOM PREDICATES
# ============================================================================

# Example:
# prop is_special_point(p cart(R, R), a cart(R, R), b cart(R, R)):
#     # NL: Point p satisfies special property relative to a, b
#     distance_sq(p, a) = distance_sq(p, b)

# TODO: Add your custom predicates here
"""

    # ===== theorem.lit =====
    templates['theorem.lit'] = f"""# Custom Theorems for Problem {problem['id']}
# {problem['name']}

# ⚠️ THEOREM RULES ⚠️
# 1. 只定义本题需要的辅助定理（Only auxiliary theorems needed for this problem）
# 2. 尽量使用库中已有的定理（Prefer library theorems when possible）
# 3. 定理要有完整的证明或标记 trust（Complete proof or mark with trust）

# ============================================================================
# CUSTOM THEOREMS
# ============================================================================

# Example:
# thm helper_lemma:
#     forall a, b cart(R, R):
#         distance_sq(a, b) >= 0
# --
#     # Proof here
#     pass

# TODO: Add your custom theorems here
"""

    # ===== README.md =====
    templates['README.md'] = f"""# Problem {problem['id']}: {problem['name']}

## Source
- **Title**: {problem['source_title']}
- **Type**: {problem.get('source_type', 'N/A')}
- **Difficulty**: {problem['difficulty']}
- **Topic**: {problem['topic']}

## Problem Statement
{problem['problem']}

## Conditions (Given)
{problem['conditions']}

## Statement (To Prove)
{problem['statement']}

## File Structure
```
problem_{problem['id']}/
├── solution.lit          # Main solution file
├── predicate.lit         # Custom predicates (if needed)
├── theorem.lit           # Custom theorems (if needed)
├── litex.config          # Module import and export order
├── agent_session.log     # Full session log (generated during solving)
├── litex_verified.json   # Verification output (generated after verification)
└── README.md             # This file
```

## Workflow
1. Start full logging: `python3 ../memory/Litex/start_full_logging.py {problem['id']}`
2. Edit `solution.lit` (main formalization and proof)
3. If needed, add custom predicates in `predicate.lit`
4. If needed, add custom theorems in `theorem.lit`
5. From this problem directory verify all exports: `{GOLITEX_PATH} -runner -r . -all -json > litex_verified.json`
6. Inspect `result`, `ok`, and `trace`; report trusted imports separately. Run `-strict` separately for zero-trust checking (the original geometry library currently fails strict verification).

## Translation Rules ⚠️
- **One NL sentence → One Litex statement** (一句 NL 对一句 Litex)
- **No abstraction in problem translation** (不要封装)
- **No reasoning in translation** (不要在翻译中推理)
- **Translate conclusion directly** (结论直接翻译，不要推导)
"""

    return templates

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_problem.py <problem_id> [--no-template]")
        print("Example: python3 extract_problem.py 5")
        sys.exit(1)
    
    problem_id = sys.argv[1]
    generate_template = "--no-template" not in sys.argv
    
    extract_problem(problem_id, generate_template=generate_template)

if __name__ == "__main__":
    main()
