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
    Heuristic analyzer to detect if a C syntax error actually belongs on a previous line or unclosed block.
    E.g.
    1. If line 5 triggers 'expected ; before return', line 4 was missing ';'.
    2. If line 9 triggers 'expected declaration or statement at end of input', an earlier block (like line 5 'if (...) {') was never closed.
    """
    if not code:
        return reported_line or 1

    lines = code.splitlines()
    total_lines = len(lines)
    err_lower = (compiler_error or "").lower()

    # 1. Unclosed Brace / Block Analysis
    if any(k in err_lower for k in [
        "expected declaration or statement at end of input",
        "expected '}' at end of input",
        "expected '}' before",
        "unterminated",
        "expected '{'",
        "reached end of file while parsing"
    ]):
        # Track opening braces and matching
        open_blocks = [] # list of (line_num, line_text)
        for i, l in enumerate(lines, start=1):
            clean_l = re.sub(r'//.*$', '', l) # remove line comments
            clean_l = re.sub(r'".*?"', '""', clean_l) # remove strings
            for ch in clean_l:
                if ch == '{':
                    open_blocks.append((i, l.strip()))
                elif ch == '}' and open_blocks:
                    open_blocks.pop()

        if len(open_blocks) > 1:
            # More than just main() is unclosed! The innermost unclosed block (e.g. if/for/while) is the culprit
            innermost_line, _ = open_blocks[-1]
            return innermost_line

    if not reported_line or reported_line <= 1:
        return reported_line or 1

    if reported_line > total_lines + 1:
        return min(reported_line, total_lines)

    # 2. Missing Semicolon or Delimiter on Preceding Statement
    if any(k in err_lower for k in [
        "expected ';'", "expected declaration or statement",
        "expected expression before", "expected '=', ',', ';'", "before 'return'",
        "before '}'", "before 'printf'", "before 'scanf'", "before 'if'", "before 'for'", "before 'while'"
    ]):
        # Find previous non-empty, non-comment line
        idx = reported_line - 2  # 0-indexed line right above reported_line
        while idx >= 0:
            stripped = lines[idx].strip()
            if stripped and not stripped.startswith("//") and not stripped.startswith("/*"):
                if not stripped.endswith(";") and not stripped.endswith("{") and not stripped.endswith("}") and not stripped.endswith(":") and not stripped.startswith("#"):
                    return idx + 1
                break
            idx -= 1

    return reported_line


_COMPILER_ERROR_PROMPT_TEMPLATE = """You are an expert C Programming Tutor in a college laboratory.

A student attempted to compile the following C program:

Complete Student C Code (with line numbers):
{numbered_student_code}

Full Compiler Error Output:
{compiler_error}

Compiler Flagged Line Number: {line_number}
Mode: {mode}

Strict Teaching & Multi-Error Debugging Guidelines:
1. COMPLETE SOURCE CODE & ERROR TRACE:
   - Carefully analyze the student's COMPLETE source code and the compiler output.
   - Count open and close curly braces '{{' vs '}}', parentheses '()', brackets '[]', and semicolons ';'.
   - Determine whether the mistake occurred on the reported line, on a preceding statement (e.g. missing semicolon on line 4 when line 5 is reported), or inside an unclosed block (e.g. an 'if (...) {{' on line 5 that was never closed before 'return 0;').
   - If there is a single error or MULTIPLE compiler errors, provide a comprehensive breakdown for each issue.
2. DO NOT provide the full copy-paste solution. Explain what is missing, why it happened, and how to fix it step-by-step.
3. Structure your response as JSON with:
   - "actual_error_line": The exact line number in the student's code where the primary fix must be applied.
   - "reported_line": The line number reported by GCC.
   - "explanation": Simple plain-language summary of what happened.
   - "why_it_happened": List of clear bullet points explaining why this happened in simple words.
   - "how_to_fix": List of step-by-step action items explaining how to correct the code.
   - "errors": An array containing an object for each error detected (if multiple or 1 error):
     [
       {{
         "actual_error_line": integer,
         "reported_line": integer,
         "title": "Short descriptive title (e.g. Unclosed if-statement block / Missing semicolon / Undeclared variable)",
         "explanation": "Simple plain-language description",
         "why_it_happened": ["Point 1...", "Point 2..."],
         "how_to_fix": ["Step 1...", "Step 2..."]
       }}
     ]
   - "remember_tip": A memorable rule of thumb for students to remember.
   - "concept": Core C concept involved.

