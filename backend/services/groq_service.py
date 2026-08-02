"""
Groq AI Service
Sends compiler errors to Groq LLM and returns structured beginner-friendly feedback.
Only called when GCC reports a compilation failure.
"""

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GROQ_API_KEY")
_client = Groq(api_key=_api_key) if _api_key else None

_PROMPT_TEMPLATE = """You are an expert C Programming Tutor.

A beginner student attempted to compile the following C program.

Programming Language: C
Compiler: GCC

Student Code:
{student_code}

Compiler Error:
{compiler_error}

Compiler Line: {line_number}

Your task is to help the student understand the error.

Rules:
- Do NOT generate corrected code.
- Do NOT rewrite the student's program.
- Do NOT solve the problem directly.
- Encourage debugging.
- Keep explanations simple enough for beginners.

Return ONLY valid JSON in this exact format:
{{
  "explanation": "",
  "reason": "",
  "hint": "",
  "concept": ""
}}

Where:
- explanation: Explain the compiler error in simple beginner-friendly language.
- reason: Explain why the compiler produced this specific error.
- hint: Give one debugging hint without revealing the answer.
- concept: Explain the C programming concept involved."""


def analyze_compiler_error(student_code: str, compiler_error: str, line_number: int | None) -> dict:
    """
    Sends student code and compiler error to Groq.
    Returns structured JSON feedback. Never raises — always returns a safe dict.
    """
    fallback = {
        "explanation": "AI explanation is temporarily unavailable.",
        "reason": "",
        "hint": "Read the compiler error message carefully — it tells you exactly what is wrong.",
        "concept": "",
    }

    if not _client:
        return fallback

    try:
        prompt = _PROMPT_TEMPLATE.format(
            student_code=student_code,
            compiler_error=compiler_error,
            line_number=line_number if line_number else "unknown",
        )

        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )

        raw_text = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

        parsed = json.loads(raw_text)

        # Ensure all expected keys exist
        return {
            "explanation": parsed.get("explanation", ""),
            "reason": parsed.get("reason", ""),
            "hint": parsed.get("hint", ""),
            "concept": parsed.get("concept", ""),
        }

    except json.JSONDecodeError:
        return fallback
    except Exception:
        return fallback
