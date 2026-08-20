"""
Database Layer & Auto-Seeding Engine
Supports PostgreSQL (Supabase) with zero-configuration SQLite local fallback.
Auto-initializes tables and seed data (problems, test cases, users, writeups, exams).
"""

import os
import json
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

# Determine Database URL (Supabase PostgreSQL or Local SQLite fallback)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or "postgresql" not in DATABASE_URL:
    DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
    os.makedirs(DATA_DIR, exist_ok=True)
    DB_PATH = os.path.join(DATA_DIR, "ailab.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# Connect Engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── 1. Models ──────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), unique=True, index=True, nullable=False) # e.g. STU2024001
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), default="student") # student, faculty, admin
    email = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Student attributes
    current_xp = Column(Integer, default=2840)
    level = Column(Integer, default=8)
    rank = Column(String(64), default="Code Architect")
    streak_days = Column(Integer, default=5)
    section = Column(String(16), default="A")


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(32), default="easy") # easy, medium, hard
    concepts = Column(Text, default="[]") # JSON list of concepts
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    constraints = Column(Text, nullable=True)
    sample_input = Column(Text, nullable=True)
    sample_output = Column(Text, nullable=True)
    starter_code = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    xp_reward = Column(Integer, default=100)
    hints = Column(Text, default="[]") # JSON list of hints
    progressive_hints = Column(Text, default="[]") # JSON 3-tier hints
    requires_input = Column(Boolean, default=True)
    allows_fixed_output = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    input_data = Column(Text, default="")
    expected_output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, default=False)

    problem = relationship("Problem", back_populates="test_cases")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(64), index=True, nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    code = Column(Text, nullable=False)
    status = Column(String(32), default="completed") # completed, failed, attempted
    score = Column(Float, default=0.0) # 0.0 - 10.0
    passed_test_cases = Column(Integer, default=0)
    total_test_cases = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    mode = Column(String(32), default="practice") # practice, writeup, exam
    is_creative = Column(Boolean, default=False)
    execution_time_ms = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WriteUp(Base):
    __tablename__ = "writeups"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    topics = Column(String(256), default="Arrays, Functions")
    duration_minutes = Column(Integer, default=30)
    question_ids = Column(Text, default="[1, 2]") # JSON list of problem IDs
    ai_policy = Column(String(32), default="limited") # none, limited, full
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WriteUpSession(Base):
    __tablename__ = "writeup_sessions"

    id = Column(Integer, primary_key=True, index=True)
    writeup_id = Column(Integer, ForeignKey("writeups.id"), nullable=False)
    student_id = Column(String(64), index=True, nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    duration_minutes = Column(Integer, default=30)
    saved_code = Column(Text, default="{}") # JSON {problem_id: code}
    status = Column(String(32), default="active") # active, submitted, expired
    score = Column(Float, default=0.0)
    submitted_at = Column(DateTime, nullable=True)


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    topics = Column(String(256), default="Loops, Arrays, Pointers")
    duration_minutes = Column(Integer, default=45)
    question_ids = Column(Text, default="[3, 4]") # JSON list of problem IDs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id = Column(String(64), index=True, nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    duration_minutes = Column(Integer, default=45)
    saved_code = Column(Text, default="{}") # JSON {problem_id: code}
    status = Column(String(32), default="active") # active, submitted, expired
    score = Column(Float, default=0.0)
    submitted_at = Column(DateTime, nullable=True)


class StudentFeedback(Base):
    __tablename__ = "student_feedback"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(64), index=True, nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    difficulty_rating = Column(Integer, default=3) # 1 (very easy) to 5 (very hard)
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class LabActivity(Base):
    __tablename__ = "lab_activity"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(64), index=True, nullable=False)
    action = Column(String(64), nullable=False) # run, submit, debug_fix, writeup_start
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SubmissionAnalysis(Base):
    __tablename__ = "submission_analysis"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    student_id = Column(String(64), index=True, nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    status = Column(String(32), default="VALID_SOLUTION") # VALID_SOLUTION, POTENTIALLY_HARDCODED, WRONG_ANSWER
    hardcoding_risk_score = Column(Float, default=0.0)
    has_input_ops = Column(Boolean, default=True)
    has_static_output = Column(Boolean, default=False)
    hidden_passed_ratio = Column(Float, default=1.0)
    static_analysis_summary = Column(Text, default="[]") # JSON list of findings
    ai_analysis_result = Column(Text, default="{}") # JSON dict of Groq analysis
    evidence_notes = Column(Text, nullable=True)
    review_status = Column(String(32), default="pending") # pending, approved, flagged
    reviewed_by = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 2. Automatic Database Seeding ──────────────────────────────

def init_db_and_seed():
    # Safely migrate new columns if database exists
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE problems ADD COLUMN requires_input BOOLEAN DEFAULT 1"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE problems ADD COLUMN allows_fixed_output BOOLEAN DEFAULT 0"))
            conn.commit()
        except Exception:
            pass

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Users if not present
        if db.query(User).count() == 0:
            default_users = [
                User(user_id="STU2024001", full_name="Suravi R", role="student", current_xp=2840, level=8, rank="Code Architect", streak_days=5),
                User(user_id="STU2024002", full_name="Rahul M", role="student", current_xp=2200, level=6, rank="Debugger", streak_days=3),
                User(user_id="STU2024003", full_name="Priya K", role="student", current_xp=3450, level=10, rank="Problem Solver", streak_days=7),
                User(user_id="STU2024004", full_name="Amit S", role="student", current_xp=950, level=3, rank="Explorer", streak_days=1),
                User(user_id="FAC2024001", full_name="Dr. Anand Kumar", role="faculty", email="anand.kumar@college.edu")
            ]
            db.add_all(default_users)
            db.commit()

        # 2. Seed Problems & Test Cases if not present
        if db.query(Problem).count() == 0:
            problems_data = [
                {
                    "id": 1,
                    "title": "Hello World",
                    "description": "Write a C program that prints \"Hello, World!\" to the console.",
                    "difficulty": "easy",
                    "concepts": ["printf", "basics"],
                    "starter_code": '#include <stdio.h>\n\nint main() {\n    // Write your code here\n    printf("Hello, World!\\n");\n    return 0;\n}\n',
                    "expected_output": "Hello, World!",
                    "sample_input": None,
                    "sample_output": "Hello, World!",
                    "xp_reward": 100,
                    "hints": ["Use printf() to print text", "Include <stdio.h>", "Remember semicolon"],
                    "progressive_hints": [
                        {"tier": 1, "title": "Output Function", "text": "Use the standard I/O library printf() function."},
                        {"tier": 2, "title": "Exact String Match", "text": "Make sure string matches 'Hello, World!' exactly."},
                        {"tier": 3, "title": "Full Code Hint", "text": "printf(\"Hello, World!\\n\"); inside main()."}
                    ],
                    "test_cases": [
                        {"input": "", "expected": "Hello, World!", "is_hidden": False}
                    ]
                },
                {
                    "id": 2,
                    "title": "Sum of Two Numbers",
                    "description": "Write a C program that reads two integers from the user and prints their sum in the format: Sum = X",
                    "difficulty": "easy",
                    "concepts": ["scanf", "variables", "arithmetic"],
                    "starter_code": '#include <stdio.h>\n\nint main() {\n    int a, b;\n    if (scanf("%d %d", &a, &b) == 2) {\n        printf("Sum = %d\\n", a + b);\n    }\n    return 0;\n}\n',
                    "expected_output": "Sum = 15",
                    "sample_input": "5 10",
                    "sample_output": "Sum = 15",
                    "xp_reward": 100,
                    "hints": ["Use scanf() to read inputs", "Use %d format specifier", "Use a + b"],
                    "progressive_hints": [
                        {"tier": 1, "title": "Variables", "text": "Declare two integer variables to store user inputs."},
                        {"tier": 2, "title": "Scanf address", "text": "Pass &a and &b to scanf()."},
                        {"tier": 3, "title": "Sum & Print", "text": "Compute sum = a + b and print with printf(\"Sum = %d\\n\", sum);"}
                    ],
                    "test_cases": [
                        {"input": "5 10", "expected": "Sum = 15", "is_hidden": False},
                        {"input": "100 250", "expected": "Sum = 350", "is_hidden": True},
                        {"input": "-10 20", "expected": "Sum = 10", "is_hidden": True}
                    ]
                },
                {
                    "id": 3,
                    "title": "Largest of Three",
                    "description": "Write a C program that reads three integers and prints the largest one in the format: Largest = X",
                    "difficulty": "easy",
                    "concepts": ["if", "else", "comparison"],
                    "starter_code": '#include <stdio.h>\n\nint main() {\n    int a, b, c;\n    if (scanf("%d %d %d", &a, &b, &c) == 3) {\n        int max = a;\n        if (b > max) max = b;\n        if (c > max) max = c;\n        printf("Largest = %d\\n", max);\n    }\n    return 0;\n}\n',
                    "expected_output": "Largest = 42",
                    "sample_input": "15 42 28",
                    "sample_output": "Largest = 42",
                    "xp_reward": 100,
                    "hints": ["Compare numbers using if statements", "Track the maximum value in a variable"],
                    "progressive_hints": [
                        {"tier": 1, "title": "Comparisons", "text": "A number is largest if it is greater than the other two."},
                        {"tier": 2, "title": "Logical AND", "text": "Check if (a >= b && a >= c) then 'a' is largest."},
                        {"tier": 3, "title": "Max Tracker", "text": "int max = (a > b) ? a : b; if (c > max) max = c;"}
                    ],
                    "test_cases": [
                        {"input": "15 42 28", "expected": "Largest = 42", "is_hidden": False},
                        {"input": "99 12 5", "expected": "Largest = 99", "is_hidden": True},
                        {"input": "1 1 10", "expected": "Largest = 10", "is_hidden": True}
                    ]
                },
                {
                    "id": 4,
                    "title": "Even or Odd",
                    "description": "Write a C program that reads an integer and prints \"Even\" or \"Odd\".",
                    "difficulty": "easy",
                    "concepts": ["if", "modulus", "operators"],
                    "starter_code": '#include <stdio.h>\n\nint main() {\n    int num;\n    if (scanf("%d", &num) == 1) {\n        if (num % 2 == 0) printf("Even\\n");\n        else printf("Odd\\n");\n    }\n    return 0;\n}\n',
                    "expected_output": "Even",
                    "sample_input": "4",
                    "sample_output": "Even",
                    "xp_reward": 100,
                    "hints": ["Use modulus operator % 2", "Even numbers have 0 remainder"],
                    "progressive_hints": [
                        {"tier": 1, "title": "Remainder", "text": "Divide by 2 and check if remainder is zero."},
                        {"tier": 2, "title": "Modulus", "text": "if (num % 2 == 0) for even."},
                        {"tier": 3, "title": "Bitwise option", "text": "if ((num & 1) == 0) for bitwise test."}
                    ],
                    "test_cases": [
                        {"input": "4", "expected": "Even", "is_hidden": False},
                        {"input": "7", "expected": "Odd", "is_hidden": True},
                        {"input": "0", "expected": "Even", "is_hidden": True}
                    ]
                },
                {
                    "id": 5,
                    "title": "Factorial Calculation",
                    "description": "Write a C program to calculate the factorial of a positive integer N in the format: Factorial = X",
                    "difficulty": "easy",
                    "concepts": ["loops", "for", "multiplication"],
                    "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1) {\n        long long fact = 1;\n        for (int i = 1; i <= n; i++) fact *= i;\n        printf("Factorial = %lld\\n", fact);\n    }\n    return 0;\n}\n',
                    "expected_output": "Factorial = 120",
                    "sample_input": "5",
                    "sample_output": "Factorial = 120",
                    "xp_reward": 100,
                    "hints": ["Use a loop from 1 to n", "Initialize fact = 1", "Use long long to prevent overflow"],
                    "progressive_hints": [
                        {"tier": 1, "title": "Loop Accumulator", "text": "Initialize accumulator to 1, loop from 1 to n."},
                        {"tier": 2, "title": "Step Multiplication", "text": "In each step: fact = fact * i."},
                        {"tier": 3, "title": "Format Specifier", "text": "Print with %lld for long long."}
                    ],
                    "test_cases": [
                        {"input": "5", "expected": "Factorial = 120", "is_hidden": False},
                        {"input": "3", "expected": "Factorial = 6", "is_hidden": True},
                        {"input": "6", "expected": "Factorial = 720", "is_hidden": True}
                    ]
                }
            ]

            for p_data in problems_data:
                test_cases = p_data.pop("test_cases", [])
                p_id = p_data["id"]
                req_input = p_id != 1 # Problem 1 (Hello World) does not require input
                allows_fixed = p_id == 1

                p = Problem(
                    id=p_id,
                    title=p_data["title"],
                    description=p_data["description"],
                    difficulty=p_data["difficulty"],
                    concepts=json.dumps(p_data["concepts"]),
                    starter_code=p_data["starter_code"],
                    expected_output=p_data["expected_output"],
                    sample_input=p_data.get("sample_input"),
                    sample_output=p_data.get("sample_output"),
                    xp_reward=p_data["xp_reward"],
                    hints=json.dumps(p_data["hints"]),
                    progressive_hints=json.dumps(p_data["progressive_hints"]),
                    requires_input=req_input,
                    allows_fixed_output=allows_fixed
                )
                db.add(p)
                db.flush()

                for tc in test_cases:
                    db.add(TestCase(
                        problem_id=p.id,
                        input_data=tc["input"],
                        expected_output=tc["expected"],
                        is_hidden=tc["is_hidden"]
                    ))

            db.commit()

        # 3. Seed Sample Write-Up & Exam
        if db.query(WriteUp).count() == 0:
            w = WriteUp(
                id=1,
                title="Week 04 Write-Up: Conditionals & Loops",
                description="Mandatory weekly laboratory assessment on C control flow structures, branch analysis, and iteration constraints.",
                topics="if-else, while, for loops, logic",
                duration_minutes=30,
                question_ids=json.dumps([3, 5]),
                ai_policy="limited",
                is_active=True
            )
            db.add(w)
            db.commit()

        if db.query(Exam).count() == 0:
            e = Exam(
                id=1,
                title="Mid-Term C Programming Practical Exam",
                description="Formal laboratory examination. Code will be executed against full hidden test suites. AI guidance is strictly disabled.",
                topics="Conditionals, Modulus, Iteration",
                duration_minutes=45,
                question_ids=json.dumps([2, 4]),
                is_active=True
            )
            db.add(e)
            db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    init_db_and_seed()
    print("Database initialized and seeded successfully.")
