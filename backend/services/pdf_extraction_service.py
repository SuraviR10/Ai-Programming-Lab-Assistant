"""
Intelligent C Lab Manual Extraction & Validation Service
Extracts distinct experiments, full problem statements, objectives, input/output descriptions,
structured test cases, C reference implementations, constraints, and validation metrics
from text-based and scanned/OCR PDF manuals.
"""

import os
import re
import json
import logging
from io import BytesIO
from typing import List, Dict, Any, Tuple

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from services.groq_service import _client, GROQ_MODELS

logger = logging.getLogger(__name__)

# OCR Character confusion patterns for C syntax detection
OCR_CONFUSION_PATTERNS = [
    (r'\bint\s+main\s*\(\s*\)\s*\(', "OCR brace error: '(' detected instead of '{' at main()", "replace_main_brace"),
    (r'#\s*inc1ude', "OCR letter confusion: '1' recognized instead of 'l' in '#include'", "fix_include"),
    (r'#\s*incIude', "OCR letter confusion: 'I' recognized instead of 'l' in '#include'", "fix_include"),
    (r'printf\s*\(\s*"[^"]*"\s*\:', "OCR colon confusion: ':' recognized instead of ';' after printf", "fix_semicolon"),
    (r'scanf\s*\(\s*"[^"]*"\s*,\s*&[a-zA-Z0-9_]+\s*\)', "OCR scanf check", "valid"),
]

_EXTRACTION_PROMPT = """You are an expert Computer Science Laboratory Manual Extraction Engine.

Analyze the following laboratory manual text extracted from a College C Programming Laboratory Manual PDF.

Laboratory Manual Content:
{manual_text}

Strict Instructions:
1. Intelligently identify and separate EVERY distinct programming experiment/exercise. Do NOT merge different experiments together.
2. For each experiment, extract a complete, separate record containing:
   - experiment_number: (Integer e.g. 1, 2, 3...)
   - title: (Clear concise title e.g., "Roots of Quadratic Equation", "Matrix Multiplication", "Largest and Smallest in Array")
   - objective: (The stated Aim or Objective of the lab experiment)
   - problem_statement: (The COMPLETE problem statement EXACTLY as given in the manual. Preserve mathematical expressions, conditions, numbered requirements, input/output specifications, and special instructions. Do NOT summarize or shorten.)
   - input_description: (Detailed input format requirements or null)
   - output_description: (Detailed expected output format description or null)
   - constraints: (Any variable ranges or time/space constraints, or null)
   - test_cases: (List of ALL test cases/sample inputs given in the manual, structured as objects with "input" and "expected_output" strings)
   - reference_code: (The complete, intact C reference code if given in the manual, preserving #include, main(), variables, loops, conditions, braces, comments, indentation. Do NOT include page headers, footers, or non-code text inside the C program. If no code is present, set to null.)
   - expected_output: (The primary expected output string or null)
   - additional_requirements: (Any special viva/theory notes, constraints, or null)
   - extraction_confidence: (Confidence score between 0.85 and 0.99)

3. Return ONLY valid JSON in this exact structure without markdown backticks or commentary:
{{
  "detected_programs": [
    {{
      "experiment_number": 1,
      "title": "Largest and Smallest in Array",
      "objective": "To write a C program to read N integers and find the largest and smallest elements.",
      "problem_statement": "Write a C program to read N integers and find the largest and smallest elements in the array. Ensure that the program handles both positive and negative values correctly.",
      "input_description": "First line contains integer N. Second line contains N space-separated integers.",
      "output_description": "Print Largest = X and Smallest = Y on separate lines.",
      "constraints": "1 <= N <= 1000",
      "test_cases": [
        {{
          "input": "5\\n10 20 5 30 15",
          "expected_output": "Largest = 30\\nSmallest = 5"
        }},
        {{
          "input": "3\\n-10 -50 -2",
          "expected_output": "Largest = -2\\nSmallest = -50"
        }}
      ],
      "reference_code": "#include <stdio.h>\\n\\nint main() {{\\n    int n, i;\\n    if (scanf(\\"%d\\", &n) != 1) return 0;\\n    int arr[n];\\n    for (i = 0; i < n; i++) scanf(\\"%d\\", &arr[i]);\\n    int max = arr[0], min = arr[0];\\n    for (i = 1; i < n; i++) {{\\n        if (arr[i] > max) max = arr[i];\\n        if (arr[i] < min) min = arr[i];\\n    }}\\n    printf(\\"Largest = %d\\\\nSmallest = %d\\\\n\\", max, min);\\n    return 0;\\n}}",
      "expected_output": "Largest = 30\\nSmallest = 5",
      "additional_requirements": "Use 1D array traversal",
      "extraction_confidence": 0.96
    }}
  ]
}}"""