Return ONLY valid JSON in this exact structure:
{{
  "actual_error_line": {prev_line},
  "reported_line": {line_number},
  "explanation": "Simple plain-language summary",
  "why_it_happened": [
    "Point 1 explaining why this happened in simple words",
    "Point 2 explaining compiler token scanning or delimiter expectations"
  ],
  "how_to_fix": [
    "Step 1: Check line X for...",
    "Step 2: Add or modify..."
  ],
  "errors": [
    {{
      "actual_error_line": {prev_line},
      "reported_line": {line_number},
      "title": "Error Title",
      "explanation": "Explanation for this error",
      "why_it_happened": ["Point 1...", "Point 2..."],
      "how_to_fix": ["Step 1...", "Step 2..."]
    }}
  ],
  "remember_tip": "Memorable rule of thumb for students to remember",
  "concept": "C Concept Name"
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
    "groq/compound-mini",
    "qwen/qwen3.8-27b",
    "groq/compound",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "allam-2-7b"
]


def analyze_compiler_error(student_code: str, compiler_error: str, line_number: int | None, mode: str = "practice") -> dict:
    """
    Sends complete student code and compiler error to Groq LLM.
    Returns structured point-wise JSON guidance with intelligent line offset detection and multi-error support.
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
            "errors": [],
            "remember_tip": "During examinations, verify syntax independently.",
            "concept": "Examination Policy"
        }

    is_offset = (actual_line != line_number) if line_number else False

    # Clean fallback explanation without awkward repetition
    if is_offset:
        fallback_why = [
            f"The compiler was scanning tokens and encountered an unexpected token near line {line_number or 'unknown'}.",
            f"An opening block, delimiter, or statement on line {actual_line} was not properly terminated before reaching line {line_number or actual_line}."
        ]
        fallback_how = [
            f"Inspect Line {actual_line} (the statement/block before line {line_number}): check if it is missing a closing brace '}}' or semicolon ';'.",
            f"Verify that all parenthesis '()', curly braces '{{}}', and quotes '\"' are balanced between line {actual_line} and line {line_number or actual_line}.",
            "Ensure all opened code blocks are properly closed with '}'."
        ]
    else:
        fallback_why = [
            f"The compiler encountered invalid C syntax on line {line_number or 1}.",
            "A required symbol, correct format, or matching delimiter was missing or mismatched."
        ]
        fallback_how = [
            f"Look directly at Line {actual_line}: check if a required symbol, delimiter, or type declaration is missing.",
            f"Verify that all parenthesis '()', curly braces '{{}}', and double quotes '\"' on line {actual_line} are properly matched.",
            "Ensure all variable names and function names are spelled correctly."
        ]

    fallback_error_item = {
        "actual_error_line": actual_line,
        "reported_line": line_number,
        "title": "Syntax Issue on Line " + str(actual_line),
        "explanation": f"Mistake detected on Line {actual_line} (even though the compiler reported Line {line_number or actual_line})." if is_offset else f"Syntax issue detected on Line {line_number or 1}.",
        "why_it_happened": fallback_why,
        "how_to_fix": fallback_how
    }

    fallback = {
        "ai_disabled": False,
        "actual_error_line": actual_line,
        "reported_line": line_number,
        "explanation": f"Mistake detected on Line {actual_line} (even though the compiler reported Line {line_number or actual_line})." if is_offset else f"Syntax issue detected on Line {line_number or 1}.",
        "reason": f"When a delimiter like a semicolon (;) or closing bracket is missing on line {actual_line}, the C compiler continues reading until line {line_number or actual_line} before flagging an error.",
        "why_it_happened": fallback_why,
        "how_to_fix": fallback_how,
        "hint": f"Check Line {actual_line} for a missing semicolon ';' or unclosed delimiter before Line {line_number or actual_line}." if is_offset else f"Check Line {actual_line} for missing symbols or syntax typos.",
        "errors": [fallback_error_item],
        "remember_tip": "Rule of Thumb: In C, whenever GCC reports 'expected ; before...' or 'expected declaration at end of input', the mistake is on the line where the unclosed block or statement began!",
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
                temperature=0.1,
                max_tokens=900,
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

            # Extract multi-error array
            errors_list = parsed.get("errors")
            if not isinstance(errors_list, list) or len(errors_list) == 0:
                errors_list = [{
                    "actual_error_line": act_line,
                    "reported_line": line_number,
                    "title": "Compiler Error on Line " + str(act_line),
                    "explanation": parsed.get("explanation", fallback["explanation"]),
                    "why_it_happened": why_list,
                    "how_to_fix": how_list
                }]

            return {
                "ai_disabled": False,
                "actual_error_line": act_line,
                "reported_line": line_number,
                "explanation": parsed.get("explanation", fallback["explanation"]),
                "reason": parsed.get("reason", "; ".join(why_list)),
                "why_it_happened": why_list,
                "how_to_fix": how_list,
                "hint": parsed.get("hint", "; ".join(how_list)),
                "errors": errors_list,
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

