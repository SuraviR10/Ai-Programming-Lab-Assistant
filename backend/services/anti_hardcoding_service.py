"""
Anti-Hardcoding Static Analysis Service
Inspects student C code structure to detect input-independent hardcoded printf outputs.
Considers problem requirement metadata to avoid false positives on legitimate print problems.
"""

import re


def analyze_c_code_structure(student_code: str, problem_meta: dict) -> dict:
    """
    Performs static AST/structural analysis on student C code.
    Returns hardcoding risk score (0.0 to 1.0) and evidence breakdown.
    """
    requires_input = problem_meta.get("requires_input", True)
    allows_fixed_output = problem_meta.get("allows_fixed_output", False)
    expected_output = (problem_meta.get("expected_output") or "").strip().lower()
    sample_output = (problem_meta.get("sample_output") or "").strip().lower()

    # Exception check: Problems that naturally allow fixed output (e.g. Hello World)
    if allows_fixed_output or not requires_input:
        return {
            "requires_input": False,
            "allows_fixed_output": True,
            "has_input_ops": False,
            "has_constant_print": True,
            "is_suspicious": False,
            "hardcoding_risk_score": 0.0,
            "evidence": ["Problem natively permits static text printing."]
        }

    # 1. Inspect input operations in C code
    input_patterns = [
        r'\bscanf\s*\(',
        r'\bgetchar\s*\(',
        r'\bfgets\s*\(',
        r'\bfscanf\s*\(',
        r'\bread\s*\(',
        r'\bcin\b'
    ]
    has_input_ops = any(re.search(pat, student_code) for pat in input_patterns)

    # 2. Inspect static printf statements for hardcoded expected values
    has_constant_print = False
    evidence = []

    printf_matches = re.findall(r'printf\s*\(\s*"([^"]+)"', student_code)
    for string_literal in printf_matches:
        norm_lit = re.sub(r'\s+', ' ', string_literal).strip().lower()
        if expected_output and (expected_output in norm_lit or norm_lit in expected_output):
            has_constant_print = True
            evidence.append(f"Literal output matching sample result ('{string_literal}') detected in printf statement.")
            break
        if sample_output and (sample_output in norm_lit or norm_lit in sample_output):
            has_constant_print = True
            evidence.append(f"Literal sample output ('{string_literal}') hardcoded directly in program.")
            break

    if not has_input_ops:
        evidence.append("No standard C input processing function (scanf, fgets, etc.) found in source code.")

    # 3. Calculate Risk Score
    risk_score = 0.0

    if not has_input_ops and has_constant_print:
        risk_score = 0.95
    elif not has_input_ops:
        risk_score = 0.75
    elif has_constant_print:
        risk_score = 0.40
    else:
        risk_score = 0.05

    is_suspicious = (risk_score >= 0.70)

    return {
        "requires_input": requires_input,
        "allows_fixed_output": allows_fixed_output,
        "has_input_ops": has_input_ops,
        "has_constant_print": has_constant_print,
        "is_suspicious": is_suspicious,
        "hardcoding_risk_score": round(risk_score, 2),
        "evidence": evidence
    }
