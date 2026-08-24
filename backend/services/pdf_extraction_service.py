"""
PDF Parsing & AI Program Extraction Service
Handles robust multi-page text extraction from uploaded PDF manuals,
scanned PDF architecture detection, and AI-assisted detection of distinct
programming problems, problem statements, reference code, sample I/O, and concepts.
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

Analyze the following laboratory manual text extracted from a College C Programming Laboratory Manual PDF.

Laboratory Manual Content:
{manual_text}

Strict Instructions:
1. Identify and extract ALL distinct PROGRAMMING PROBLEMS / EXERCISES / LAB EXPERIMENTS meant for students to write code.
2. For each detected programming problem, extract:
   - program_number (Integer e.g. 1, 2, 3, 4...)
   - title (Clear concise title, e.g., "Quadratic Equation Roots", "Largest of Three Numbers", "Matrix Multiplication")
   - problem_statement (Full, clear problem statement describing what the student must implement)
   - topic (Core C topic e.g., "Conditionals", "Loops & Control Flow", "Arrays & Matrices", "Strings", "Functions & Recursion", "Pointers", "Structures & Unions", "File Handling")
   - input_format (Input requirements or null, e.g., "Three float coefficients a, b, c")
   - output_format (Expected output format or null, e.g., "Roots are real and distinct: root1 = X, root2 = Y")
   - constraints (Constraints if specified, or null)
   - sample_input (Example input string if provided, or null)
   - sample_output (Example output string if provided, or null)
   - reference_code (Complete or partial C reference code if present in the manual, or null)
   - confidence (Confidence score between 0.85 and 0.99)

3. Do NOT skip any exercises. Extract all programs present in the provided manual.
4. Return ONLY valid JSON in this exact structure without extra markdown or text:
{{
  "detected_programs": [
    {{
      "program_number": 1,
      "title": "Largest of Three Numbers",
      "problem_statement": "Write a C program to find the largest of three given numbers using conditional statements.",
      "topic": "Conditionals",
      "input_format": "Three space-separated integers",
      "output_format": "Largest = X",
      "constraints": null,
      "sample_input": "12 45 30",
      "sample_output": "Largest = 45",
      "reference_code": "#include <stdio.h>\\nint main() {\\n    int a, b, c;\\n    scanf(\\"%d %d %d\\", &a, &b, &c);\\n    int max = (a > b) ? ((a > c) ? a : c) : ((b > c) ? b : c);\\n    printf(\\"Largest = %d\\\\n\\", max);\\n    return 0;\\n}",
      "confidence": 0.96
    }}
  ]
}}"""


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text from PDF bytes using pypdf.
    Handles multi-page documents, cleans text layers, and detects scanned documents.
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
            page_clean = re.sub(r'[ \t]+', ' ', page_text)
            full_text.append(f"--- Page {i+1} ---\n{page_clean}")

        combined_text = "\n\n".join(full_text).strip()
        cleaned_text = re.sub(r'\n{4,}', '\n\n\n', combined_text)

        raw_char_count = len(re.sub(r'---\s*Page\s*\d+\s*---', '', cleaned_text).strip())
        is_scanned = raw_char_count < 60

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
    High-precision Regex Heuristic Parser for C Lab Manuals.
    Detects Programs, Experiments, Exercises, Aims, Objectives, Reference Codes, and Sample I/O.
    """
    programs = []

    # Match:
    # 1. Program 1:, Experiment 1:, Lab 1:, Ex 1:, Task 1:, Problem 1:, Week 1:
    # 2. 1. Title / 1) Title
    primary_pattern = re.compile(
        r'(?:^|\n)\s*(?:Program|Experiment|Lab|Ex|Exercise|Problem|Task|Assignment|Week|Session)\s*[-:]?\s*(\d+)[\:\.\-\s]+([^\n]+)|'
        r'(?:^|\n)\s*(\d+)[\.\)]\s*([A-Za-z][^\n]+)',
        re.IGNORECASE | re.MULTILINE
    )

    matches = list(primary_pattern.finditer(pdf_text))

    def detect_topic(text: str) -> str:
        t = text.lower()
        if any(w in t for w in ['matrix', 'matrices', '2d array', 'row', 'column']):
            return "2D Arrays & Matrices"
        elif any(w in t for w in ['array', 'bubble sort', 'linear search', 'binary search', 'insertion', 'deletion']):
            return "Arrays & Searching"
        elif any(w in t for w in ['string', 'palindrome', 'concat', 'reverse string', 'vowel', 'length']):
            return "Strings"
        elif any(w in t for w in ['pointer', 'address of', 'swap using pointer', 'call by reference']):
            return "Pointers"
        elif any(w in t for w in ['structure', 'struct', 'union', 'student record', 'employee']):
            return "Structures & Unions"
        elif any(w in t for w in ['file', 'fopen', 'fprintf', 'fscanf', 'file copy']):
            return "File Handling"
        elif any(w in t for w in ['recursion', 'recursive', 'fibonacci recursion', 'tower of hanoi', 'factorial recursion']):
            return "Recursion"
        elif any(w in t for w in ['function', 'modular', 'call by value']):
            return "Functions"
        elif any(w in t for w in ['prime', 'fibonacci', 'factorial', 'armstrong', 'loop', 'pattern', 'series', 'sum of digits']):
            return "Loops & Control Flow"
        elif any(w in t for w in ['quadratic', 'largest', 'leap year', 'switch', 'vowel or consonant', 'grade', 'if-else']):
            return "Conditionals"
        return "General C Programming"

    def extract_c_code(block: str) -> str | None:
        code_patterns = [
            r'(#include\s*<[\w\.]+>[\s\S]*?(?:return\s+\d+;|getch\(\);|return;|\})\s*\})',
            r'((?:int|void)\s+main\s*\([^\)]*\)\s*\{[\s\S]*?\n\})'
        ]
        for cp in code_patterns:
            m = re.search(cp, block)
            if m:
                return m.group(1).strip()
        return None

    def extract_io(block: str):
        sample_in, sample_out = None, None
        in_match = re.search(r'(?:Sample\s+)?(?:Input|Inputs|Enter\s+[^\n:]+)\s*[:=]\s*([^\n]+)', block, re.IGNORECASE)
        if in_match:
            sample_in = in_match.group(1).strip()

        out_match = re.search(r'(?:Sample\s+)?(?:Output|Expected\s+Output|Result)\s*[:=]\s*([^\n]+)', block, re.IGNORECASE)
        if out_match:
            sample_out = out_match.group(1).strip()
        return sample_in, sample_out

    if matches:
        for idx, match in enumerate(matches):
            p_num = match.group(1) or match.group(3) or str(idx + 1)
            raw_title = match.group(2) or match.group(4) or f"Program {p_num}"

            start_pos = match.start()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(pdf_text)
            block_text = pdf_text[start_pos:end_pos].strip()

            clean_title = re.sub(r'^(?:Aim|Objective|Title|Write\s+a\s+(?:C\s+)?program\s+(?:to\s+)?|To\s+write\s+(?:a\s+)?(?:C\s+)?program\s+(?:to\s+)?)\s*[:\-\.]*\s*', '', raw_title, flags=re.IGNORECASE).strip()
            clean_title = clean_title.rstrip('.:-').capitalize()[:70] or f"Lab Program {p_num}"

            stmt_match = re.search(r'(?:Aim|Objective|Problem\s+Statement)\s*[:\-\.]*\s*([^\n]+(?:\n[^\n#]+)?)', block_text, re.IGNORECASE)
            if stmt_match:
                prob_statement = stmt_match.group(1).strip()
            else:
                prob_statement = f"Write a C program to {clean_title.lower()}."

            ref_code = extract_c_code(block_text)
            sample_in, sample_out = extract_io(block_text)
            topic = detect_topic(block_text + " " + clean_title)

            try:
                num_val = int(p_num)
            except ValueError:
                num_val = idx + 1

            programs.append({
                "program_number": num_val,
                "title": clean_title,
                "problem_statement": prob_statement,
                "topic": topic,
                "input_format": f"Standard input for {topic.lower()}",
                "output_format": "Formatted console output",
                "constraints": None,
                "sample_input": sample_in,
                "sample_output": sample_out,
                "reference_code": ref_code,
                "confidence": 0.90
            })
    else:
        lines = pdf_text.splitlines()
        prog_num = 1
        current_block = []

        for line in lines:
            line_str = line.strip()
            if re.search(r'\b(?:Write\s+a\s+C\s+program|Aim\s*:|Objective\s*:)\b', line_str, re.IGNORECASE):
                if current_block and prog_num > 1:
                    block_content = "\n".join(current_block)
                    programs[-1]["reference_code"] = extract_c_code(block_content)
                    s_in, s_out = extract_io(block_content)
                    if s_in: programs[-1]["sample_input"] = s_in
                    if s_out: programs[-1]["sample_output"] = s_out

                current_block = [line_str]
                clean_title = re.sub(r'^.*?(?:Write\s+a\s+(?:C\s+)?program\s+(?:to\s+)?|Aim\s*:\s*|Objective\s*:\s*)', '', line_str, flags=re.IGNORECASE).strip()
                clean_title = clean_title.rstrip('.:-').capitalize()[:70] or f"Lab Program {prog_num}"

                programs.append({
                    "program_number": prog_num,
                    "title": clean_title,
                    "problem_statement": line_str,
                    "topic": detect_topic(line_str),
                    "input_format": "Standard input",
                    "output_format": "Console output",
                    "constraints": None,
                    "sample_input": None,
                    "sample_output": None,
                    "reference_code": None,
                    "confidence": 0.85
                })
                prog_num += 1
            else:
                current_block.append(line_str)

        if current_block and programs:
            block_content = "\n".join(current_block)
            programs[-1]["reference_code"] = extract_c_code(block_content)
            s_in, s_out = extract_io(block_content)
            if s_in: programs[-1]["sample_input"] = s_in
            if s_out: programs[-1]["sample_output"] = s_out

    return programs


def extract_programs_from_manual_text(pdf_text: str) -> List[Dict[str, Any]]:
    """
    Sends extracted PDF text to Groq LLM to detect programming problems.
    Falls back gracefully to high-precision heuristic extraction if Groq is unavailable.
    """
    if not pdf_text or not pdf_text.strip():
        return []

    # 1. Attempt Groq LLM Multi-Program Detection with extended context (up to 25,000 characters)
    if _client:
        sample_text = pdf_text[:25000]
        prompt = _EXTRACTION_PROMPT.format(manual_text=sample_text)
        for model_name in GROQ_MODELS:
            try:
                response = _client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.15,
                    max_tokens=3500,
                )
                raw_text = response.choices[0].message.content.strip()
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
                parsed = json.loads(raw_text)

                if isinstance(parsed, dict) and "detected_programs" in parsed and len(parsed["detected_programs"]) > 0:
                    logger.info(f"Groq successfully detected {len(parsed['detected_programs'])} programs using {model_name}.")
                    return parsed["detected_programs"]
            except Exception as e:
                logger.warning(f"Groq manual extraction failed on model {model_name}: {e}")
                continue

    # 2. Fallback Heuristic Extraction
    heuristic_results = fallback_heuristic_extraction(pdf_text)
    logger.info(f"Heuristic parser detected {len(heuristic_results)} programs from PDF text.")
    return heuristic_results
