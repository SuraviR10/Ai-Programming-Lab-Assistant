"""
Evaluation Service
Executes C code against problem test cases, evaluates correctness, scores submissions,
performs static AST/hardcoding analysis, calls Groq semantic analysis,
awards XP/creativity recognition, and records submission analysis telemetry.
"""

import re
import json
from datetime import datetime, timezone
from database import SessionLocal, Problem, TestCase, Submission, SubmissionAnalysis, LabActivity, User
from services.gcc_service import compile_and_run
from services.anti_hardcoding_service import analyze_c_code_structure
from services.groq_service import analyze_solution_semantics


def evaluate_submission(problem_id: int, student_code: str, student_id: str = "STU2024001", mode: str = "practice") -> dict:
    """
    Complete solution evaluation pipeline:
    1. GCC compilation
    2. Execution against visible & hidden test cases
    3. Static Code Analysis (detecting constant printf outputs when input required)
    4. Optional Groq Semantic Analysis
    5. Anti-hardcoding classification & evidence logging
    6. Non-punitive student guidance & XP allocation
    """
    db = SessionLocal()
    try:
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem:
            return {
                "success": False,
                "score": 0.0,
                "passed_test_cases": 0,
                "total_test_cases": 0,
                "error": "Problem not found"
            }

        test_cases = db.query(TestCase).filter(TestCase.problem_id == problem_id).all()
        if not test_cases:
            test_cases = [TestCase(input_data=problem.sample_input or "", expected_output=problem.expected_output, is_hidden=False)]

        passed_count = 0
        total_cases = len(test_cases)
        total_exec_time = 0.0
        test_details = []
        hidden_failed_count = 0

        # 1. Execute against all test cases
        for idx, tc in enumerate(test_cases, 1):
            run_res = compile_and_run(student_code, input_data=tc.input_data)

            if not run_res["success"]:
                # Save failed compilation submission
                sub = Submission(
                    student_id=student_id,
                    problem_id=problem_id,
                    code=student_code,
                    status="failed",
                    score=0.0,
                    passed_test_cases=0,
                    total_test_cases=total_cases,
                    xp_earned=0,
                    mode=mode,
                    execution_time_ms=run_res.get("execution_time_ms", 0)
                )
                db.add(sub)
                db.commit()

                return {
                    "success": False,
                    "status": "COMPILATION_ERROR",
                    "compiler_error": run_res["compiler_error"],
                    "line": run_res.get("line"),
                    "score": 0.0,
                    "passed_test_cases": 0,
                    "total_test_cases": total_cases
                }

            total_exec_time += run_res["execution_time_ms"]
            actual = run_res["output"].strip()
            expected = tc.expected_output.strip()

            is_match = _compare_outputs(actual, expected)
            if is_match:
                passed_count += 1
            elif tc.is_hidden:
                hidden_failed_count += 1

            test_details.append({
                "case_number": idx,
                "passed": is_match,
                "input": tc.input_data if not tc.is_hidden else "[HIDDEN TEST CASE]",
                "expected": expected if not tc.is_hidden else "[HIDDEN TEST CASE]",
                "actual": actual if not tc.is_hidden else ("[HIDDEN TEST FAILED]" if not is_match else "[HIDDEN TEST PASSED]")
            })

        # 2. Static Code Analysis (Anti-Hardcoding)
        problem_meta = {
            "requires_input": getattr(problem, "requires_input", True),
            "allows_fixed_output": getattr(problem, "allows_fixed_output", False),
            "expected_output": problem.expected_output,
            "sample_output": problem.sample_output
        }

        static_analysis = analyze_c_code_structure(student_code, problem_meta)

        # 3. Groq Semantic Analysis
        ai_analysis = {}
        if mode != "exam":
            ai_analysis = analyze_solution_semantics(
                student_code=student_code,
                problem_title=problem.title,
                problem_description=problem.description,
                static_analysis=static_analysis,
                test_results={"passed": passed_count, "total": total_cases}
            )

        # 4. Determine Final Solution Status & Hardcoding Classification
        is_completed = (passed_count == total_cases)
        is_hardcoded = False
        final_status = "VALID_SOLUTION"

        if static_analysis["is_suspicious"] and (hidden_failed_count > 0 or not is_completed):
            is_hardcoded = True
            final_status = "POTENTIALLY_HARDCODED"
        elif not is_completed:
            final_status = "PARTIALLY_CORRECT" if passed_count > 0 else "WRONG_ANSWER"

        # 5. Creativity Recognition
        is_creative = _detect_creativity(student_code, problem_id) or ai_analysis.get("is_creative_approach", False)

        # 6. Score & XP Calculation
        score = round((passed_count / total_cases) * 10.0, 1)
        base_xp = problem.xp_reward if is_completed else int(problem.xp_reward * (passed_count / total_cases))
        creative_bonus = 50 if (is_creative and is_completed) else 0
        total_xp_earned = base_xp + creative_bonus if not is_hardcoded else 10

        # Save Submission
        sub = Submission(
            student_id=student_id,
            problem_id=problem_id,
            code=student_code,
            status="completed" if is_completed and not is_hardcoded else "attempted",
            score=score if not is_hardcoded else 3.0,
            passed_test_cases=passed_count,
            total_test_cases=total_cases,
            xp_earned=total_xp_earned,
            mode=mode,
            is_creative=is_creative,
            execution_time_ms=round(total_exec_time / max(1, total_cases), 2)
        )
        db.add(sub)
        db.flush()

        # Save Submission Analysis Telemetry
        analysis = SubmissionAnalysis(
            submission_id=sub.id,
            student_id=student_id,
            problem_id=problem_id,
            status=final_status,
            hardcoding_risk_score=static_analysis["hardcoding_risk_score"],
            has_input_ops=static_analysis["has_input_ops"],
            has_static_output=static_analysis["has_constant_print"],
            hidden_passed_ratio=round((passed_count - (total_cases - hidden_failed_count)) / max(1, hidden_failed_count), 2),
            static_analysis_summary=json.dumps(static_analysis["evidence"]),
            ai_analysis_result=json.dumps(ai_analysis),
            evidence_notes="; ".join(static_analysis["evidence"]),
            review_status="flagged" if is_hardcoded else "approved"
        )
        db.add(analysis)

        # Update User XP & Level
        user = db.query(User).filter(User.user_id == student_id).first()
        if user:
            user.current_xp += total_xp_earned
            user.level = max(1, user.current_xp // 350)
            if is_creative and "Architect" not in user.rank:
                user.rank = "Code Architect"

        # Log Activity
        act_details = f"Submitted Problem #{problem_id} ({passed_count}/{total_cases} passed, Status: {final_status})"
        activity = LabActivity(student_id=student_id, action="submit", details=act_details)
        db.add(activity)

        db.commit()

        # 7. Construct Non-Punitive Educational Feedback Message
        if is_hardcoded:
            feedback_msg = (
                "⚠️ Your solution appears to produce a fixed output for the example input. "
                "Try writing dynamic logic so your program processes the input and calculates the result!"
            )
        elif is_completed:
            feedback_msg = "🎉 Excellent work! All test cases passed with valid problem logic."
            if is_creative:
                feedback_msg += " ✨ Recognized valid alternative approach (+50 XP Bonus)!"
        else:
            feedback_msg = f"Passed {passed_count} of {total_cases} test cases. Some additional cases need attention."

        return {
            "success": True,
            "status": final_status,
            "score": score if not is_hardcoded else 3.0,
            "passed_test_cases": passed_count,
            "total_test_cases": total_cases,
            "test_details": test_details,
            "xp_earned": total_xp_earned,
            "is_creative": is_creative,
            "is_hardcoded": is_hardcoded,
            "hardcoding_risk_score": static_analysis["hardcoding_risk_score"],
            "execution_time_ms": round(total_exec_time / max(1, total_cases), 2),
            "feedback": feedback_msg,
            "correctness_value": round((passed_count / total_cases) * 6.0, 1),
            "approach_value": 2.0 if (is_completed and not is_hardcoded) else 1.0,
            "code_quality_value": 1.0,
            "creativity_value": 1.0 if is_creative else 0.5
        }

    finally:
        db.close()


def _compare_outputs(actual: str, expected: str) -> bool:
    """Whitespace and case-normalized string comparison."""
    norm_actual = re.sub(r'\s+', ' ', actual).strip().lower()
    norm_expected = re.sub(r'\s+', ' ', expected).strip().lower()
    return norm_actual == norm_expected


def _detect_creativity(code: str, problem_id: int) -> bool:
    """
    Detects if the student used an alternative valid approach
    (e.g., ternary operators, bitwise logic, custom functions, or pointer arithmetic).
    """
    code_clean = code.lower()
    if problem_id == 4: # Even/Odd
        if "& 1" in code or "&1" in code:
            return True
    if problem_id == 3: # Largest of three
        if "?" in code and ":" in code:
            return True
    if "int " in code_clean and "(" in code_clean and "main" not in code_clean and "printf" not in code_clean:
        return True # Custom function declared
    if "*" in code and "->" in code:
        return True
    return False
