"""
Groq AI Service
Provides progressive C compiler error guidance & AI diagnostics.
Includes intelligent line-offset detection (previous line vs reported line),
complete code context analysis, beginner-friendly explanations in simple language,
point-wise reasons (why it happened) and point-wise step-by-step fixes (how to correct),
test case failure analysis, and memorable concept tips.
Respects exam policy (disabled in exams) and never raises unhandled errors.
"""

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GROQ_API_KEY")
_client = Groq(api_key=_api_key) if _api_key else None


def format_code_with_line_numbers(code: str) -> str:
    """
    Formats complete student C code with explicit 1-based line numbers.
    This guarantees the LLM has exact line-by-line visibility over the entire program.
    """
    lines = code.splitlines()
    if not lines:
        return "  1 | [Empty File]"
    return "\n".join(f"{i+1:3d} | {line}" for i, line in enumerate(lines))


def detect_actual_error_line_heuristic(code: str, compiler_error: str, reported_line: int | None) -> int:
    """
    Heuristic analyzer to detect if a C syntax error actually belongs on the previous line.
    E.g. If line 5 triggers 'expected ; before return', line 4 was missing ';'.
    """
    if not reported_line or reported_line <= 1:
        return reported_line or 1

    lines = code.splitlines()
    if reported_line > len(lines) + 1:
        return min(reported_line, len(lines))

    err_lower = compiler_error.lower()

    # Semicolon missing, expected token, or declaration error often trips on next line
    if any(k in err_lower for k in [
        "expected ';'", "expected ';'", "expected declaration or statement",
        "expected expression before", "expected '=', ',', ';'", "before 'return'",
        "before '}'", "before 'printf'", "before 'scanf'", "before 'if'", "before 'for'", "before 'while'"
    ]):
        # Find previous non-empty, non-comment line
        idx = reported_line - 2  # 0-indexed line right above reported_line
        while idx >= 0:
            stripped = lines[idx].strip()
            if stripped and not stripped.startswith("//") and not stripped.startswith("/*"):
                # If this previous line does not end with ';' or '{' or '}' or ':' or '#', it's the real culprit!
                if not stripped.endswith(";") and not stripped.endswith("{") and not stripped.endswith("}") and not stripped.endswith(":") and not stripped.startswith("#"):
                    return idx + 1
                break
            idx -= 1

    return reported_line


_COMPILER_ERROR_PROMPT_TEMPLATE = """You are an expert C Programming Tutor in a college laboratory.

A student attempted to compile the following C program:

Complete Student C Code (with line numbers):
{numbered_student_code}

Compiler Error:
{compiler_error}

Compiler Reported Line Number: {line_number}
Line Directly Above: {prev_line}
Mode: {mode}

Strict Teaching & Debugging Guidelines:
1. COMPLETE SOURCE CODE & LINE OFFSET ANALYSIS:
   - You have the student's COMPLETE source code with exact 1-based line numbers.
   - In C compilers (like GCC/Clang), syntax errors such as missing semicolons (';'), unclosed parentheses (')'), unmatched brackets/braces ('}}'), or unclosed quotes are very frequently reported on the NEXT line or subsequent statement rather than where the typo occurred.
   - Analyze line {line_number} AND the preceding lines (especially line {prev_line}).
   - Determine the "actual_error_line" (the real line number where the student must make the fix). For example, if line 4 is missing a semicolon and GCC reports line 5, "actual_error_line" MUST be 4.
2. DO NOT provide the full corrected code copy-paste solution. Guide the student so they learn how to fix it themselves.
3. Use simple, beginner-friendly language (avoid heavy compiler jargon).
4. Provide structured POINT-WISE explanations:
   - "why_it_happened": A list of clear bullet points explaining WHY this error occurred and why the compiler behaved this way.
   - "how_to_fix": A list of simple, step-by-step action items explaining HOW to correct the code without giving away the full program.
5. Provide a "remember_tip" ("Key Information to Remember"): A memorable rule of thumb for future C programming.
6. Identify the core C concept involved.

Return ONLY valid JSON in this exact structure:
{{
  "actual_error_line": {prev_line},
  "reported_line": {line_number},
  "explanation": "Simple plain-language summary of the mistake and where it is located",
  "why_it_happened": [
    "Point 1 explaining why this happened in simple words",
    "Point 2 explaining compiler token scanning or delimiter expectations"
  ],
  "how_to_fix": [
    "Step 1: Check line X for...",
    "Step 2: Add or modify..."
  ],
  "remember_tip": "Memorable rule of thumb for students to remember",
  "concept": "C concept (e.g. Statement Semicolon Termination, Bracket Matching, Variable Declaration)"
}}"""