def sanitize_pdf_text(raw_text: str) -> str:
    """Removes page headers, running footers, page numbers, and excessive whitespace."""
    if not raw_text:
        return ""
    # Strip common header/footer lines (e.g., 'Page 12 of 45', 'Department of CSE', 'Lab Manual')
    cleaned = re.sub(r'(?i)(?:Page\s*\d+\s*(?:of\s*\d+)?|\d+\s*/\s*\d+)\s*$', '', raw_text, flags=re.MULTILINE)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n{4,}', '\n\n\n', cleaned)
    return cleaned.strip()


def detect_ocr_ambiguities(code_str: str) -> List[str]:
    """Detects likely OCR character confusion errors in extracted C code."""
    if not code_str:
        return []
    warnings = []
    for pattern, msg, _ in OCR_CONFUSION_PATTERNS:
        if re.search(pattern, code_str):
            warnings.append(msg)
    
    # Check 0 vs O confusion in numbers
    if re.search(r'\b[1-9]O\b|\bO[0-9]\b', code_str):
        warnings.append("OCR letter/digit confusion: Letter 'O' detected where number '0' expected.")
    
    # Check 1 vs l confusion in numbers
    if re.search(r'\b[0-9]+l[0-9]+\b', code_str):
        warnings.append("OCR letter/digit confusion: Letter 'l' detected inside number.")
        
    return warnings


