"""
Code Integrity & Structural Similarity Analysis Service
Performs structural C code normalization, AST/token-level canonicalization,
and pairwise similarity analysis (resilient to variable renaming, whitespace modification, and comment alteration).
"""

import re
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from database import SessionLocal, Submission, Problem, ManualProgram, CodeSimilarityAnalysis, User

# Standard C reserved keywords and standard I/O library identifiers to preserve
C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "int", "long", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while",
    "main", "printf", "scanf", "getchar", "putchar", "gets", "puts", "fgets", "fputs",
    "malloc", "calloc", "realloc", "free", "exit", "strlen", "strcpy", "strcmp",
    "strcat", "abs", "sqrt", "pow", "NULL", "include", "define", "stdio", "stdlib", "string", "math"
}


def strip_c_comments(code: str) -> str:
    """Removes both single-line (//) and multi-line (/* */) comments from C source code."""
    if not code:
        return ""
    # Remove multi-line comments
    code = re.sub(r'/\*[\s\S]*?\*/', '', code)
    # Remove single-line comments
    code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
    return code


def canonicalize_c_code(code: str) -> Tuple[str, List[str]]:
    """
    Normalizes C code structurally:
    1. Strips comments and preprocessor lines (#include, #define)
    2. Replaces string literals with '__STR__' and characters with '__CHR__'
    3. Replaces numeric constants with '__NUM__'
    4. Canonicalizes identifier names ($v0, $v1, $v2...) while preserving C keywords
    5. Normalizes whitespace and structure into a linear token stream.
    
    Returns (normalized_code_string, token_list).
    """
    clean_code = strip_c_comments(code)
    
    # Strip preprocessor directives (#include, #define) so boilerplate header imports don't skew similarity
    clean_code = re.sub(r'#\s*(?:include|define|pragma|ifdef|ifndef|endif)\b[^\n]*', '', clean_code)
    
    # Normalize string and char literals
    clean_code = re.sub(r'"(\\.|[^"\\])*"', ' __STR__ ', clean_code)
    clean_code = re.sub(r"'(\\.|[^'\\])*'", ' __CHR__ ', clean_code)
    
    # Tokenize words, operators, numbers, and delimiters
    raw_tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*|\d+(?:\.\d+)?|==|!=|<=|>=|&&|\|\||\+\+|--|->|[+\-*/%=<>&|!~^?:;,(){}\[\]]', clean_code)
    
    canonical_tokens = []
    identifier_map: Dict[str, str] = {}
    id_counter = 0
    
    for tok in raw_tokens:
        if tok in C_KEYWORDS:
            canonical_tokens.append(tok)
        elif re.match(r'^\d+(?:\.\d+)?$', tok):
            canonical_tokens.append("__NUM__")
        elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', tok):
            # User-defined identifier/variable: map to canonical placeholder
            if tok not in identifier_map:
                identifier_map[tok] = f"$v{id_counter}"
                id_counter += 1
            canonical_tokens.append(identifier_map[tok])
        else:
            # Operators / punctuation
            canonical_tokens.append(tok)
            
    normalized_str = " ".join(canonical_tokens)
    return normalized_str, canonical_tokens


def calculate_jaccard_token_similarity(tokens1: List[str], tokens2: List[str], n: int = 3) -> float:
    """Calculates n-gram token Jaccard similarity between two token streams."""
    if not tokens1 or not tokens2:
        return 0.0
    
    if len(tokens1) < n or len(tokens2) < n:
        set1, set2 = set(tokens1), set(tokens2)
    else:
        set1 = set(tuple(tokens1[i:i+n]) for i in range(len(tokens1) - n + 1))
        set2 = set(tuple(tokens2[i:i+n]) for i in range(len(tokens2) - n + 1))
        
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return round((intersection / max(1, union)), 4)


def calculate_structural_lcs_similarity(s1: str, s2: str) -> float:
    """Calculates Longest Common Subsequence ratio between two normalized code strings."""
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    
    from difflib import SequenceMatcher
    matcher = SequenceMatcher(None, s1, s2)
    return round(matcher.ratio(), 4)


def compute_code_similarity_score(code_a: str, code_b: str) -> Dict[str, Any]:
    """
    Computes comprehensive structural similarity between two C programs:
    - Normalizes identifiers (defeats variable renaming)
    - Normalizes comments, strings, numbers, whitespaces
    - Computes 3-gram and 4-gram token Jaccard similarity & structural LCS similarity
    - Returns overall similarity percentage (0-100%) and matched structural fragments.
    """
    norm_a, tokens_a = canonicalize_c_code(code_a)
    norm_b, tokens_b = canonicalize_c_code(code_b)
    
    if not norm_a or not norm_b:
        return {
            "similarity_percentage": 0.0,
            "structural_similarity": 0.0,
            "token_similarity": 0.0,
            "normalized_code_a": norm_a,
            "normalized_code_b": norm_b,
            "matched_patterns": []
        }
        
    token_sim_3 = calculate_jaccard_token_similarity(tokens_a, tokens_b, n=3)
    token_sim_4 = calculate_jaccard_token_similarity(tokens_a, tokens_b, n=4)
    avg_token_sim = (token_sim_3 + token_sim_4) / 2.0
    lcs_sim = calculate_structural_lcs_similarity(norm_a, norm_b)
    
    # If normalized tokens match identically, similarity is 100%
    if norm_a == norm_b:
        composite_score = 1.0
    else:
        composite_score = (0.50 * lcs_sim) + (0.50 * avg_token_sim)
        
    similarity_pct = round(composite_score * 100, 1)
    
    # Extract matched common sub-blocks
    from difflib import SequenceMatcher
    matcher = SequenceMatcher(None, tokens_a, tokens_b)
    matched_blocks = []
    for match in matcher.get_matching_blocks():
        if match.size >= 4: # 4 or more continuous canonical tokens
            fragment = " ".join(tokens_a[match.a:match.a + match.size])
            if fragment not in matched_blocks:
                matched_blocks.append(fragment[:120])
                
    return {
        "similarity_percentage": min(100.0, max(0.0, similarity_pct)),
        "structural_similarity": round(lcs_sim, 3),
        "token_similarity": round(avg_token_sim, 3),
        "normalized_code_a": norm_a,
        "normalized_code_b": norm_b,
        "matched_patterns": matched_blocks[:10]
    }