_TEST_FAILURE_PROMPT_TEMPLATE = """You are an expert C Programming Laboratory Tutor.

A student wrote a C program that compiled successfully, but when tested against test cases, the output did not match the expected result.

Problem Title: {problem_title}
Problem Description:
{problem_description}

Complete Student C Code (with line numbers):
{numbered_student_code}

Failed Test Case Details:
{test_cases_summary}

Mode: {mode}

Strict Teaching & Diagnostic Guidelines:
1. COMPLETE CODE LOGIC ANALYSIS:
   - Inspect the algorithmic logic (input reading with scanf, format specifiers, variable types, arithmetic calculations, loop conditions/boundaries, conditional branching, output formatting with printf, newline characters '\\n').
   - Determine "actual_error_line" (the line number where the logic deviates or where the fix is required).
2. Explain clearly in simple, beginner-friendly language why the student's output differs from expected.
3. Provide structured POINT-WISE explanations:
   - "why_it_happened": A list of clear bullet points explaining WHY the calculation or output formatting produced a different result.
   - "how_to_fix": A list of step-by-step action items guiding how to fix the logic without giving away the full code copy-paste.
4. Provide a "remember_tip": A memorable rule of thumb for this programming concept.
5. Identify the core C concept involved.

Return ONLY valid JSON in this exact structure:
{{
  "actual_error_line": 1,
  "explanation": "Simple plain-language explanation of why the output did not match",
  "why_it_happened": [
    "Point 1 explaining the logical or format discrepancy",
    "Point 2 explaining variable values or loop iterations"
  ],
  "how_to_fix": [
    "Step 1: Look at line X and check...",
    "Step 2: Ensure your calculation or format matches..."
  ],
  "remember_tip": "Memorable rule of thumb for future C programming",
  "concept": "C concept involved"
}}"""


GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]


def analyze_compiler_error(student_code: str, compiler_error: str, line_number: int | None, mode: str = "practice") -> dict:
    """
    Sends complete student code and compiler error to Groq LLM.
    Returns structured point-wise JSON guidance with intelligent line offset detection.
    Enforces mode policy: 'exam' mode strictly returns disabled AI status.
    """
    actual_line = detect_actual_error_line_heuristic(student_code, compiler_error, line_number)
    prev_line = max(1, line_number - 1) if (line_number and line_number > 1) else 1

    # Exam mode policy check — AI disabled
    if mode == "exam":
        return {
            "ai_disabled": True,
            "actual_error_line": line_number,
            "reported_line": line_number,
            "explanation": "AI Guidance is disabled during official examination sessions.",
            "reason": "Exam policy in effect.",
            "why_it_happened": ["Official laboratory examination in progress."],
            "how_to_fix": ["Inspect the compiler error output and debug independently."],
            "hint": "Inspect the technical compiler error above to debug your code.",
            "remember_tip": "During examinations, verify syntax independently.",
            "concept": "Examination Policy"
        }

    is_offset = (actual_line != line_number) if line_number else False

    fallback_why = [
        f"The compiler was reading tokens and encountered an unexpected token near line {line_number or 'unknown'}.",
        f"In C, statements must end with a delimiter like ';' or braces '}}'. When omitted on line {actual_line}, the compiler only notices the mistake when reaching line {line_number or actual_line}."
    ] if is_offset else [
        f"The compiler encountered invalid C syntax on line {line_number or 1}.",
        "A required symbol, correct format, or matching delimiter was missing or mismatched."
    ]

    fallback_how = [
        f"Look directly at Line {actual_line} (the line right above line {line_number}): check if it is missing a semicolon (';') at the end.",
        f"Verify that all parenthesis '()', curly braces '{{}}', and double quotes '\"' on lines {actual_line} to {line_number or actual_line} are properly matched.",
        "Ensure all variable names and function names are spelled correctly."
    ]

    fallback = {
        "ai_disabled": False,
        "actual_error_line": actual_line,
        "reported_line": line_number,
        "explanation": f"Mistake detected on Line {actual_line} (even though the compiler reported Line {line_number or actual_line})." if is_offset else f"Syntax issue detected on Line {line_number or 1}.",
        "reason": f"When a delimiter like a semicolon (;) or closing bracket is missing on line {actual_line}, the C compiler continues reading until line {line_number or actual_line} before flagging an error.",
        "why_it_happened": fallback_why,
        "how_to_fix": fallback_how,
        "hint": f"Check Line {actual_line} for a missing semicolon ';' or unclosed delimiter before Line {line_number or actual_line}.",
        "remember_tip": "Rule of Thumb: In C, whenever GCC reports 'expected ; before...', the missing semicolon is almost always on the line immediately ABOVE the reported line!",
        "concept": "C Statement Termination & Delimiters"
    }

    if not _client:
        return fallback

    numbered_code = format_code_with_line_numbers(student_code)

    prompt = _COMPILER_ERROR_PROMPT_TEMPLATE.format(
        numbered_student_code=numbered_code,
        compiler_error=compiler_error,
        line_number=line_number if line_number else "unknown",
        prev_line=actual_line,
        mode=mode
    )

    for model_name in GROQ_MODELS:
        try:
            response = _client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=700,
            )

            raw_text = response.choices[0].message.content.strip()
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            parsed = json.loads(raw_text)

            # Extract why_it_happened and how_to_fix lists
            why_list = parsed.get("why_it_happened")
            if not isinstance(why_list, list) or len(why_list) == 0:
                why_list = [parsed.get("reason", fallback["reason"])]

            how_list = parsed.get("how_to_fix")
            if not isinstance(how_list, list) or len(how_list) == 0:
                how_list = [parsed.get("hint", fallback["hint"])]

            act_line = parsed.get("actual_error_line")
            try:
                act_line = int(act_line)
            except (ValueError, TypeError):
                act_line = actual_line

            return {
                "ai_disabled": False,
                "actual_error_line": act_line,
                "reported_line": line_number,
                "explanation": parsed.get("explanation", fallback["explanation"]),
                "reason": parsed.get("reason", "; ".join(why_list)),
                "why_it_happened": why_list,
                "how_to_fix": how_list,
                "hint": parsed.get("hint", "; ".join(how_list)),
                "remember_tip": parsed.get("remember_tip", fallback["remember_tip"]),
                "concept": parsed.get("concept", fallback["concept"])
            }
        except Exception:
            continue

    return fallback


