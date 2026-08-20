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
from services.groq_service import analyze_compiler_error

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


@router.post("/api/compiler/run")
def run_code(request: RunRequest, db: Session = Depends(get_db)):
    # 1. Determine input data from problem sample if not provided
    input_data = request.input_data
    if not input_data and request.problem_id:
        problem = db.query(Problem).filter(Problem.id == request.problem_id).first()
        if problem and problem.sample_input:
            input_data = problem.sample_input

    # 2. Compile and execute with GCC
    result = compile_and_run(request.code, input_data=input_data)

    if result["success"]:
        # Compilation and execution succeeded — return output directly without Groq
        return {
            "success": True,
            "output": result["output"],
            "execution_time_ms": result["execution_time_ms"]
        }

    # 3. Compilation failed — call Groq AI (respecting mode policy)
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