def analyze_and_store_submission_integrity(
    student_id: str,
    problem_id: int,
    submitted_code: str,
    submission_id: int | None = None,
    exam_id: int | None = None,
    flag_threshold: float = 75.0,
    db: Session | None = None
) -> List[Dict[str, Any]]:
    """
    Compares the current student submission against:
    1. Other student submissions for this problem (and exam)
    2. The lab manual / problem reference code
    
    Stores high-similarity results in the database and returns the similarity analysis findings.
    """
    close_db_after = False
    if db is None:
        db = SessionLocal()
        close_db_after = True
        
    reports = []
    try:
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        
        # 1. Compare against Problem Reference Code if present
        ref_code = None
        if problem and problem.starter_code and "Write your solution" not in problem.starter_code:
            ref_code = problem.starter_code
            
        # Check ManualProgram reference code
        manual_prog = db.query(ManualProgram).filter(ManualProgram.title == (problem.title if problem else "")).first()
        if manual_prog and manual_prog.reference_code:
            ref_code = manual_prog.reference_code
            
        if ref_code and submitted_code.strip():
            ref_sim = compute_code_similarity_score(submitted_code, ref_code)
            if ref_sim["similarity_percentage"] >= 60.0:
                is_flagged = ref_sim["similarity_percentage"] >= flag_threshold
                sim_record = CodeSimilarityAnalysis(
                    exam_id=exam_id,
                    problem_id=problem_id,
                    student_id_1=student_id,
                    student_id_2="REFERENCE_CODE",
                    submission_id_1=submission_id,
                    submission_id_2=None,
                    similarity_percentage=ref_sim["similarity_percentage"],
                    structural_similarity=ref_sim["structural_similarity"],
                    token_similarity=ref_sim["token_similarity"],
                    matched_patterns=json.dumps(ref_sim["matched_patterns"]),
                    normalized_code_1=ref_sim["normalized_code_a"],
                    normalized_code_2=ref_sim["normalized_code_b"],
                    is_flagged=is_flagged,
                    faculty_reviewed=False,
                    review_status="flagged" if is_flagged else "pending",
                    review_notes=f"Structural match with Faculty Reference Code: {ref_sim['similarity_percentage']}% similarity."
                )
                db.add(sim_record)
                reports.append({
                    "target": "Faculty Reference Solution",
                    "student_id": "REFERENCE_CODE",
                    "similarity_percentage": ref_sim["similarity_percentage"],
                    "structural_similarity": ref_sim["structural_similarity"],
                    "is_flagged": is_flagged,
                    "matched_patterns": ref_sim["matched_patterns"]
                })

        # 2. Compare against Other Student Submissions for this problem
        other_subs_query = db.query(Submission).filter(
            Submission.problem_id == problem_id,
            Submission.student_id != student_id
        )
        if exam_id:
            other_subs_query = other_subs_query.filter(Submission.mode == "exam")
            
        other_submissions = other_subs_query.order_by(Submission.timestamp.desc()).limit(25).all()
        
        seen_students = set()
        for other in other_submissions:
            if other.student_id in seen_students or not other.code.strip():
                continue
            seen_students.add(other.student_id)
            
            sim_res = compute_code_similarity_score(submitted_code, other.code)
            if sim_res["similarity_percentage"] >= 65.0:
                is_flagged = sim_res["similarity_percentage"] >= flag_threshold
                
                # Retrieve student 2 name
                st2 = db.query(User).filter(User.user_id == other.student_id).first()
                st2_name = st2.full_name if st2 else other.student_id
                
                sim_entry = CodeSimilarityAnalysis(
                    exam_id=exam_id,
                    problem_id=problem_id,
                    student_id_1=student_id,
                    student_id_2=other.student_id,
                    submission_id_1=submission_id,
                    submission_id_2=other.id,
                    similarity_percentage=sim_res["similarity_percentage"],
                    structural_similarity=sim_res["structural_similarity"],
                    token_similarity=sim_res["token_similarity"],
                    matched_patterns=json.dumps(sim_res["matched_patterns"]),
                    normalized_code_1=sim_res["normalized_code_a"],
                    normalized_code_2=sim_res["normalized_code_b"],
                    is_flagged=is_flagged,
                    faculty_reviewed=False,
                    review_status="flagged" if is_flagged else "pending",
                    review_notes=f"Pairwise structural code similarity: {sim_res['similarity_percentage']}%."
                )
                db.add(sim_entry)
                reports.append({
                    "target": f"Student {other.student_id} ({st2_name})",
                    "student_id": other.student_id,
                    "student_name": st2_name,
                    "submission_id": other.id,
                    "similarity_percentage": sim_res["similarity_percentage"],
                    "structural_similarity": sim_res["structural_similarity"],
                    "is_flagged": is_flagged,
                    "matched_patterns": sim_res["matched_patterns"]
                })
                
        db.commit()
    except Exception as e:
        logger.error(f"Code similarity analysis error: {e}")
    finally:
        if close_db_after:
            db.close()
            
    return reports
