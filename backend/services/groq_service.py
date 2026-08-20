"""
Groq AI Service
Provides progressive C compiler error guidance & AI diagnostics.
Respects exam policy (disabled in exams) and never raises errors.
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

Compiler Line Number: {line_number}
Mode: {mode}

Rules:
1. Do NOT provide complete corrected C code.
2. Do NOT solve the problem directly for the student.
3. Explain the error in simple, beginner-friendly terms.
4. Provide a single tactical debugging hint to guide self-correction.
5. Identify the C language concept involved.

Return ONLY valid JSON in this format:
{{
  "explanation": "What went wrong in simple terms",
  "reason": "Why the compiler reported this error",
  "hint": "Tactical hint to help the student debug independently",
  "concept": "C concept (e.g. Semicolon termination, Variable scope)"
}}"""


GROQ_MODELS = ["groq/compound-mini", "qwen/qwen3.6-27b", "groq/compound"]


def analyze_compiler_error(student_code: str, compiler_error: str, line_number: int | None, mode: str = "practice") -> dict:
    """
    Sends compiler error to Groq LLM and returns structured JSON guidance.
    Enforces mode policy: 'exam' mode strictly returns disabled AI status.
    """
    # Exam mode policy check — AI disabled
    if mode == "exam":
        return {
            "ai_disabled": True,
            "explanation": "AI Guidance is disabled during official examination sessions.",
            "reason": "Exam policy in effect.",
            "hint": "Inspect the technical compiler error above to debug your code.",
            "concept": "Examination Policy"
        }

    fallback = {
        "ai_disabled": False,
        "explanation": f"Compiler syntax error detected near line {line_number if line_number else 'unknown'}.",
        "reason": "The GCC compiler could not parse the C source syntax.",
        "hint": "Inspect the line indicated above for missing semicolons, unmatched braces, or uninitialized variables.",
        "concept": "C Syntax / Statement Termination"
    }

    if not _client:
        return fallback

    prompt = _PROMPT_TEMPLATE.format(
        student_code=student_code,
        compiler_error=compiler_error,
        line_number=line_number if line_number else "unknown",
        mode=mode
    )

    for model_name in GROQ_MODELS:
        try:
            response = _client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
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
                "concept": parsed.get("concept", fallback["concept"])
            }
        except Exception as e:
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