def analyze_test_failure(student_code: str, problem_title: str, problem_description: str, failed_test_cases: list, mode: str = "practice") -> dict:
    """
    Sends complete student code and failed test case details to Groq LLM when outputs do not match.
    Returns structured point-wise JSON guidance explaining the logical discrepancy.
    Enforces mode policy: 'exam' mode strictly returns disabled AI status.
    """
    if mode == "exam":
        return {
            "ai_disabled": True,
            "actual_error_line": None,
            "explanation": "AI Guidance is disabled during official examination sessions.",
            "reason": "Exam policy in effect.",
            "why_it_happened": ["Examination session active."],
            "how_to_fix": ["Verify your output format and calculation logic."],
            "hint": "Compare your program output with the problem requirements.",
            "remember_tip": "During examinations, test your logic with manual trace tables.",
            "concept": "Examination Policy"
        }

    # Format test cases summary
    tc_summary_lines = []
    for idx, tc in enumerate(failed_test_cases, start=1):
        inp = tc.get("input", "[None]")
        exp = tc.get("expected", "[Expected Output]")
        act = tc.get("actual", "[Actual Output]")
        tc_summary_lines.append(f"Test Case #{idx}:\n  Input: {inp}\n  Expected Output: {exp}\n  Student Actual Output: {act}")
    test_cases_summary = "\n\n".join(tc_summary_lines) if tc_summary_lines else "Test case output mismatch."

    fallback = {
        "ai_disabled": False,
        "actual_error_line": None,
        "explanation": "Your program output did not match the expected output for the given test case(s).",
        "reason": "The output produced by your logic differs from the expected format or mathematical calculation.",
        "why_it_happened": [
            "The calculation logic produced a different result than what the problem requires.",
            "Or the output formatting (spaces, newlines '\\n', or extra text prompts in printf) does not match the expected format exactly."
        ],
        "how_to_fix": [
            "Step 1: Check your input reading (scanf) — ensure you use the address operator '&' for numeric variables.",
            "Step 2: Step through your arithmetic or loop boundaries with the test input values.",
            "Step 3: Make sure your printf matches the exact expected string without unnecessary prompt text."
        ],
        "hint": "Check your input reading (scanf), calculation logic, loop bounds, and output formatting (printf).",
        "remember_tip": "Rule of Thumb: When test cases fail, trace your variables step-by-step with sample input values to see where your calculation differs from the expected result.",
        "concept": "Logic & Output Verification"
    }

    if not _client:
        return fallback

    numbered_code = format_code_with_line_numbers(student_code)

    prompt = _TEST_FAILURE_PROMPT_TEMPLATE.format(
        problem_title=problem_title or "C Programming Problem",
        problem_description=problem_description or "Write a C program according to the specification.",
        numbered_student_code=numbered_code,
        test_cases_summary=test_cases_summary,
        mode=mode
    )

    for model_name in GROQ_MODELS:
        try:
            response = _client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=700,
            )

            raw_text = response.choices[0].message.content.strip()
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            parsed = json.loads(raw_text)

            why_list = parsed.get("why_it_happened")
            if not isinstance(why_list, list) or len(why_list) == 0:
                why_list = [parsed.get("reason", fallback["reason"])]

            how_list = parsed.get("how_to_fix")
            if not isinstance(how_list, list) or len(how_list) == 0:
                how_list = [parsed.get("hint", fallback["hint"])]

            act_line = parsed.get("actual_error_line")
            try:
                act_line = int(act_line) if act_line is not None else None
            except (ValueError, TypeError):
                act_line = None

            return {
                "ai_disabled": False,
                "actual_error_line": act_line,
                "explanation": parsed.get("explanation", fallback["explanation"]),
                "reason": parsed.get("reason", "; ".join(why_list)),
                "why_it_happened": why_list,
                "how_to_fix": how_list,
                "hint": parsed.get("hint", "; ".join(how_list)),
                "remember_tip": parsed.get("remember_tip", fallback["remember_tip"]),
                "concept": parsed.get("concept", fallback["concept"])
            }
        except Exception:
            continue

    return fallback


