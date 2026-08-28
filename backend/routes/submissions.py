"""
Submissions & Compiler Evaluation Routes
POST /api/compiler/run — Run code against sample input with GCC & Groq error guidance
POST /api/submissions — Submit code for complete test-suite evaluation and XP awarding
POST /api/feedback — Submit student difficulty feedback rating
"""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, Problem, TestCase, Submission, User, StudentFeedback, LabActivity
from services.gcc_service import compile_and_run
from services.groq_service import analyze_compiler_error, analyze_test_failure

router = APIRouter(tags=["compiler_and_submissions"])


class RunRequest(BaseModel):
    code: str
    problem_id: int | None = None
    input_data: str | None = None
    mode: str = "practice"


class SubmitRequest(BaseModel):
    student_id: str = "STU2024001"
    problem_id: int
    code: str
    mode: str = "practice"


class FeedbackRequest(BaseModel):
    student_id: str = "STU2024001"
    problem_id: int
    difficulty_rating: int # 1 to 5
    comment: str | None = None


class ChallengeRequest(BaseModel):
    student_id: str = "STU2024001"
    concept: str = "Arrays"
    difficulty: str = "medium"


class ActivityRequest(BaseModel):
    student_id: str = "STU2024001"
    action: str
    details: str | None = None


def _normalize_str(s: str | None) -> str:
    if not s:
        return ""
    import re
    return re.sub(r'\s+', ' ', s).strip().lower()


@router.post("/api/compiler/run")
def run_code(request: RunRequest, db: Session = Depends(get_db)):
    """
    Executes student C code via GCC with full code context.
    - If Compilation / Execution Fails: Calls Groq error analyzer with complete code.
    - If Output Mismatches Expected Problem Output: Calls Groq test failure analyzer with complete code.
    - If Everything is Correct: Completely bypasses Groq API calls for fast zero-overhead execution.
    """
    # 1. Determine input data from problem sample if not provided
    input_data = request.input_data
    problem = None
    if request.problem_id:
        problem = db.query(Problem).filter(Problem.id == request.problem_id).first()
        if problem and not input_data and problem.sample_input:
            input_data = problem.sample_input

    # 2. Compile and execute with GCC
    result = compile_and_run(request.code, input_data=input_data)

    if not result["success"]:
        # Compilation or execution failed — call Groq AI with complete code context
        compiler_error = result["compiler_error"]
        line_number = result.get("line")

        ai_feedback = analyze_compiler_error(
            student_code=request.code,
            compiler_error=compiler_error,
            line_number=line_number,
            mode=request.mode
        )

        return {
            "success": False,
            "compiler_error": compiler_error,
            "line": line_number,
            "ai_feedback": ai_feedback,
            "execution_time_ms": result.get("execution_time_ms", 0)
        }

    # 3. Compilation succeeded
    # Check if there is a test case / expected output to compare against
    if problem and problem.expected_output:
        expected = problem.expected_output
        actual = result["output"]
        is_match = (_normalize_str(actual) == _normalize_str(expected))

        if not is_match:
            # Test case output mismatch — call Groq with complete student code to diagnose logical flaw
            ai_feedback = analyze_test_failure(
                student_code=request.code,
                problem_title=problem.title,
                problem_description=problem.description,
                failed_test_cases=[{
                    "input": input_data or "[None]",
                    "expected": expected,
                    "actual": actual
                }],
                mode=request.mode
            )

            return {
                "success": True,
                "output": result["output"],
                "test_passed": False,
                "ai_feedback": ai_feedback,
                "execution_time_ms": result["execution_time_ms"]
            }

        # Everything is correct — return output directly without Groq call!
        return {
            "success": True,
            "output": result["output"],
            "test_passed": True,
            "execution_time_ms": result["execution_time_ms"]
        }

    # Clean execution with no specific problem expected output — direct bypass, no Groq
    return {
        "success": True,
        "output": result["output"],
        "execution_time_ms": result["execution_time_ms"]
    }


@router.post("/api/submissions")
def submit_solution(request: SubmitRequest, db: Session = Depends(get_db)):
    from services.evaluation_service import evaluate_submission
    result = evaluate_submission(
        problem_id=request.problem_id,
        student_code=request.code,
        student_id=request.student_id,
        mode=request.mode
    )
    return result


@router.post("/api/feedback")
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    fb = StudentFeedback(
        student_id=request.student_id,
        problem_id=request.problem_id,
        difficulty_rating=request.difficulty_rating,
        comment=request.comment
    )
    db.add(fb)
    db.commit()

    return {"success": True, "message": "Feedback recorded successfully."}


@router.post("/api/practice/challenge")
def generate_challenge(request: ChallengeRequest):
    from services.practice_service import generate_challenge_problem
    result = generate_challenge_problem(
        concept=request.concept,
        student_id=request.student_id,
        difficulty=request.difficulty
    )
    return result


@router.post("/api/student/activity")
def log_student_activity(request: ActivityRequest, db: Session = Depends(get_db)):
    act = LabActivity(
        student_id=request.student_id,
        action=request.action,
        details=request.details
    )
    db.add(act)
    db.commit()

    return {"success": True, "message": "Activity logged."}