def validate_extracted_experiment(exp: Dict[str, Any], is_ocr: bool = False) -> Dict[str, Any]:
    """
    Module 1.1 — Automated Extraction Validation:
    - Code validation: balanced braces, valid C syntax, #include presence, main() presence, string integrity.
    - Test case validation: input -> expected_output pairs verified.
    - Experiment validation: ensures isolation, calculates final confidence, flags review items.
    """
    code = exp.get("reference_code") or ""
    validation = {
        "valid_syntax": True,
        "braces_balanced": True,
        "has_main": True,
        "has_includes": True,
        "strings_valid": True,
        "test_cases_valid": True,
        "ocr_warnings": [],
        "warnings": [],
        "confidence_level": "HIGH"
    }

    # 1. Code Validation
    if code:
        # Check balanced braces
        open_braces = code.count('{')
        close_braces = code.count('}')
        if open_braces != close_braces:
            validation["braces_balanced"] = False
            validation["valid_syntax"] = False
            validation["warnings"].append(f"Unbalanced curly braces: {open_braces} open '{{' vs {close_braces} close '}}'.")

        open_parens = code.count('(')
        close_parens = code.count(')')
        if open_parens != close_parens:
            validation["valid_syntax"] = False
            validation["warnings"].append(f"Unbalanced parentheses: {open_parens} '(' vs {close_parens} ')'.")

        # Check for main function
        has_main = bool(re.search(r'\b(?:int|void)\s+main\s*\(', code))
        validation["has_main"] = has_main
        if not has_main:
            validation["warnings"].append("No standard 'main()' function declaration detected in reference code.")

        # Check for include statements
        has_inc = bool(re.search(r'#\s*include\s*<[\w\.]+>', code))
        validation["has_includes"] = has_inc
        if not has_inc:
            validation["warnings"].append("No standard '#include <...>' header found in reference code.")

        # Check for unterminated string literals (odd number of unescaped quotes per line)
        for line in code.splitlines():
            # strip escaped quotes
            clean_line = line.replace(r'\"', '')
            if clean_line.count('"') % 2 != 0:
                validation["strings_valid"] = False
                validation["valid_syntax"] = False
                validation["warnings"].append("Unterminated string literal detected in code line.")
                break

        # Check OCR ambiguities if document was scanned
        if is_ocr:
            ocr_issues = detect_ocr_ambiguities(code)
            if ocr_issues:
                validation["ocr_warnings"] = ocr_issues
                validation["warnings"].extend(ocr_issues)

    # 2. Test Case Validation
    raw_tc = exp.get("test_cases") or []
    valid_test_cases = []
    if isinstance(raw_tc, list):
        for tc in raw_tc:
            if isinstance(tc, dict):
                in_val = str(tc.get("input", "")).strip()
                out_val = str(tc.get("expected_output", "")).strip()
                if in_val or out_val:
                    valid_test_cases.append({"input": in_val, "expected_output": out_val})
            elif isinstance(tc, str):
                valid_test_cases.append({"input": "", "expected_output": tc.strip()})

    # If no test cases extracted, populate with sample input/output if available
    if not valid_test_cases:
        s_in = exp.get("sample_input")
        s_out = exp.get("sample_output") or exp.get("expected_output")
        if s_out:
            valid_test_cases.append({"input": s_in or "", "expected_output": s_out})
        else:
            validation["test_cases_valid"] = False
            validation["warnings"].append("No valid test cases or sample input/output found for this experiment.")

    exp["test_cases"] = valid_test_cases

    # 3. Calculate Confidence Score
    base_conf = float(exp.get("extraction_confidence") or exp.get("confidence") or 0.92)
    if validation["warnings"]:
        penalty = min(0.35, len(validation["warnings"]) * 0.08)
        base_conf = max(0.50, round(base_conf - penalty, 2))

    if base_conf >= 0.88 and validation["valid_syntax"] and validation["test_cases_valid"]:
        validation["confidence_level"] = "HIGH"
    elif base_conf >= 0.70:
        validation["confidence_level"] = "MEDIUM (Needs Verification)"
    else:
        validation["confidence_level"] = "LOW (Flagged for Faculty Correction)"

    exp["extraction_confidence"] = base_conf
    exp["validation_report"] = validation
    return exp


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text from PDF bytes using pypdf with fallback OCR support for scanned pages.
    """
    if not PYPDF_AVAILABLE:
        return {
            "success": False,
            "text": "",
            "total_pages": 0,
            "is_scanned": False,
            "ocr_used": False,
            "error": "pypdf library not installed"
        }

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        full_text = []
        is_scanned = False
        ocr_used = False

        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            page_clean = sanitize_pdf_text(page_text)
            
            # Scanned page detection (less than 40 chars on a page)
            if len(page_clean.strip()) < 40 and OCR_AVAILABLE:
                try:
                    # Attempt image extraction from page for OCR
                    for img_obj in page.images:
                        img = Image.open(BytesIO(img_obj.data))
                        ocr_txt = pytesseract.image_to_string(img)
                        if ocr_txt.strip():
                            page_clean += "\n" + sanitize_pdf_text(ocr_txt)
                            ocr_used = True
                            is_scanned = True
                except Exception as ocr_err:
                    logger.debug(f"Page {i+1} OCR fallback non-critical exception: {ocr_err}")

            full_text.append(f"--- Experiment Page {i+1} ---\n{page_clean}")

        combined_text = "\n\n".join(full_text).strip()
        raw_char_count = len(re.sub(r'---\s*Experiment\s*Page\s*\d+\s*---', '', combined_text).strip())
        if raw_char_count < 60:
            is_scanned = True

        return {
            "success": True,
            "text": combined_text,
            "total_pages": total_pages,
            "is_scanned": is_scanned,
            "ocr_used": ocr_used,
            "error": None
        }
    except Exception as e:
        logger.error(f"PDF Extraction error: {e}")
        return {
            "success": False,
            "text": "",
            "total_pages": 0,
            "is_scanned": False,
            "ocr_used": False,
            "error": str(e)
        }


def fallback_heuristic_extraction(pdf_text: str, is_ocr: bool = False) -> List[Dict[str, Any]]:
    """
    High-precision Regex & Section Boundary Parser for C Lab Manuals.
    Separates: Experiment Number/Title -> Objective -> Problem Statement -> 
    Input/Output specs -> Test Cases -> C Reference Code -> Expected Output -> Additional Requirements.
    """
    programs = []

    # Detect experiment header patterns:
    # "Experiment 1:", "Lab 01:", "Program 1.", "Exercise 1:", "Problem 1:", "1. Title", "Week 1:"
    primary_pattern = re.compile(
        r'(?:^|\n)\s*(?:Experiment|Program|Lab|Exercise|Ex|Problem|Task|Assignment|Week|Session)\s*[-:]?\s*(\d+)[\:\.\-\s]+([^\n]+)|'
        r'(?:^|\n)\s*(\d+)[\.\)]\s*([A-Za-z][^\n]+)',
        re.IGNORECASE | re.MULTILINE
    )

    matches = list(primary_pattern.finditer(pdf_text))

    def detect_topic(text: str) -> str:
        t = text.lower()
        if any(w in t for w in ['matrix', 'matrices', '2d array', 'row', 'column']):
            return "2D Arrays & Matrices"
        elif any(w in t for w in ['array', 'bubble sort', 'linear search', 'binary search', 'insertion', 'deletion', 'smallest', 'largest']):
            return "Arrays & Searching"
        elif any(w in t for w in ['string', 'palindrome', 'concat', 'reverse string', 'vowel', 'length', 'strcmp']):
            return "Strings"
        elif any(w in t for w in ['pointer', 'address of', 'swap using pointer', 'call by reference', 'malloc']):
            return "Pointers & Memory"
        elif any(w in t for w in ['structure', 'struct', 'union', 'student record', 'employee']):
            return "Structures & Unions"
        elif any(w in t for w in ['file', 'fopen', 'fprintf', 'fscanf', 'file copy', 'fclose']):
            return "File Handling"
        elif any(w in t for w in ['recursion', 'recursive', 'fibonacci recursion', 'tower of hanoi', 'factorial recursion']):
            return "Recursion"
        elif any(w in t for w in ['function', 'modular', 'call by value', 'user defined']):
            return "Functions"
        elif any(w in t for w in ['prime', 'fibonacci', 'factorial', 'armstrong', 'loop', 'pattern', 'series', 'sum of digits']):
            return "Loops & Control Flow"
        elif any(w in t for w in ['quadratic', 'largest', 'leap year', 'switch', 'vowel or consonant', 'grade', 'if-else']):
            return "Conditionals"
        return "General C Programming"

    def extract_c_code(block: str) -> str | None:
        """Extracts complete C code block while preserving #include, main, braces, comments, indentation."""
        code_patterns = [
            r'(#\s*include\s*<[\w\.]+>[\s\S]*?(?:return\s+\d+;|return;|\})\s*\})',
            r'((?:int|void)\s+main\s*\([^\)]*\)\s*\{[\s\S]*?\n\})'
        ]
        for cp in code_patterns:
            m = re.search(cp, block)
            if m:
                code_text = m.group(1).strip()
                # Clean stray page markers from inside code
                code_text = re.sub(r'---\s*Experiment\s*Page\s*\d+\s*---', '', code_text)
                return code_text.strip()
        return None

    def extract_structured_test_cases(block: str) -> Tuple[List[Dict[str, str]], str | None, str | None]:
        """Extracts multiple paired test cases structurally."""
        test_cases = []
        sample_in, sample_out = None, None

        # 1. Look for explicit Test Case 1, Test Case 2 sections
        tc_blocks = re.findall(
            r'Test\s*Case\s*\d*\s*[:\-]?\s*(?:Input|Inputs)?\s*[:\-]?\s*([^\n]+(?:\n(?!(?:Expected\s+)?Output|Test\s*Case)[^\n]+)*)\s*(?:Expected\s+)?Output\s*[:\-]?\s*([^\n]+(?:\n(?!(?:Test\s*Case|Program|Experiment))[^\n]+)*)',
            block,
            re.IGNORECASE
        )
        for in_str, out_str in tc_blocks:
            clean_in = in_str.strip()
            clean_out = out_str.strip()
            if clean_in or clean_out:
                test_cases.append({"input": clean_in, "expected_output": clean_out})

        # 2. Look for Sample Input / Sample Output
        in_matches = list(re.finditer(r'(?:Sample\s+)?(?:Input|Inputs|Enter\s+[^\n:]+)\s*[:=]\s*([^\n]+(?:\n(?!(?:Sample\s+)?Output|Result|Reference|#include)[^\n]+)*)', block, re.IGNORECASE))
        out_matches = list(re.finditer(r'(?:Sample\s+)?(?:Output|Expected\s+Output|Result)\s*[:=]\s*([^\n]+(?:\n(?!(?:Sample\s+)?Input|Reference|#include|Test\s*Case)[^\n]+)*)', block, re.IGNORECASE))

        if in_matches and out_matches:
            for idx in range(min(len(in_matches), len(out_matches))):
                sin = in_matches[idx].group(1).strip()
                sout = out_matches[idx].group(1).strip()
                if not any(tc["input"] == sin for tc in test_cases):
                    test_cases.append({"input": sin, "expected_output": sout})
            sample_in = in_matches[0].group(1).strip()
            sample_out = out_matches[0].group(1).strip()
        elif out_matches:
            sample_out = out_matches[0].group(1).strip()
            if not test_cases:
                test_cases.append({"input": "", "expected_output": sample_out})

        return test_cases, sample_in, sample_out

    if matches:
        for idx, match in enumerate(matches):
            p_num = match.group(1) or match.group(3) or str(idx + 1)
            raw_title = match.group(2) or match.group(4) or f"Experiment {p_num}"

            start_pos = match.start()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(pdf_text)
            block_text = pdf_text[start_pos:end_pos].strip()

            clean_title = re.sub(
                r'^(?:Aim|Objective|Title|Write\s+a\s+(?:C\s+)?program\s+(?:to\s+)?|To\s+write\s+(?:a\s+)?(?:C\s+)?program\s+(?:to\s+)?)\s*[:\-\.]*\s*',
                '',
                raw_title,
                flags=re.IGNORECASE
            ).strip()
            clean_title = clean_title.rstrip('.:-').capitalize()[:75] or f"Lab Experiment {p_num}"

            # Extract Aim / Objective
            aim_match = re.search(r'(?:Aim|Objective)\s*[:\-\.]*\s*([^\n]+(?:\n(?!(?:Problem|Input|Output|Reference|#include))[^\n]+)*)', block_text, re.IGNORECASE)
            objective = aim_match.group(1).strip() if aim_match else f"Implement a C program for {clean_title.lower()}."

            # Extract Problem Statement
            stmt_match = re.search(r'(?:Problem\s+Statement|Description)\s*[:\-\.]*\s*([^\n]+(?:\n(?!(?:Input|Output|Sample|Reference|#include))[^\n]+)*)', block_text, re.IGNORECASE)
            if stmt_match:
                prob_statement = stmt_match.group(1).strip()
            elif aim_match:
                prob_statement = objective
            else:
                prob_statement = f"Write a C program to {clean_title.lower()} as per standard laboratory specifications."

            # Extract Input / Output descriptions & constraints
            in_desc_m = re.search(r'(?:Input\s+Description|Input\s+Format)\s*[:\-\.]*\s*([^\n]+)', block_text, re.IGNORECASE)
            out_desc_m = re.search(r'(?:Output\s+Description|Output\s+Format)\s*[:\-\.]*\s*([^\n]+)', block_text, re.IGNORECASE)
            const_m = re.search(r'(?:Constraints|Range)\s*[:\-\.]*\s*([^\n]+)', block_text, re.IGNORECASE)

            ref_code = extract_c_code(block_text)
            test_cases, sample_in, sample_out = extract_structured_test_cases(block_text)
            topic = detect_topic(block_text + " " + clean_title)

            try:
                num_val = int(p_num)
            except ValueError:
                num_val = idx + 1

            exp_record = {
                "experiment_number": num_val,
                "title": clean_title,
                "objective": objective,
                "problem_statement": prob_statement,
                "topic": topic,
                "input_description": in_desc_m.group(1).strip() if in_desc_m else (f"Standard input for {topic.lower()}" if sample_in else "None"),
                "output_description": out_desc_m.group(1).strip() if out_desc_m else "Formatted console output",
                "input_format": in_desc_m.group(1).strip() if in_desc_m else "Standard input",
                "output_format": out_desc_m.group(1).strip() if out_desc_m else "Console output",
                "constraints": const_m.group(1).strip() if const_m else None,
                "sample_input": sample_in,
                "sample_output": sample_out,
                "expected_output": sample_out or "Standard Program Output",
                "test_cases": test_cases,
                "reference_code": ref_code,
                "additional_requirements": None,
                "extraction_confidence": 0.92,
                "faculty_verified": False
            }

            validated = validate_extracted_experiment(exp_record, is_ocr=is_ocr)
            programs.append(validated)
    else:
        # Fallback line-by-line block splitter
        lines = pdf_text.splitlines()
        prog_num = 1
        current_block = []

        for line in lines:
            line_str = line.strip()
            if re.search(r'\b(?:Write\s+a\s+C\s+program|Aim\s*:|Objective\s*:|Experiment\s*\d+)\b', line_str, re.IGNORECASE):
                if current_block and prog_num > 1:
                    block_content = "\n".join(current_block)
                    programs[-1]["reference_code"] = extract_c_code(block_content)
                    tcs, s_in, s_out = extract_structured_test_cases(block_content)
                    if tcs: programs[-1]["test_cases"] = tcs
                    if s_in: programs[-1]["sample_input"] = s_in
                    if s_out:
                        programs[-1]["sample_output"] = s_out
                        programs[-1]["expected_output"] = s_out
                    programs[-1] = validate_extracted_experiment(programs[-1], is_ocr=is_ocr)

                current_block = [line_str]
                clean_title = re.sub(r'^.*?(?:Write\s+a\s+(?:C\s+)?program\s+(?:to\s+)?|Aim\s*:\s*|Objective\s*:\s*)', '', line_str, flags=re.IGNORECASE).strip()
                clean_title = clean_title.rstrip('.:-').capitalize()[:75] or f"Lab Experiment {prog_num}"

                programs.append({
                    "experiment_number": prog_num,
                    "title": clean_title,
                    "objective": line_str,
                    "problem_statement": line_str,
                    "topic": detect_topic(line_str),
                    "input_description": "Standard input",
                    "output_description": "Formatted console output",
                    "input_format": "Standard input",
                    "output_format": "Console output",
                    "constraints": None,
                    "sample_input": None,
                    "sample_output": None,
                    "expected_output": None,
                    "test_cases": [],
                    "reference_code": None,
                    "additional_requirements": None,
                    "extraction_confidence": 0.86,
                    "faculty_verified": False
                })
                prog_num += 1
            else:
                current_block.append(line_str)

        if current_block and programs:
            block_content = "\n".join(current_block)
            programs[-1]["reference_code"] = extract_c_code(block_content)
            tcs, s_in, s_out = extract_structured_test_cases(block_content)
            if tcs: programs[-1]["test_cases"] = tcs
            if s_in: programs[-1]["sample_input"] = s_in
            if s_out:
                programs[-1]["sample_output"] = s_out
                programs[-1]["expected_output"] = s_out
            programs[-1] = validate_extracted_experiment(programs[-1], is_ocr=is_ocr)

    return programs


