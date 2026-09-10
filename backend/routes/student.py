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
        user = User(user_id=student_id, full_name="Student " + student_id, role="student", current_xp=0, level=1, rank="C Programmer", streak_days=1)

    submissions = db.query(Submission).filter(Submission.student_id == student_id).all()
    all_problems = db.query(Problem).filter(Problem.is_active == True).all()
    total_problems = len(all_problems)

    completed_ids = set()
    total_attempts = len(submissions)
    total_score_sum = 0.0
    creative_count = 0

    for s in submissions:
        if s.status in ["completed", "passed"]:
            completed_ids.add(s.problem_id)
        total_score_sum += s.score
        if s.is_creative:
            creative_count += 1

    avg_score = round(total_score_sum / total_attempts, 1) if total_attempts > 0 else 0.0
    problems_completed = len(completed_ids)

    # Dynamic Concept Mastery Calculation
    CORE_CONCEPTS = [
        "Variables & I/O",
        "Conditionals",
        "Iteration & Loops",
        "Arrays & Strings",
        "Modular Functions",
        "Pointers & Memory"
    ]

    concept_scores = {c: [] for c in CORE_CONCEPTS}
    prob_concept_map = {}
    for p in all_problems:
        concepts = json.loads(p.concepts) if p.concepts else []
        for c in concepts:
            c_lower = c.lower()
            if "io" in c_lower or "printf" in c_lower or "scanf" in c_lower or "variable" in c_lower or "basic" in c_lower:
                prob_concept_map.setdefault(p.id, []).append("Variables & I/O")
            elif "conditional" in c_lower or "if" in c_lower or "switch" in c_lower:
                prob_concept_map.setdefault(p.id, []).append("Conditionals")
            elif "loop" in c_lower or "iterat" in c_lower or "while" in c_lower or "for" in c_lower:
                prob_concept_map.setdefault(p.id, []).append("Iteration & Loops")
            elif "array" in c_lower or "string" in c_lower or "matrix" in c_lower:
                prob_concept_map.setdefault(p.id, []).append("Arrays & Strings")
            elif "function" in c_lower or "modular" in c_lower or "recursion" in c_lower:
                prob_concept_map.setdefault(p.id, []).append("Modular Functions")
            elif "pointer" in c_lower or "memory" in c_lower or "struct" in c_lower:
                prob_concept_map.setdefault(p.id, []).append("Pointers & Memory")

    for s in submissions:
        matched_concepts = prob_concept_map.get(s.problem_id, [])
        for mc in matched_concepts:
            if mc in concept_scores:
                concept_scores[mc].append(s.score)

    concepts_breakdown = []
    for c in CORE_CONCEPTS:
        scores = concept_scores[c]
        if scores:
            mastery = min(100, int((sum(scores) / (len(scores) * 10.0)) * 100))
        else:
            mastery = 0

        if mastery >= 80:
            status = "Mastered"
        elif mastery >= 60:
            status = "Proficient"
        elif mastery >= 30:
            status = "Practicing"
        else:
            status = "Needs Focus" if scores else "Not Started"

        concepts_breakdown.append({
            "concept": c,
            "mastery": mastery,
            "status": status,
            "attempts": len(scores)
        })

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
