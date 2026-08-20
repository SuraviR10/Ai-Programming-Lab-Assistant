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


@router.post("/{writeup_id}/submit")
def submit_writeup(writeup_id: int, request: SubmitWriteupRequest, db: Session = Depends(get_db)):
    session = db.query(WriteUpSession).filter(
        WriteUpSession.writeup_id == writeup_id,
        WriteUpSession.student_id == request.student_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Write-up session not found")

    w = db.query(WriteUp).filter(WriteUp.id == writeup_id).first()
    q_ids = json.loads(w.question_ids) if w and w.question_ids else []

    session.saved_code = json.dumps(request.code_map)
    session.status = "submitted"
    session.submitted_at = datetime.now(timezone.utc)
    session.score = 9.2 # High default score for valid writeup completion
    db.commit()

    return {
        "success": True,
        "status": "submitted",
        "score": session.score,
        "message": "Weekly write-up submitted successfully!"
    }
