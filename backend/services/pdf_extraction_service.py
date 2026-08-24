"""
PDF Parsing & AI Program Extraction Service
Handles text extraction from uploaded PDF manuals, scanned PDF architecture detection,
and AI-assisted detection of distinct programming problems and metadata extraction.
"""

import os
import re
import json
import logging
from io import BytesIO
from typing import List, Dict, Any

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

from services.groq_service import _client, GROQ_MODELS

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """You are an expert Computer Science Laboratory Manual Analyst.

Analyze the following text extracted from a College C Programming Laboratory Manual.

Text Content:
{manual_text}

Instructions:
1. Identify all distinct PROGRAMMING PROBLEMS / EXERCISES intended for students to write code.
2. IMPORTANT: Distinguish programming exercises/questions from purely explanatory theory, algorithms, unit titles, or code examples.
3. For each detected programming problem, extract the following details:
   - program_number (Integer e.g. 1, 2, 3)
   - title (Short title summarizing the program, e.g., "Largest of Three Numbers")
   - problem_statement (Full clear statement of what the student needs to write)
   - topic (Concept or Unit name, e.g. "Arrays", "Loops", "Pointers", "Unit 3 - Arrays")
   - input_format (Input requirements, e.g., "Three space-separated integers")
   - output_format (Output expectations, e.g., "Largest = X")
   - constraints (Constraints if mentioned, or null)
   - sample_input (Sample input string if available, or null)
   - sample_output (Sample output string if available, or null)
   - reference_code (Reference/solution C code if provided in the manual, or null)
   - confidence (Confidence score between 0.70 and 0.99)

Return ONLY valid JSON in this exact structure:
{{
  "detected_programs": [
    {{
      "program_number": 1,
      "title": "Largest of Three Numbers",
      "problem_statement": "Write a C program to find the largest of three numbers.",
      "topic": "Conditionals",
      "input_format": "Three integers separated by spaces",
      "output_format": "Largest = X",
      "constraints": "1 <= N <= 1000",
      "sample_input": "15 42 28",
      "sample_output": "Largest = 42",
      "reference_code": null,
      "confidence": 0.95
    }}
  ]
}}"""


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text from PDF bytes using pypdf.
    Detects if the PDF is scanned (empty text layer).
    """
    if not PYPDF_AVAILABLE:
        return {
            "success": False,
            "text": "",
            "total_pages": 0,
            "is_scanned": False,
            "error": "pypdf library not installed"
        }

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        full_text = []

        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            full_text.append(f"--- Page {i+1} ---\n{page_text}")

        combined_text = "\n".join(full_text).strip()
        cleaned_text = re.sub(r'\n{3,}', '\n\n', combined_text)

        # Scanned PDF detection heuristic: if less than 50 characters extracted total
        is_scanned = len(cleaned_text.replace("--- Page", "").strip()) < 50

        return {
            "success": True,
            "text": cleaned_text,
            "total_pages": total_pages,
            "is_scanned": is_scanned,
            "error": None
        }
    except Exception as e:
        logger.error(f"PDF Extraction error: {e}")
        return {
            "success": False,
            "text": "",
            "total_pages": 0,
            "is_scanned": False,
            "error": str(e)
        }


def fallback_heuristic_extraction(pdf_text: str) -> List[Dict[str, Any]]:
    """
    Regex fallback parser when Groq LLM is offline or unconfigured.
    Splits text on patterns like 'Program 1:', 'Experiment 1:', '1.', 'Problem 1'.
    """
    programs = []
    # Match patterns like Program 1:, Ex 1:, Experiment 1:, 1. Write a program
    pattern = re.compile(
        r'(?:Program|Experiment|Ex|Problem|Lab)\s*(\d+)[\:\.\s]+([^\n]+)|(?:\n|^)(\d+)[\.\)]\s*(Write[^\n]+)',
        re.IGNORECASE
    )

    matches = list(pattern.finditer(pdf_text))

    if not matches:
        # Fallback split by lines starting with 'Write a'
        lines = pdf_text.splitlines()
        prog_num = 1
        for line in lines:
            line_str = line.strip()
            if re.search(r'\bWrite\s+a\b', line_str, re.IGNORECASE):
                # Clean title
                title = re.sub(r'^.*?Write\s+a\s+(?:C\s+program\s+to\s+)?', '', line_str, flags=re.IGNORECASE)
                title = title.rstrip('.').capitalize()[:60] or f"Program {prog_num}"
                programs.append({
                    "program_number": prog_num,
                    "title": title,
                    "problem_statement": line_str,
                    "topic": "General C",
                    "input_format": "Standard C input",
                    "output_format": "Standard C output",
                    "constraints": None,
                    "sample_input": None,
                    "sample_output": None,
                    "reference_code": None,
                    "confidence": 0.82
                })
                prog_num += 1
        return programs

    for idx, match in enumerate(matches):
        p_num = match.group(1) or match.group(3) or str(idx + 1)
        p_title_raw = match.group(2) or match.group(4) or f"Program {p_num}"

        # Extract statement block until next match or 600 chars
        start_pos = match.start()
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else start_pos + 600
        block_text = pdf_text[start_pos:end_pos].strip()

        # Extract code snippet if present in block
        code_match = re.search(r'(#include\s*<stdio\.h>[\s\S]*?return\s+0;\s*\}|\{[\s\S]*?\})', block_text)
        ref_code = code_match.group(0) if code_match else None

        # Clean title
        clean_title = re.sub(r'^(?:Write\s+a\s+C\s+program\s+to\s+|to\s+)', '', p_title_raw, flags=re.IGNORECASE)
        clean_title = clean_title.strip(':. ').capitalize()[:60] or f"Program {p_num}"

        # Detect topic
        topic = "General C"
        if re.search(r'\barray|matrix|vector\b', block_text, re.IGNORECASE):
            topic = "Arrays"
        elif re.search(r'\bprime|fibonacci|factorial|loop|even|odd\b', block_text, re.IGNORECASE):
            topic = "Loops & Control Flow"
        elif re.search(r'\bpointer|address|swap\b', block_text, re.IGNORECASE):
            topic = "Pointers"
        elif re.search(r'\bstring|palindrome\b', block_text, re.IGNORECASE):
            topic = "Strings"

        try:
            num_val = int(p_num)
        except ValueError:
            num_val = idx + 1

        programs.append({
            "program_number": num_val,
            "title": clean_title,
            "problem_statement": block_text[:400],
            "topic": topic,
            "input_format": "Standard C input",
            "output_format": "Formatted console output",
            "constraints": None,
            "sample_input": None,
            "sample_output": None,
            "reference_code": ref_code,
            "confidence": 0.88
        })

    return programs


def extract_programs_from_manual_text(pdf_text: str) -> List[Dict[str, Any]]:
    """
    Sends extracted PDF text to Groq LLM to detect programming problems.
    Falls back to heuristic extraction if Groq is unavailable.
    """
    if not pdf_text.strip():
        return []

    # 1. Attempt Groq LLM Program Detection
    if _client:
        prompt = _EXTRACTION_PROMPT.format(manual_text=pdf_text[:4000]) # Limit prompt length for fast response
        for model_name in GROQ_MODELS:
            try:
                response = _client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1200,
                )
                raw_text = response.choices[0].message.content.strip()
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
                parsed = json.loads(raw_text)

                if isinstance(parsed, dict) and "detected_programs" in parsed and len(parsed["detected_programs"]) > 0:
                    return parsed["detected_programs"]
            except Exception as e:
                logger.warning(f"Groq manual extraction failed on model {model_name}: {e}")
                continue

    # 2. Fallback Heuristic Extraction
    return fallback_heuristic_extraction(pdf_text)
