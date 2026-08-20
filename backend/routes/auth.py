"""
Authentication Routes
POST /api/auth/login — authenticates student or faculty and returns profile state
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    user_id: str
    role: str = "student"


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user_id = request.user_id.strip()
    
    # Query user from DB
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        # Auto-provision user for seamless lab access if not existing
        role = request.role if request.role in ["student", "faculty"] else "student"
        full_name = "Cadet " + user_id if role == "student" else "Dr. " + user_id
        user = User(
            user_id=user_id,
            full_name=full_name,
            role=role,
            current_xp=2840 if role == "student" else 0,
            level=8 if role == "student" else 1,
            rank="Code Architect" if role == "student" else "Faculty Officer",
            streak_days=5
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "success": True,
        "user_id": user.user_id,
        "full_name": user.full_name,
        "role": user.role,
        "email": user.email,
        "current_xp": user.current_xp,
        "level": user.level,
        "rank": user.rank,
        "streak_days": user.streak_days,
        "section": user.section
    }
