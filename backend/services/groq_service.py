"""
Groq AI Service
Provides progressive C compiler error guidance & AI diagnostics.
Includes intelligent line-offset detection (previous line vs reported line),
beginner-friendly explanations, tactical debugging hints, and memorable concepts.
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

_PROMPT_TEMPLATE = """You are an expert C Programming Tutor in a college laboratory.

A student attempted to compile the following C program:

Student Code:
{student_code}

Compiler Error:
{compiler_error}

Compiler Reported Line Number: {line_number}
Mode: {mode}

Special Teaching Guidelines for C Compilation Errors:
1. LINE OFFSET AWARENESS:
   - In C compilers (like GCC/Clang), syntax errors such as missing semicolons (';'), unclosed parentheses (')'), unmatched brackets, or unclosed string quotes are very frequently reported on the NEXT line or the subsequent statement rather than where the typo occurred.
   - Analyze whether the true mistake is on the line immediately preceding the reported line (e.g. line {line_number} vs line {prev_line}).
   - If the previous line is missing a semicolon or delimiter, explicitly tell the student to inspect the previous line!
2. Do NOT provide complete corrected C code or solve the program for the student.
3. Explain the error in simple, beginner-friendly terms without overwhelming jargon.
4. Provide a tactical step-by-step hint to guide self-correction.
5. Provide a "remember_tip" ("Key Information to Remember"): A memorable, concise rule of thumb that helps the student remember this concept in future C programming (e.g. "Rule of Thumb: In C, statements end with a semicolon ';'. When GCC reports 'expected ; before...', always check the line right ABOVE the reported line!").
6. Identify the core C language concept involved.

Return ONLY valid JSON in this exact structure:
{{
  "explanation": "Simple explanation of what went wrong, explicitly noting if the mistake is on the previous line",
  "reason": "Why the compiler reported this line (e.g. compiler only realizes a semicolon is missing when reaching the next statement)",
  "hint": "Actionable hint to guide the student to fix the error independently",
  "remember_tip": "Concise key information / rule of thumb for students to remember",
  "concept": "C concept (e.g. Statement Semicolon Termination, Bracket Matching, Variable Declaration)"
}}"""


GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]


def analyze_compiler_error(student_code: str, compiler_error: str, line_number: int | None, mode: str = "practice") -> dict:
    """
    Sends compiler error to Groq LLM and returns structured JSON guidance with
    previous line offset detection and memorable rules of thumb.
    Enforces mode policy: 'exam' mode strictly returns disabled AI status.
    """
    prev_line = max(1, line_number - 1) if (line_number and line_number > 1) else 1

    # Exam mode policy check — AI disabled
    if mode == "exam":
        return {
            "ai_disabled": True,
            "explanation": "AI Guidance is disabled during official examination sessions.",
            "reason": "Exam policy in effect.",
            "hint": "Inspect the technical compiler error above to debug your code.",
            "remember_tip": "During examinations, verify syntax independently.",
            "concept": "Examination Policy"
        }

    fallback = {
        "ai_disabled": False,
        "explanation": f"Compiler syntax error detected near line {line_number if line_number else 'unknown'}. In C, if a semicolon (;) or bracket is missing, the compiler often flags the NEXT line.",
        "reason": f"The GCC compiler encountered an unexpected token. When a semicolon or closing brace is omitted on line {prev_line}, the compiler only detects the error on line {line_number if line_number else 'unknown'}.",
        "hint": f"Inspect line {line_number} and the line directly above it (line {prev_line}) for missing semicolons ';', unclosed braces '}}', or unmatched parentheses ')'.",
        "remember_tip": "Rule of Thumb: In C, whenever you see 'expected ; before...', the missing semicolon is almost always on the line immediately ABOVE the reported line!",
        "concept": "C Statement Termination & Delimiters"
    }

    if not _client:
        return fallback

    prompt = _PROMPT_TEMPLATE.format(
        student_code=student_code,
        compiler_error=compiler_error,
        line_number=line_number if line_number else "unknown",
        prev_line=prev_line,
        mode=mode
    )

    for model_name in GROQ_MODELS:
        try:
            response = _client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.25,
                max_tokens=600,
            )

            raw_text = response.choices[0].message.content.strip()
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            parsed = json.loads(raw_text)

            return {
                "ai_disabled": False,
                "explanation": parsed.get("explanation", fallback["explanation"]),
                "reason": parsed.get("reason", fallback["reason"]),
                "hint": parsed.get("hint", fallback["hint"]),
                "remember_tip": parsed.get("remember_tip", fallback["remember_tip"]),
                "concept": parsed.get("concept", fallback["concept"])
            }
        except Exception:
            continue

    return fallback


_SOLUTION_ANALYSIS_PROMPT = """You are an AI C Programming Laboratory Evaluator.

Problem Title: {problem_title}
Problem Description: {problem_description}

Student C Code:
{student_code}

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
    Sends compiled code & static findings to Groq LLM to verify semantic integrity
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

    prompt = _SOLUTION_ANALYSIS_PROMPT.format(
        problem_title=problem_title,
        problem_description=problem_description,
        student_code=student_code,
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
                "reasoning": parsed.get("reasoning", fallback["reasoning"]),
                "is_creative_approach": bool(parsed.get("is_creative_approach", False)),
                "creative_summary": parsed.get("creative_summary", "")
            }
        except Exception:
            continue

    return fallback
