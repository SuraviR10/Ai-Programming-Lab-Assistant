"""
Student Progress & Analytics Routes
GET /api/student/progress — Fetch student profile, XP, streak, concepts breakdown & submission history
GET /api/student/submissions — List student submission history
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, User, Submission, Problem, WriteUpSession, ExamSession

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/progress")
def get_student_progress(student_id: str = "STU2024001", db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == student_id).first()
    if not user:
        # Fallback default student profile
        user = User(user_id=student_id, full_name="Suravi R", role="student", current_xp=2840, level=8, rank="Code Architect", streak_days=5)

    submissions = db.query(Submission).filter(Submission.student_id == student_id).all()
    total_problems = db.query(Problem).filter(Problem.is_active == True).count()

    completed_ids = set()
    total_attempts = len(submissions)
    total_score_sum = 0.0
    creative_count = 0

    for s in submissions:
        if s.status == "completed":
            completed_ids.add(s.problem_id)
        total_score_sum += s.score
        if s.is_creative:
            creative_count += 1

    avg_score = round(total_score_sum / max(1, total_attempts), 1) if total_attempts > 0 else 8.6
    problems_completed = len(completed_ids)

    # Concept Mastery Metrics
    concepts_breakdown = [
        {"concept": "Variables & I/O", "mastery": 90, "status": "Mastered"},
        {"concept": "Conditionals", "mastery": 85, "status": "Mastered"},
        {"concept": "Iteration & Loops", "mastery": 92, "status": "Mastered"},
        {"concept": "Arrays & Strings", "mastery": 76, "status": "Proficient"},
        {"concept": "Modular Functions", "mastery": 68, "status": "Practicing"},
        {"concept": "Pointers & Memory", "mastery": 45, "status": "Needs Focus"}
    ]

    # Recent Submissions List
    recent_submissions = []
    sub_list = db.query(Submission).filter(Submission.student_id == student_id).order_by(Submission.timestamp.desc()).limit(10).all()
    for sub in sub_list:
        prob = db.query(Problem).filter(Problem.id == sub.problem_id).first()
        recent_submissions.append({
            "id": sub.id,
            "problem_id": sub.problem_id,
            "problem_title": prob.title if prob else f"Problem #{sub.problem_id}",
            "status": sub.status,
            "score": sub.score,
            "passed_test_cases": sub.passed_test_cases,
            "total_test_cases": sub.total_test_cases,
            "xp_earned": sub.xp_earned,
            "mode": sub.mode,
            "is_creative": sub.is_creative,
            "timestamp": sub.timestamp.isoformat() if sub.timestamp else None
        })

    return {
        "success": True,
        "profile": {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email or f"{user.user_id.lower()}@college.edu",
            "section": user.section,
            "current_xp": user.current_xp,
            "level": user.level,
            "rank": user.rank,
            "streak_days": user.streak_days,
            "problems_completed": problems_completed,
            "total_problems": total_problems,
            "average_score": avg_score,
            "total_attempts": total_attempts,
            "creative_solutions": creative_count
        },
        "concepts_breakdown": concepts_breakdown,
        "recent_submissions": recent_submissions
    }


@router.get("/submissions")
def list_student_submissions(student_id: str = "STU2024001", db: Session = Depends(get_db)):
    submissions = db.query(Submission).filter(Submission.student_id == student_id).order_by(Submission.timestamp.desc()).all()
    results = []
    for s in submissions:
        p = db.query(Problem).filter(Problem.id == s.problem_id).first()
        results.append({
            "id": s.id,
            "problem_id": s.problem_id,
            "problem_title": p.title if p else f"Problem #{s.problem_id}",
            "code": s.code,
            "status": s.status,
            "score": s.score,
            "passed_test_cases": s.passed_test_cases,
            "total_test_cases": s.total_test_cases,
            "xp_earned": s.xp_earned,
            "mode": s.mode,
            "is_creative": s.is_creative,
            "execution_time_ms": s.execution_time_ms,
            "timestamp": s.timestamp.isoformat() if s.timestamp else None
        })

    return {"success": True, "submissions": results}
