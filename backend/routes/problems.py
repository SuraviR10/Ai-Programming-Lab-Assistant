"""
Problems Route
GET /api/problems — list all available C programming problems
GET /api/problems/{id} — detail view of problem with starter code & hints
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Problem, Submission

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.get("")
def list_problems(student_id: str = "STU2024001", db: Session = Depends(get_db)):
    problems = db.query(Problem).filter(Problem.is_active == True).all()
    
    # Query student submissions to determine completed/attempted status
    student_subs = db.query(Submission).filter(Submission.student_id == student_id).all()
    status_map = {}
    best_score_map = {}
    
    for sub in student_subs:
        p_id = sub.problem_id
        if p_id not in status_map or sub.status == "completed":
            status_map[p_id] = sub.status
        if p_id not in best_score_map or sub.score > best_score_map[p_id]:
            best_score_map[p_id] = sub.score

    results = []
    for p in problems:
        concepts = json.loads(p.concepts) if p.concepts else []
        hints = json.loads(p.hints) if p.hints else []
        prog_hints = json.loads(p.progressive_hints) if p.progressive_hints else []

        results.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "difficulty": p.difficulty,
            "concepts": concepts,
            "starter_code": p.starter_code,
            "expected_output": p.expected_output,
            "sample_input": p.sample_input,
            "sample_output": p.sample_output,
            "xp_reward": p.xp_reward,
            "hints": hints,
            "progressive_hints": prog_hints,
            "status": status_map.get(p.id, "pending"),
            "best_score": best_score_map.get(p.id, 0.0),
        })

    return {"success": True, "problems": results}


@router.get("/{problem_id}")
def get_problem(problem_id: int, student_id: str = "STU2024001", db: Session = Depends(get_db)):
    p = db.query(Problem).filter(Problem.id == problem_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")

    concepts = json.loads(p.concepts) if p.concepts else []
    hints = json.loads(p.hints) if p.hints else []
    prog_hints = json.loads(p.progressive_hints) if p.progressive_hints else []

    # Get student status
    sub = db.query(Submission).filter(
        Submission.student_id == student_id,
        Submission.problem_id == problem_id
    ).order_by(Submission.score.desc()).first()

    status = sub.status if sub else "pending"
    best_score = sub.score if sub else 0.0

    return {
        "success": True,
        "problem": {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "difficulty": p.difficulty,
            "concepts": concepts,
            "starter_code": p.starter_code,
            "expected_output": p.expected_output,
            "sample_input": p.sample_input,
            "sample_output": p.sample_output,
            "xp_reward": p.xp_reward,
            "hints": hints,
            "progressive_hints": prog_hints,
            "status": status,
            "best_score": best_score,
        }
    }
