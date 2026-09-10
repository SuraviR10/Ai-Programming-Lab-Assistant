"""
Weekly Write-Up Routes
GET /api/writeups — List active weekly lab writeups
POST /api/writeups/{id}/start — Start/resume writeup session with server timer
POST /api/writeups/{id}/autosave — Periodically save code draft
POST /api/writeups/{id}/submit — Final submit writeup session
"""

import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, WriteUp, WriteUpSession, Problem, TestCase, Submission, LabActivity

router = APIRouter(prefix="/api/writeups", tags=["writeups"])


class StartWriteupRequest(BaseModel):
    student_id: str = "STU2024001"


class AutosaveWriteupRequest(BaseModel):
    student_id: str = "STU2024001"
    code_map: dict # {problem_id: code_string}


class SubmitWriteupRequest(BaseModel):
    student_id: str = "STU2024001"
    code_map: dict # {problem_id: code_string}


@router.get("")
def list_writeups(student_id: str = "STU2024001", db: Session = Depends(get_db)):
    writeups = db.query(WriteUp).filter(WriteUp.is_active == True).all()

    results = []
    for w in writeups:
        q_ids = json.loads(w.question_ids) if w.question_ids else []
        session = db.query(WriteUpSession).filter(
            WriteUpSession.writeup_id == w.id,
            WriteUpSession.student_id == student_id
        ).first()

        status = session.status if session else "scheduled"
        score = session.score if session else 0.0

        results.append({
            "id": w.id,
            "title": w.title,
            "description": w.description,
            "topics": w.topics,
            "duration_minutes": w.duration_minutes,
            "questions_count": len(q_ids),
            "ai_policy": w.ai_policy,
            "status": status,
            "score": score,
            "created_at": w.created_at.isoformat() if w.created_at else None
        })

    return {"success": True, "writeups": results}


@router.post("/{writeup_id}/start")
def start_writeup(writeup_id: int, request: StartWriteupRequest, db: Session = Depends(get_db)):
    w = db.query(WriteUp).filter(WriteUp.id == writeup_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Write-up not found")

    q_ids = json.loads(w.question_ids) if w.question_ids else []
    problems = db.query(Problem).filter(Problem.id.in_(q_ids)).all()

    # Get or create active session
    session = db.query(WriteUpSession).filter(
        WriteUpSession.writeup_id == writeup_id,
        WriteUpSession.student_id == request.student_id
    ).first()

    now = datetime.now(timezone.utc)
    if not session:
        session = WriteUpSession(
            writeup_id=writeup_id,
            student_id=request.student_id,
            start_time=now,
            duration_minutes=w.duration_minutes,
            saved_code="{}",
            status="active"
        )
        db.add(session)

        # Log activity
        activity = LabActivity(
            student_id=request.student_id,
            action="writeup_start",
            details=f"Started Write-Up #{writeup_id}: {w.title}"
        )
        db.add(activity)

        db.commit()
        db.refresh(session)

    # Calculate remaining time in seconds
    elapsed_sec = (now - session.start_time.replace(tzinfo=timezone.utc)).total_seconds() if session.start_time.tzinfo is None else (now - session.start_time).total_seconds()
    total_sec = w.duration_minutes * 60
    remaining_sec = max(0, int(total_sec - elapsed_sec))

    if remaining_sec <= 0 and session.status == "active":
        session.status = "expired"
        db.commit()

    prob_details = []
    saved_map = json.loads(session.saved_code) if session.saved_code else {}

    for p in problems:
        prob_details.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "difficulty": p.difficulty,
            "starter_code": saved_map.get(str(p.id)) or saved_map.get(p.id) or p.starter_code,
            "expected_output": p.expected_output,
            "sample_input": p.sample_input,
            "sample_output": p.sample_output
        })

    return {
        "success": True,
        "session_id": session.id,
        "writeup": {
            "id": w.id,
            "title": w.title,
            "description": w.description,
            "topics": w.topics,
            "ai_policy": w.ai_policy,
            "duration_minutes": w.duration_minutes,
            "remaining_seconds": remaining_sec,
            "status": session.status,
            "problems": prob_details
        }
    }


@router.post("/{writeup_id}/autosave")
def autosave_writeup(writeup_id: int, request: AutosaveWriteupRequest, db: Session = Depends(get_db)):
    session = db.query(WriteUpSession).filter(
        WriteUpSession.writeup_id == writeup_id,
        WriteUpSession.student_id == request.student_id
    ).first()

    if not session or session.status != "active":
        return {"success": False, "message": "Session inactive or expired."}

    session.saved_code = json.dumps(request.code_map)
    db.commit()

    return {"success": True, "message": "Draft code auto-saved successfully."}