_SOLUTION_ANALYSIS_PROMPT = """You are an AI C Programming Laboratory Evaluator.

Problem Title: {problem_title}
Problem Description: {problem_description}

Complete Student C Code (with line numbers):
{numbered_student_code}

Static Analysis Findings:
{static_analysis}

Test Case Results:
{test_results}

Tasks:
1. Determine if the student's solution is genuine (implements logic) or fake/hardcoded (simply prints static answers without using input).
2. Note that if the problem does NOT require input, printing fixed output is completely valid.
3. If valid, check if the student used a creative/alternative valid approach (e.g. ternary operators, bitwise logic, custom functions).

Return ONLY valid JSON in this format:
{{
  "classification": "VALID",
  "confidence": 0.95,
  "reasoning": "Simple educational explanation",
  "is_creative_approach": false,
  "creative_summary": ""
}}"""


def analyze_solution_semantics(student_code: str, problem_title: str, problem_description: str, static_analysis: dict, test_results: dict) -> dict:
    """
    Sends compiled complete code & static findings to Groq LLM to verify semantic integrity
    and detect hardcoding vs creative alternative solutions.
    """
    fallback = {
        "classification": "SUSPICIOUS" if static_analysis.get("is_suspicious") else "VALID",
        "confidence": 0.85,
        "reasoning": "Static analysis indicates potential hardcoded output without input processing." if static_analysis.get("is_suspicious") else "Solution follows valid logic structure.",
        "is_creative_approach": False,
        "creative_summary": ""
    }

    if not _client:
        return fallback

    numbered_code = format_code_with_line_numbers(student_code)

    prompt = _SOLUTION_ANALYSIS_PROMPT.format(
        problem_title=problem_title,
        problem_description=problem_description,
        numbered_student_code=numbered_code,
        static_analysis=json.dumps(static_analysis),
        test_results=json.dumps(test_results)
    )

    for model_name in GROQ_MODELS:
        try:
            response = _client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=400,
            )

            raw_text = response.choices[0].message.content.strip()
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            parsed = json.loads(raw_text)

            return {
                "classification": parsed.get("classification", fallback["classification"]),
                "confidence": float(parsed.get("confidence", fallback["confidence"])),
                "reasoning": parsed.get("reason", fallback["reasoning"]),
                "is_creative_approach": bool(parsed.get("is_creative_approach", False)),
                "creative_summary": parsed.get("creative_summary", "")
            }
        except Exception:
            continue

    return fallback

