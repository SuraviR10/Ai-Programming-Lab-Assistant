"""
Exam Mode Routes
GET /api/exams — List active timed practical exams
POST /api/exams/{id}/start — Start/resume timed exam session with AI DISABLED
POST /api/exams/{id}/autosave — Periodically save exam draft
POST /api/exams/{id}/submit — Submit final exam session
"""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, Exam, ExamSession, Problem, LabActivity

router = APIRouter(prefix="/api/exams", tags=["exams"])


class StartExamRequest(BaseModel):
    student_id: str = "STU2024001"


class AutosaveExamRequest(BaseModel):
    student_id: str = "STU2024001"
    code_map: dict # {problem_id: code_string}


class SubmitExamRequest(BaseModel):
    student_id: str = "STU2024001"
    code_map: dict # {problem_id: code_string}


@router.get("")
def list_exams(student_id: str = "STU2024001", db: Session = Depends(get_db)):
    exams = db.query(Exam).filter(Exam.is_active == True).all()

    results = []
    for e in exams:
        q_ids = json.loads(e.question_ids) if e.question_ids else []
        session = db.query(ExamSession).filter(
            ExamSession.exam_id == e.id,
            ExamSession.student_id == student_id
        ).first()

        status = session.status if session else "scheduled"
        score = session.score if session else 0.0

        results.append({
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "topics": e.topics,
            "duration_minutes": e.duration_minutes,
            "questions_count": len(q_ids),
            "status": status,
            "score": score,
            "created_at": e.created_at.isoformat() if e.created_at else None
        })

    return {"success": True, "exams": results}


@router.post("/{exam_id}/start")
def start_exam(exam_id: int, request: StartExamRequest, db: Session = Depends(get_db)):
    e = db.query(Exam).filter(Exam.id == exam_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Exam not found")

    q_ids = json.loads(e.question_ids) if e.question_ids else []
    problems = db.query(Problem).filter(Problem.id.in_(q_ids)).all()

    session = db.query(ExamSession).filter(
        ExamSession.exam_id == exam_id,
        ExamSession.student_id == request.student_id
    ).first()

    now = datetime.now(timezone.utc)
    if not session:
        session = ExamSession(
            exam_id=exam_id,
            student_id=request.student_id,
            start_time=now,
            duration_minutes=e.duration_minutes,
            saved_code="{}",
            status="active"
        )
        db.add(session)

        # Log activity
        activity = LabActivity(
            student_id=request.student_id,
            action="exam_start",
            details=f"Started Practical Exam #{exam_id}: {e.title}"
        )
        db.add(activity)

        db.commit()
        db.refresh(session)

    # Calculate remaining time in seconds
    elapsed_sec = (now - session.start_time.replace(tzinfo=timezone.utc)).total_seconds() if session.start_time.tzinfo is None else (now - session.start_time).total_seconds()
    total_sec = e.duration_minutes * 60
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
        "exam": {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "topics": e.topics,
            "ai_policy": "none", # EXAM MODE: Strictly NO AI TUTORING
            "duration_minutes": e.duration_minutes,
            "remaining_seconds": remaining_sec,
            "status": session.status,
            "problems": prob_details
        }
    }


@router.post("/{exam_id}/autosave")
def autosave_exam(exam_id: int, request: AutosaveExamRequest, db: Session = Depends(get_db)):
    session = db.query(ExamSession).filter(
        ExamSession.exam_id == exam_id,
        ExamSession.student_id == request.student_id
    ).first()

    if not session or session.status != "active":
        return {"success": False, "message": "Exam session inactive or expired."}

    session.saved_code = json.dumps(request.code_map)
    db.commit()

    return {"success": True, "message": "Exam draft code auto-saved."}


@router.post("/{exam_id}/submit")
def submit_exam(exam_id: int, request: SubmitExamRequest, db: Session = Depends(get_db)):
    session = db.query(ExamSession).filter(
        ExamSession.exam_id == exam_id,
        ExamSession.student_id == request.student_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    session.saved_code = json.dumps(request.code_map)
    session.status = "submitted"
    session.submitted_at = datetime.now(timezone.utc)
    session.score = 9.5
    db.commit()

    return {
        "success": True,
        "status": "submitted",
        "score": session.score,
        "message": "Practical Exam submitted successfully!"
    }
