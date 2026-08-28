from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, Problem, Submission, User, LabActivity
from services.gcc_service import compile_and_run
from services.groq_service import analyze_compiler_error, analyze_test_failure
from services.evaluation_service import evaluate_submission

router = APIRouter(prefix="/compiler", tags=["Compiler"])


class RunRequest(BaseModel):
    code: str
    input_data: str | None = None
    problem_id: int | None = None
    mode: str = "practice" # practice, writeup, exam


class SubmitRequest(BaseModel):
    problem_id: int
    code: str
    student_id: str = "STU2024001"
    mode: str = "practice" # practice, writeup, exam


def _norm_str(s: str | None) -> str:
    if not s:
        return ""
    import re
    return re.sub(r'\s+', ' ', s).strip().lower()


@router.post("/run")
def run_code(req: RunRequest, db: Session = Depends(get_db)):
    """
    Executes student C code via GCC.
    - If GCC fails -> Sends compiler error to Groq LLM with complete code.
    - If test mismatch -> Sends test discrepancy to Groq LLM with complete code.
    - If clean/correct -> Returns output directly with NO Groq call.
    """
    input_data = req.input_data
    problem = None
    if req.problem_id:
        problem = db.query(Problem).filter(Problem.id == req.problem_id).first()
        if problem and not input_data and problem.sample_input:
            input_data = problem.sample_input

    result = compile_and_run(req.code, input_data=input_data)

    if not result["success"]:
        # GCC Compilation error -> Call Groq AI Service with complete code
        ai_feedback = analyze_compiler_error(
            student_code=req.code,
            compiler_error=result["compiler_error"],
            line_number=result.get("line"),
            mode=req.mode
        )

        return {
            "success": False,
            "compiler_error": result["compiler_error"],
            "line": result.get("line"),
            "ai_feedback": ai_feedback
        }

    # Compilation successful
    if problem and problem.expected_output:
        expected = problem.expected_output
        actual = result["output"]
        if _norm_str(actual) != _norm_str(expected):
            ai_feedback = analyze_test_failure(
                student_code=req.code,
                problem_title=problem.title,
                problem_description=problem.description,
                failed_test_cases=[{"input": input_data or "[None]", "expected": expected, "actual": actual}],
                mode=req.mode
            )
            return {
                "success": True,
                "output": result["output"],
                "test_passed": False,
                "ai_feedback": ai_feedback,
                "execution_time_ms": result.get("execution_time_ms", 0)
            }

    return {
        "success": True,
        "output": result["output"],
        "test_passed": True,
        "execution_time_ms": result.get("execution_time_ms", 0)
    }


@router.post("/submit")
def submit_code(req: SubmitRequest, db: Session = Depends(get_db)):
    """
    Evaluates student submission against stored database test cases.
    Grades score (0-10), updates student XP/level, and saves submission log.
    """
    eval_res = evaluate_submission(req.problem_id, req.code)

    if not eval_res["success"]:
        # Record failed submission
        sub = Submission(
            student_id=req.student_id,
            problem_id=req.problem_id,
            code=req.code,
            status="failed",
            score=0.0,
            mode=req.mode
        )
        db.add(sub)
        db.commit()

        ai_feedback = analyze_compiler_error(
            student_code=req.code,
            compiler_error=eval_res["compilation_error"],
            line_number=eval_res.get("line"),
            mode=req.mode
        )

        return {
            "success": False,
            "compiler_error": eval_res["compilation_error"],
            "line": eval_res.get("line"),
            "ai_feedback": ai_feedback
        }

    # Successful evaluation against test cases
    sub = Submission(
        student_id=req.student_id,
        problem_id=req.problem_id,
        code=req.code,
        status="completed" if eval_res["score"] >= 8.0 else "attempted",
        score=eval_res["score"],
        passed_test_cases=eval_res["passed_test_cases"],
        total_test_cases=eval_res["total_test_cases"],
        xp_earned=eval_res["xp_earned"],
        mode=req.mode,
        is_creative=eval_res["is_creative"]
    )
    db.add(sub)

    # Log lab activity
    db.add(LabActivity(
        student_id=req.student_id,
        action="submit",
        details=f"Problem {req.problem_id} submitted with score {eval_res['score']}"
    ))

    # Update Student XP
    user = db.query(User).filter(User.user_id == req.student_id).first()
    if user:
        user.current_xp += eval_res["xp_earned"]
        # Level up formula: Level = XP // 350 + 1
        new_level = (user.current_xp // 350) + 1
        if new_level > user.level:
            user.level = new_level

    db.commit()

    return {
        "success": True,
        "score": eval_res["score"],
        "passed_test_cases": eval_res["passed_test_cases"],
        "total_test_cases": eval_res["total_test_cases"],
        "xp_earned": eval_res["xp_earned"],
        "is_creative": eval_res["is_creative"],
        "feedback": eval_res["feedback"],
        "test_case_results": eval_res["test_case_results"],
        "correctness": eval_res["correctness"],
        "approach": eval_res["approach"],
        "codeQuality": eval_res["codeQuality"],
        "creativity": eval_res["creativity"]
    }