def _compare_outputs(actual: str, expected: str) -> bool:
    if not actual and not expected:
        return True
    if not actual or not expected:
        return False
    import re
    norm_act = re.sub(r'\s+', ' ', actual).strip().lower()
    norm_exp = re.sub(r'\s+', ' ', expected).strip().lower()
    return norm_act == norm_exp


@router.post("/{writeup_id}/submit")
def submit_writeup(writeup_id: int, request: SubmitWriteupRequest, db: Session = Depends(get_db)):
    """
    Evaluates each problem in the weekly writeup session with GCC and test cases.
    Awards real authentic scores (0.0 - 10.0) based on test performance.
    """
    w = db.query(WriteUp).filter(WriteUp.id == writeup_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Write-up not found")

    session = db.query(WriteUpSession).filter(
        WriteUpSession.writeup_id == writeup_id,
        WriteUpSession.student_id == request.student_id
    ).first()

    if not session:
        session = WriteUpSession(
            writeup_id=writeup_id,
            student_id=request.student_id,
            start_time=datetime.now(timezone.utc),
            duration_minutes=w.duration_minutes,
            saved_code=json.dumps(request.code_map),
            status="active"
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    q_ids = json.loads(w.question_ids) if w and w.question_ids else []
    problems = db.query(Problem).filter(Problem.id.in_(q_ids)).all() if q_ids else []

    total_problems = len(problems) if problems else 1
    score_per_problem = 10.0 / total_problems

    total_score = 0.0
    breakdown = []

    from services.gcc_service import compile_and_run

    for p in problems:
        code = request.code_map.get(str(p.id)) or request.code_map.get(p.id) or ""
        test_cases = db.query(TestCase).filter(TestCase.problem_id == p.id).all()
        if not test_cases:
            test_cases = [TestCase(input_data=p.sample_input or "", expected_output=p.expected_output or p.sample_output or "", is_hidden=False)]

        total_tc = len(test_cases)
        passed_tc = 0
        prob_status = "NOT_ATTEMPTED"
        comp_error = ""

        if code.strip():
            compiled_ok = True
            for tc in test_cases:
                run_res = compile_and_run(code, input_data=tc.input_data)
                if not run_res["success"]:
                    compiled_ok = False
                    comp_error = run_res.get("compiler_error", "Compilation failed.")
                    break
                else:
                    actual = (run_res.get("output") or "").strip()
                    expected = (tc.expected_output or "").strip()
                    if _compare_outputs(actual, expected):
                        passed_tc += 1

            if not compiled_ok:
                prob_status = "COMPILATION_ERROR"
                prob_score = 0.0
            else:
                prob_score = round((passed_tc / total_tc) * score_per_problem, 2)
                prob_status = "PASSED" if passed_tc == total_tc else ("PARTIAL" if passed_tc > 0 else "FAILED")
        else:
            prob_score = 0.0

        total_score += prob_score

        # Record submission
        sub = Submission(
            student_id=request.student_id,
            problem_id=p.id,
            code=code or "// Empty Write-Up Submission",
            status="passed" if prob_status == "PASSED" else "failed",
            score=prob_score,
            passed_test_cases=passed_tc,
            total_test_cases=total_tc,
            xp_earned=int(prob_score * 10),
            mode="writeup",
            execution_time_ms=50.0
        )
        db.add(sub)

        breakdown.append({
            "problem_id": p.id,
            "title": p.title,
            "score": prob_score,
            "max_score": round(score_per_problem, 2),
            "passed_cases": passed_tc,
            "total_cases": total_tc,
            "status": prob_status,
            "compiler_error": comp_error if prob_status == "COMPILATION_ERROR" else None
        })

    total_score = min(10.0, max(0.0, round(total_score, 1)))

    session.saved_code = json.dumps(request.code_map)
    session.status = "submitted"
    session.submitted_at = datetime.now(timezone.utc)
    session.score = total_score

    # Log activity
    activity = LabActivity(
        student_id=request.student_id,
        action="writeup_submit",
        details=f"Completed Write-Up #{writeup_id}: {w.title} with Score: {total_score}/10"
    )
    db.add(activity)

    db.commit()

    return {
        "success": True,
        "status": "submitted",
        "score": total_score,
        "max_score": 10.0,
        "percentage": round((total_score / 10.0) * 100, 1),
        "breakdown": breakdown,
        "message": f"Weekly write-up evaluated successfully. Score: {total_score} / 10.0"
    }