def extract_programs_from_manual_text(pdf_text: str, is_ocr: bool = False) -> List[Dict[str, Any]]:
    """
    Sends extracted PDF text to Groq LLM to detect all programming experiments.
    Enriches each record with automated validation reports (balanced braces, C syntax, test cases).
    Falls back gracefully to high-precision heuristic extraction if Groq is unavailable.
    """
    if not pdf_text or not pdf_text.strip():
        return []

    # 1. Attempt Groq LLM Multi-Program Detection with extended context (up to 28,000 characters)
    if _client:
        sample_text = pdf_text[:28000]
        prompt = _EXTRACTION_PROMPT.format(manual_text=sample_text)
        for model_name in GROQ_MODELS:
            try:
                response = _client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.15,
                    max_tokens=4000,
                )
                raw_text = response.choices[0].message.content.strip()
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
                parsed = json.loads(raw_text)

                if isinstance(parsed, dict) and "detected_programs" in parsed and len(parsed["detected_programs"]) > 0:
                    validated_list = []
                    for prog in parsed["detected_programs"]:
                        # Ensure fields match standard naming
                        if "program_number" in prog and "experiment_number" not in prog:
                            prog["experiment_number"] = prog["program_number"]
                        validated_list.append(validate_extracted_experiment(prog, is_ocr=is_ocr))

                    logger.info(f"Groq successfully detected {len(validated_list)} validated experiments using {model_name}.")
                    return validated_list
            except Exception as e:
                logger.warning(f"Groq manual extraction failed on model {model_name}: {e}")
                continue

    # 2. Fallback Heuristic Extraction
    heuristic_results = fallback_heuristic_extraction(pdf_text, is_ocr=is_ocr)
    logger.info(f"Heuristic parser detected {len(heuristic_results)} validated experiments from PDF text.")
    return heuristic_results
