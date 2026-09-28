"""
Database Layer & Auto-Seeding Engine
Supports PostgreSQL (Supabase) with zero-configuration SQLite local fallback.
Auto-initializes tables and seeds rich curriculum data (problems, test cases, users, writeups, exams, lab manuals).
"""

import os
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


# ── Database Connection Setup (Supabase PostgreSQL + SQLite Fallback) ────────

def _create_database_engine():
    """
    Creates SQLAlchemy engine supporting:
    1. Supabase PostgreSQL (via psycopg2-binary or pg8000)
    2. Zero-config SQLite local database fallback
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.strip():
        db_url = db_url.strip()
        # Normalize postgres:// to postgresql:// for SQLAlchemy compatibility
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        engine_kwargs = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }

        # Check SSL requirement for PostgreSQL / Supabase
        if "postgresql" in db_url and "sslmode" not in db_url:
            engine_kwargs["connect_args"] = {"sslmode": "require"}

        try:
            pg_engine = create_engine(db_url, **engine_kwargs)
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[DATABASE] Successfully connected to PostgreSQL (Supabase).")
            return pg_engine, db_url
        except Exception as e:
            print(f"[DATABASE WARNING] PostgreSQL connection failed: {e}")
            print("[DATABASE] Seamlessly falling back to local SQLite database.")
            logger.warning(f"Failed to connect to DATABASE_URL: {e}. Falling back to SQLite.")

    # SQLite fallback
    try:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, "ailab.db")
        # Test write permissions
        test_file = os.path.join(data_dir, ".write_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
    except (OSError, PermissionError):
        import tempfile
        data_dir = os.path.join(tempfile.gettempdir(), "ailab_data")
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, "ailab.db")

    sqlite_url = f"sqlite:///{db_path}"
    print(f"[DATABASE] Using SQLite database at: {db_path}")
    sqlite_engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False}
    )
    return sqlite_engine, sqlite_url


engine, DATABASE_URL = _create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── 1. Data Models ─────────────────────────────────────────────

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
    action = Column(String(64), nullable=False) # run, submit, debug_fix, writeup_start, tab_switch
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


class LabManual(Base):
    __tablename__ = "lab_manuals"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(String(64), index=True, nullable=False, default="FAC2024001")
    file_name = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processing_status = Column(String(32), default="completed") # processing, completed, failed, scanned_pdf
    total_detected_programs = Column(Integer, default=0)
    verified_programs = Column(Integer, default=0)

    programs = relationship("ManualProgram", back_populates="manual", cascade="all, delete-orphan")


class ManualProgram(Base):
    __tablename__ = "manual_programs"

    id = Column(Integer, primary_key=True, index=True)
    manual_id = Column(Integer, ForeignKey("lab_manuals.id"), nullable=False)
    program_number = Column(Integer, default=1)
    title = Column(String(256), nullable=False)
    problem_statement = Column(Text, nullable=False)
    objective = Column(Text, nullable=True)
    input_description = Column(Text, nullable=True)
    output_description = Column(Text, nullable=True)
    topic = Column(String(128), default="General C")
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    constraints = Column(Text, nullable=True)
    sample_input = Column(Text, nullable=True)
    sample_output = Column(Text, nullable=True)
    test_cases = Column(Text, default="[]") # JSON list of {"input": "...", "expected_output": "..."}
    reference_code = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)
    additional_requirements = Column(Text, nullable=True)
    validation_report = Column(Text, default="{}") # JSON dict of validation results
    extraction_confidence = Column(Float, default=0.9)
    faculty_verified = Column(Boolean, default=False)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    manual = relationship("LabManual", back_populates="programs")


class CodeSimilarityAnalysis(Base):
    __tablename__ = "code_similarity_analysis"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    student_id_1 = Column(String(64), index=True, nullable=False)
    student_id_2 = Column(String(64), index=True, nullable=False) # e.g. STU2024002 or "REFERENCE_CODE"
    submission_id_1 = Column(Integer, ForeignKey("submissions.id"), nullable=True)
    submission_id_2 = Column(Integer, ForeignKey("submissions.id"), nullable=True)
    similarity_percentage = Column(Float, default=0.0) # 0.0 to 100.0
    structural_similarity = Column(Float, default=0.0)
    token_similarity = Column(Float, default=0.0)
    matched_patterns = Column(Text, default="[]") # JSON list of matched tokens or fragments
    normalized_code_1 = Column(Text, nullable=True)
    normalized_code_2 = Column(Text, nullable=True)
    is_flagged = Column(Boolean, default=False)
    faculty_reviewed = Column(Boolean, default=False)
    review_status = Column(String(32), default="pending") # pending, flagged, dismissed, verified
    review_notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProgramTopic(Base):
    __tablename__ = "program_topics"

    id = Column(Integer, primary_key=True, index=True)
    manual_id = Column(Integer, ForeignKey("lab_manuals.id"), nullable=True)
    topic_name = Column(String(128), nullable=False)
    unit_number = Column(String(64), default="Unit 1")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProgramExtractionLog(Base):
    __tablename__ = "program_extraction_logs"

    id = Column(Integer, primary_key=True, index=True)
    manual_id = Column(Integer, ForeignKey("lab_manuals.id"), nullable=False)
    log_level = Column(String(16), default="info") # info, warning, error
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 2. Rich Curriculum Seeding Data ────────────────────────────

RICH_PROBLEMS = [
    {
        "id": 1,
        "title": "Hello, World!",
        "description": "Write a C program that prints \"Hello, World!\" to standard output.",
        "difficulty": "easy",
        "concepts": ["printf", "basics", "stdio.h"],
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
        "title": "Largest of Three Numbers",
        "description": "Write a C program that reads three integers and prints the largest one in the format: Largest = X",
        "difficulty": "easy",
        "concepts": ["if", "else", "comparison", "logic"],
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
        "title": "Even or Odd Number",
        "description": "Write a C program that reads an integer and prints \"Even\" if divisible by 2, or \"Odd\" otherwise.",
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
        "concepts": ["loops", "for", "multiplication", "accumulators"],
        "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1) {\n        long long fact = 1;\n        for (int i = 1; i <= n; i++) fact *= i;\n        printf("Factorial = %lld\\n", fact);\n    }\n    return 0;\n}\n',
        "expected_output": "Factorial = 120",
        "sample_input": "5",
        "sample_output": "Factorial = 120",
        "xp_reward": 120,
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
    },
    {
        "id": 6,
        "title": "Prime Number Checker",
        "description": "Write a C program that reads an integer N and prints \"Prime\" if it is a prime number, or \"Not Prime\" otherwise.",
        "difficulty": "medium",
        "concepts": ["loops", "conditions", "prime", "optimization"],
        "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1) {\n        if (n <= 1) { printf("Not Prime\\n"); return 0; }\n        int is_prime = 1;\n        for (int i = 2; i * i <= n; i++) {\n            if (n % i == 0) { is_prime = 0; break; }\n        }\n        if (is_prime) printf("Prime\\n");\n        else printf("Not Prime\\n");\n    }\n    return 0;\n}\n',
        "expected_output": "Prime",
        "sample_input": "7",
        "sample_output": "Prime",
        "xp_reward": 150,
        "hints": ["Check divisibility from 2 up to sqrt(N)", "Numbers <= 1 are Not Prime"],
        "progressive_hints": [
            {"tier": 1, "title": "Divisibility", "text": "A number is prime if it has no divisors other than 1 and itself."},
            {"tier": 2, "title": "Loop Limit", "text": "You only need to loop up to sqrt(N) to test divisors."},
            {"tier": 3, "title": "Flag Variable", "text": "Use a flag variable is_prime initialized to 1."}
        ],
        "test_cases": [
            {"input": "7", "expected": "Prime", "is_hidden": False},
            {"input": "12", "expected": "Not Prime", "is_hidden": True},
            {"input": "13", "expected": "Prime", "is_hidden": True},
            {"input": "1", "expected": "Not Prime", "is_hidden": True}
        ]
    },
    {
        "id": 7,
        "title": "Fibonacci Sequence Generator",
        "description": "Write a C program that reads N and prints the first N Fibonacci numbers separated by single spaces.",
        "difficulty": "medium",
        "concepts": ["loops", "sequence", "variables"],
        "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1) {\n        long long a = 0, b = 1;\n        for (int i = 0; i < n; i++) {\n            printf("%lld%s", a, (i == n - 1) ? "" : " ");\n            long long next = a + b;\n            a = b;\n            b = next;\n        }\n        printf("\\n");\n    }\n    return 0;\n}\n',
        "expected_output": "0 1 1 2 3",
        "sample_input": "5",
        "sample_output": "0 1 1 2 3",
        "xp_reward": 150,
        "hints": ["Start with a = 0, b = 1", "Compute next = a + b and shift variables"],
        "progressive_hints": [
            {"tier": 1, "title": "Base Values", "text": "Fibonacci starts with 0 and 1."},
            {"tier": 2, "title": "Shift Operation", "text": "In each step: next = a + b; a = b; b = next;"},
            {"tier": 3, "title": "Formatting", "text": "Print numbers separated by single spaces."}
        ],
        "test_cases": [
            {"input": "5", "expected": "0 1 1 2 3", "is_hidden": False},
            {"input": "3", "expected": "0 1 1", "is_hidden": True},
            {"input": "7", "expected": "0 1 1 2 3 5 8", "is_hidden": True}
        ]
    },
    {
        "id": 8,
        "title": "Reverse an Integer",
        "description": "Write a C program that reads an integer and prints its reverse in the format: Reversed = X",
        "difficulty": "medium",
        "concepts": ["while loop", "modulus", "division"],
        "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1) {\n        int rev = 0;\n        while (n != 0) {\n            rev = rev * 10 + n % 10;\n            n /= 10;\n        }\n        printf("Reversed = %d\\n", rev);\n    }\n    return 0;\n}\n',
        "expected_output": "Reversed = 4321",
        "sample_input": "1234",
        "sample_output": "Reversed = 4321",
        "xp_reward": 150,
        "hints": ["Extract last digit using n % 10", "Accumulate rev = rev * 10 + digit"],
        "progressive_hints": [
            {"tier": 1, "title": "Last Digit", "text": "n % 10 gives the last digit of n."},
            {"tier": 2, "title": "Truncate", "text": "n /= 10 removes the last digit."},
            {"tier": 3, "title": "Accumulator", "text": "Multiply existing reversed result by 10 and add last digit."}
        ],
        "test_cases": [
            {"input": "1234", "expected": "Reversed = 4321", "is_hidden": False},
            {"input": "987", "expected": "Reversed = 789", "is_hidden": True},
            {"input": "100", "expected": "Reversed = 1", "is_hidden": True}
        ]
    },
    {
        "id": 9,
        "title": "Swap Numbers Using Pointers",
        "description": "Write a C program that reads two integers, passes their memory addresses to a swap function, and prints: After Swap: a = X, b = Y",
        "difficulty": "medium",
        "concepts": ["pointers", "functions", "pass-by-reference"],
        "starter_code": '#include <stdio.h>\n\nvoid swap(int *x, int *y) {\n    int temp = *x;\n    *x = *y;\n    *y = temp;\n}\n\nint main() {\n    int a, b;\n    if (scanf("%d %d", &a, &b) == 2) {\n        swap(&a, &b);\n        printf("After Swap: a = %d, b = %d\\n", a, b);\n    }\n    return 0;\n}\n',
        "expected_output": "After Swap: a = 20, b = 10",
        "sample_input": "10 20",
        "sample_output": "After Swap: a = 20, b = 10",
        "xp_reward": 175,
        "hints": ["Pass address &a and &b to function", "Use dereference operator * to swap values"],
        "progressive_hints": [
            {"tier": 1, "title": "Pointer Parameters", "text": "Function signature should accept int *x, int *y."},
            {"tier": 2, "title": "Address Passing", "text": "Call swap(&a, &b) from main()."},
            {"tier": 3, "title": "Dereferencing", "text": "int temp = *x; *x = *y; *y = temp;"}
        ],
        "test_cases": [
            {"input": "10 20", "expected": "After Swap: a = 20, b = 10", "is_hidden": False},
            {"input": "5 100", "expected": "After Swap: a = 100, b = 5", "is_hidden": True},
            {"input": "-1 1", "expected": "After Swap: a = 1, b = -1", "is_hidden": True}
        ]
    },
    {
        "id": 10,
        "title": "Palindrome String Check",
        "description": "Write a C program that reads a single word string and prints \"Palindrome\" if it reads the same backward, or \"Not Palindrome\".",
        "difficulty": "hard",
        "concepts": ["strings", "pointers", "string.h"],
        "starter_code": '#include <stdio.h>\n#include <string.h>\n\nint main() {\n    char str[100];\n    if (scanf("%99s", str) == 1) {\n        int len = strlen(str);\n        int is_pal = 1;\n        for (int i = 0; i < len / 2; i++) {\n            if (str[i] != str[len - 1 - i]) { is_pal = 0; break; }\n        }\n        if (is_pal) printf("Palindrome\\n");\n        else printf("Not Palindrome\\n");\n    }\n    return 0;\n}\n',
        "expected_output": "Palindrome",
        "sample_input": "racecar",
        "sample_output": "Palindrome",
        "xp_reward": 200,
        "hints": ["Compare characters from front and back", "Include <string.h> for strlen()"],
        "progressive_hints": [
            {"tier": 1, "title": "String Length", "text": "Use strlen(str) to find length."},
            {"tier": 2, "title": "Two-Pointer Strategy", "text": "Compare str[i] with str[len - 1 - i]."},
            {"tier": 3, "title": "Early Exit", "text": "If characters mismatch, set flag = 0 and break."}
        ],
        "test_cases": [
            {"input": "racecar", "expected": "Palindrome", "is_hidden": False},
            {"input": "hello", "expected": "Not Palindrome", "is_hidden": True},
            {"input": "madam", "expected": "Palindrome", "is_hidden": True}
        ]
    },
    {
        "id": 11,
        "title": "Roots of Quadratic Equation",
        "description": "Write a C program that reads coefficients a, b, c of ax^2 + bx + c = 0 and computes roots. Format: Real and Distinct: Root1 = X, Root2 = Y | Real and Equal: Root = X | Complex Roots",
        "difficulty": "medium",
        "concepts": ["math.h", "sqrt", "if-else", "floating-point"],
        "starter_code": '#include <stdio.h>\n#include <math.h>\n\nint main() {\n    double a, b, c;\n    if (scanf("%lf %lf %lf", &a, &b, &c) == 3) {\n        double disc = b * b - 4 * a * c;\n        if (disc > 0) {\n            double r1 = (-b + sqrt(disc)) / (2 * a);\n            double r2 = (-b - sqrt(disc)) / (2 * a);\n            printf("Real and Distinct: Root1 = %.2f, Root2 = %.2f\\n", r1, r2);\n        } else if (disc == 0) {\n            double r = -b / (2 * a);\n            printf("Real and Equal: Root = %.2f\\n", r);\n        } else {\n            printf("Complex Roots\\n");\n        }\n    }\n    return 0;\n}\n',
        "expected_output": "Real and Distinct: Root1 = 3.00, Root2 = 2.00",
        "sample_input": "1 -5 6",
        "sample_output": "Real and Distinct: Root1 = 3.00, Root2 = 2.00",
        "xp_reward": 180,
        "hints": ["Discriminant = b*b - 4*a*c", "Include <math.h> and use sqrt()"],
        "progressive_hints": [
            {"tier": 1, "title": "Discriminant Calculation", "text": "Calculate disc = b*b - 4*a*c."},
            {"tier": 2, "title": "Branch on Discriminant", "text": "If disc > 0: two real roots; if disc == 0: one repeated root; else: complex roots."},
            {"tier": 3, "title": "Formula", "text": "r1 = (-b + sqrt(disc))/(2*a); r2 = (-b - sqrt(disc))/(2*a);"}
        ],
        "test_cases": [
            {"input": "1 -5 6", "expected": "Real and Distinct: Root1 = 3.00, Root2 = 2.00", "is_hidden": False},
            {"input": "1 -4 4", "expected": "Real and Equal: Root = 2.00", "is_hidden": True},
            {"input": "1 2 5", "expected": "Complex Roots", "is_hidden": True}
        ]
    },
    {
        "id": 12,
        "title": "Matrix Addition (2D Arrays)",
        "description": "Write a C program to read dimensions R, C followed by two R x C integer matrices and print their sum matrix.",
        "difficulty": "medium",
        "concepts": ["2D Arrays", "nested loops", "matrices"],
        "starter_code": '#include <stdio.h>\n\nint main() {\n    int r, c;\n    if (scanf("%d %d", &r, &c) == 2) {\n        int a[20][20], b[20][20], sum[20][20];\n        for (int i = 0; i < r; i++) for (int j = 0; j < c; j++) scanf("%d", &a[i][j]);\n        for (int i = 0; i < r; i++) for (int j = 0; j < c; j++) scanf("%d", &b[i][j]);\n        for (int i = 0; i < r; i++) {\n            for (int j = 0; j < c; j++) {\n                sum[i][j] = a[i][j] + b[i][j];\n                printf("%d%s", sum[i][j], (j == c - 1) ? "" : " ");\n            }\n            printf("\\n");\n        }\n    }\n    return 0;\n}\n',
        "expected_output": "6 8\n10 12",
        "sample_input": "2 2\n1 2\n3 4\n5 6\n7 8",
        "sample_output": "6 8\n10 12",
        "xp_reward": 180,
        "hints": ["Use 2D arrays int a[20][20]", "Nested for loops for row (i) and column (j)"],
        "progressive_hints": [
            {"tier": 1, "title": "Matrix Dimensions", "text": "Scan row count r and col count c."},
            {"tier": 2, "title": "Nested Scan", "text": "Loop i from 0 to r-1 and j from 0 to c-1 to scan elements."},
            {"tier": 3, "title": "Element-wise Sum", "text": "sum[i][j] = a[i][j] + b[i][j];"}
        ],
        "test_cases": [
            {"input": "2 2\n1 2\n3 4\n5 6\n7 8", "expected": "6 8\n10 12", "is_hidden": False},
            {"input": "1 3\n10 20 30\n5 5 5", "expected": "15 25 35", "is_hidden": True}
        ]
    },
    {
        "id": 13,
        "title": "Linear Search in Array",
        "description": "Write a C program that reads N, an array of N integers, and a search key K. Print \"Found at Index X\" (0-indexed) or \"Not Found\".",
        "difficulty": "easy",
        "concepts": ["arrays", "linear search", "loops"],
        "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1) {\n        int arr[100];\n        for (int i = 0; i < n; i++) scanf("%d", &arr[i]);\n        int key;\n        if (scanf("%d", &key) == 1) {\n            int found_idx = -1;\n            for (int i = 0; i < n; i++) {\n                if (arr[i] == key) { found_idx = i; break; }\n            }\n            if (found_idx != -1) printf("Found at Index %d\\n", found_idx);\n            else printf("Not Found\\n");\n        }\n    }\n    return 0;\n}\n',
        "expected_output": "Found at Index 2",
        "sample_input": "5\n10 20 30 40 50\n30",
        "sample_output": "Found at Index 2",
        "xp_reward": 120,
        "hints": ["Traverse array sequentially", "Break immediately upon finding key"],
        "progressive_hints": [
            {"tier": 1, "title": "Array Scan", "text": "Read N elements into int arr[n]."},
            {"tier": 2, "title": "Traversal", "text": "Compare arr[i] with key in a for loop."},
            {"tier": 3, "title": "Found / Not Found", "text": "Track index with found_idx initialized to -1."}
        ],
        "test_cases": [
            {"input": "5\n10 20 30 40 50\n30", "expected": "Found at Index 2", "is_hidden": False},
            {"input": "4\n1 3 5 7\n9", "expected": "Not Found", "is_hidden": True},
            {"input": "3\n100 200 300\n100", "expected": "Found at Index 0", "is_hidden": True}
        ]
    },
    {
        "id": 14,
        "title": "Bubble Sort Algorithm",
        "description": "Write a C program that reads N and an array of N integers, sorts them in ascending order using Bubble Sort, and prints the sorted array separated by spaces.",
        "difficulty": "medium",
        "concepts": ["arrays", "bubble sort", "nested loops", "swapping"],
        "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1 && n > 0) {\n        int arr[100];\n        for (int i = 0; i < n; i++) scanf("%d", &arr[i]);\n        for (int i = 0; i < n - 1; i++) {\n            for (int j = 0; j < n - i - 1; j++) {\n                if (arr[j] > arr[j + 1]) {\n                    int temp = arr[j];\n                    arr[j] = arr[j + 1];\n                    arr[j + 1] = temp;\n                }\n            }\n        }\n        for (int i = 0; i < n; i++) printf("%d%s", arr[i], (i == n - 1) ? "" : " ");\n        printf("\\n");\n    }\n    return 0;\n}\n',
        "expected_output": "11 12 22 25 34 64 90",
        "sample_input": "7\n64 34 25 12 22 11 90",
        "sample_output": "11 12 22 25 34 64 90",
        "xp_reward": 180,
        "hints": ["Compare adjacent elements arr[j] and arr[j+1]", "Swap if arr[j] > arr[j+1]"],
        "progressive_hints": [
            {"tier": 1, "title": "Outer & Inner Loop", "text": "Outer loop runs n-1 times; inner loop runs n-i-1 times."},
            {"tier": 2, "title": "Adjacent Comparison", "text": "if (arr[j] > arr[j+1]) swap them."},
            {"tier": 3, "title": "Sorted Output", "text": "Print final array with single space delimiters."}
        ],
        "test_cases": [
            {"input": "7\n64 34 25 12 22 11 90", "expected": "11 12 22 25 34 64 90", "is_hidden": False},
            {"input": "4\n5 1 4 2", "expected": "1 2 4 5", "is_hidden": True},
            {"input": "3\n9 3 1", "expected": "1 3 9", "is_hidden": True}
        ]
    },
    {
        "id": 15,
        "title": "Greatest Common Divisor (GCD) using Recursion",
        "description": "Write a C program that reads two positive integers a and b, computes their GCD using a recursive function (Euclidean algorithm), and prints: GCD = X",
        "difficulty": "medium",
        "concepts": ["recursion", "functions", "euclidean algorithm"],
        "starter_code": '#include <stdio.h>\n\nint gcd(int a, int b) {\n    if (b == 0) return a;\n    return gcd(b, a % b);\n}\n\nint main() {\n    int a, b;\n    if (scanf("%d %d", &a, &b) == 2) {\n        printf("GCD = %d\\n", gcd(a, b));\n    }\n    return 0;\n}\n',
        "expected_output": "GCD = 12",
        "sample_input": "48 180",
        "sample_output": "GCD = 12",
        "xp_reward": 160,
        "hints": ["Euclidean algorithm: gcd(a, b) = gcd(b, a % b)", "Base case is when b == 0"],
        "progressive_hints": [
            {"tier": 1, "title": "Base Case", "text": "If b == 0, return a."},
            {"tier": 2, "title": "Recursive Step", "text": "Call return gcd(b, a % b);"},
            {"tier": 3, "title": "Output Format", "text": "Print GCD = %d with newline."}
        ],
        "test_cases": [
            {"input": "48 180", "expected": "GCD = 12", "is_hidden": False},
            {"input": "10 5", "expected": "GCD = 5", "is_hidden": True},
            {"input": "17 19", "expected": "GCD = 1", "is_hidden": True}
        ]
    },
    {
        "id": 16,
        "title": "Student Record Management (Structures)",
        "description": "Write a C program defining a struct Student (roll, name, marks). Read the student details and print: Roll: X | Name: Y | Marks: Z | Status: Pass/Fail (Pass if marks >= 40.0)",
        "difficulty": "hard",
        "concepts": ["structures", "struct", "typedef", "strings"],
        "starter_code": '#include <stdio.h>\n\nstruct Student {\n    int roll;\n    char name[50];\n    float marks;\n};\n\nint main() {\n    struct Student s;\n    if (scanf("%d %49s %f", &s.roll, s.name, &s.marks) == 3) {\n        printf("Roll: %d | Name: %s | Marks: %.1f | Status: %s\\n",\n               s.roll, s.name, s.marks, (s.marks >= 40.0f) ? "Pass" : "Fail");\n    }\n    return 0;\n}\n',
        "expected_output": "Roll: 101 | Name: Alice | Marks: 85.5 | Status: Pass",
        "sample_input": "101 Alice 85.5",
        "sample_output": "Roll: 101 | Name: Alice | Marks: 85.5 | Status: Pass",
        "xp_reward": 200,
        "hints": ["Define struct Student { int roll; char name[50]; float marks; };", "Use dot operator s.roll"],
        "progressive_hints": [
            {"tier": 1, "title": "Struct Declaration", "text": "Declare struct Student with roll, name, and marks members."},
            {"tier": 2, "title": "Member Scanning", "text": "Scan with scanf(\"%d %s %f\", &s.roll, s.name, &s.marks)."},
            {"tier": 3, "title": "Status Evaluation", "text": "Check (s.marks >= 40.0f) ? \"Pass\" : \"Fail\"."}
        ],
        "test_cases": [
            {"input": "101 Alice 85.5", "expected": "Roll: 101 | Name: Alice | Marks: 85.5 | Status: Pass", "is_hidden": False},
            {"input": "102 Bob 35.0", "expected": "Roll: 102 | Name: Bob | Marks: 35.0 | Status: Fail", "is_hidden": True},
            {"input": "103 Charlie 40.0", "expected": "Roll: 103 | Name: Charlie | Marks: 40.0 | Status: Pass", "is_hidden": True}
        ]
    }
]

RICH_WRITEUPS = [
    {
        "id": 1,
        "title": "Week 01 Write-Up: Basic C Syntax & Arithmetic Expressions",
        "description": "Weekly lab assessment covering stdio header inclusion, variable declarations, scanf input handling, and basic arithmetic computation.",
        "topics": "printf, scanf, variables, arithmetic",
        "duration_minutes": 25,
        "question_ids": [1, 2],
        "ai_policy": "limited"
    },
    {
        "id": 2,
        "title": "Week 02 Write-Up: Conditional Logic & Branching",
        "description": "Assessment on if-else branching, relational operators, nested conditionals, and decision-making logic in C.",
        "topics": "if-else, comparison, modulus, branching",
        "duration_minutes": 30,
        "question_ids": [3, 4],
        "ai_policy": "limited"
    },
    {
        "id": 3,
        "title": "Week 03 Write-Up: Iteration & Accumulator Loops",
        "description": "Assessment on for loops, while loops, accumulator variables, and mathematical iterations.",
        "topics": "for, while, factorial, integer reversal",
        "duration_minutes": 35,
        "question_ids": [5, 8],
        "ai_policy": "limited"
    },
    {
        "id": 4,
        "title": "Week 04 Write-Up: Prime Numbers & Fibonacci Sequences",
        "description": "Mandatory laboratory write-up on algorithm optimization, prime divisor boundary checks, and sequential series generation.",
        "topics": "prime checks, fibonacci, loop optimizations",
        "duration_minutes": 40,
        "question_ids": [6, 7],
        "ai_policy": "limited"
    },
    {
        "id": 5,
        "title": "Week 05 Write-Up: 1D Arrays & Memory Pointers",
        "description": "Assessment on array traversals, pointer memory addresses, dereferencing, and pass-by-reference functions.",
        "topics": "pointers, arrays, linear search, memory manipulation",
        "duration_minutes": 45,
        "question_ids": [9, 13],
        "ai_policy": "limited"
    }
]

RICH_EXAMS = [
    {
        "id": 1,
        "title": "Mid-Term C Programming Practical Exam",
        "description": "Formal laboratory examination. Code will be executed against full hidden test suites. AI guidance is strictly disabled.",
        "topics": "Conditionals, Modulus, Prime Checking",
        "duration_minutes": 45,
        "question_ids": [2, 4, 6]
    },
    {
        "id": 2,
        "title": "Final C Laboratory Practical Examination",
        "description": "Comprehensive semester-end laboratory practical exam. Covers strings, 2D arrays, and sorting algorithms. Proctored environment with strict anti-cheat monitoring.",
        "topics": "Strings, 2D Matrices, Bubble Sort",
        "duration_minutes": 60,
        "question_ids": [10, 12, 14]
    }
]

SAMPLE_MANUAL_PROGRAMS = [
    {
        "program_number": 1,
        "title": "Roots of a Quadratic Equation",
        "objective": "To write a C program that computes the roots of a quadratic equation ax^2 + bx + c = 0.",
        "problem_statement": "Write a C program to find the roots of a quadratic equation ax^2 + bx + c = 0 for given coefficients a, b, and c. Handle real and distinct roots, real and equal roots, and complex roots.",
        "input_description": "Three space-separated floating-point numbers a, b, c.",
        "output_description": "Print root classification and root values formatted to two decimal places.",
        "topic": "Conditionals & Math Library",
        "input_format": "%lf %lf %lf",
        "output_format": "Formatted text with %.2f precision",
        "constraints": "a != 0",
        "sample_input": "1 -5 6",
        "sample_output": "Real and Distinct: Root1 = 3.00, Root2 = 2.00",
        "expected_output": "Real and Distinct: Root1 = 3.00, Root2 = 2.00",
        "test_cases": [
            {"input": "1 -5 6", "expected_output": "Real and Distinct: Root1 = 3.00, Root2 = 2.00"},
            {"input": "1 -4 4", "expected_output": "Real and Equal: Root = 2.00"}
        ],
        "reference_code": '#include <stdio.h>\n#include <math.h>\n\nint main() {\n    double a, b, c;\n    if (scanf("%lf %lf %lf", &a, &c, &c) == 3) {\n        double d = b*b - 4*a*c;\n        if (d > 0) printf("Real and Distinct\\n");\n        else if (d == 0) printf("Real and Equal\\n");\n        else printf("Complex Roots\\n");\n    }\n    return 0;\n}\n',
        "faculty_verified": True,
        "published": True
    },
    {
        "program_number": 2,
        "title": "Matrix Addition and Subtraction",
        "objective": "To implement matrix addition and subtraction on 2D integer matrices.",
        "problem_statement": "Write a C program to read two matrices of order R x C and compute their sum matrix.",
        "input_description": "First line: R C. Next R lines: Matrix A. Next R lines: Matrix B.",
        "output_description": "R lines representing the sum matrix elements separated by spaces.",
        "topic": "2D Arrays & Matrices",
        "input_format": "%d %d followed by R*C integers",
        "output_format": "Matrix grid",
        "constraints": "1 <= R, C <= 20",
        "sample_input": "2 2\n1 2\n3 4\n5 6\n7 8",
        "sample_output": "6 8\n10 12",
        "expected_output": "6 8\n10 12",
        "test_cases": [
            {"input": "2 2\n1 2\n3 4\n5 6\n7 8", "expected_output": "6 8\n10 12"}
        ],
        "reference_code": '#include <stdio.h>\nint main() {\n    int r, c, a[10][10], b[10][10];\n    scanf("%d%d", &r, &c);\n    for(int i=0;i<r;i++) for(int j=0;j<c;j++) scanf("%d",&a[i][j]);\n    for(int i=0;i<r;i++) for(int j=0;j<c;j++) scanf("%d",&b[i][j]);\n    for(int i=0;i<r;i++) {\n        for(int j=0;j<c;j++) printf("%d ", a[i][j]+b[i][j]);\n        printf("\\n");\n    }\n    return 0;\n}\n',
        "faculty_verified": True,
        "published": True
    },
    {
        "program_number": 3,
        "title": "Bubble Sort on Linear Array",
        "objective": "To sort N integers in ascending order using the Bubble Sort algorithm.",
        "problem_statement": "Write a C program that accepts N numbers and sorts them in ascending order using Bubble Sort.",
        "input_description": "N followed by N space-separated integers.",
        "output_description": "Sorted elements separated by single spaces.",
        "topic": "Arrays & Sorting",
        "input_format": "%d followed by N integers",
        "output_format": "Space-separated sorted integers",
        "constraints": "1 <= N <= 100",
        "sample_input": "5\n50 20 40 10 30",
        "sample_output": "10 20 30 40 50",
        "expected_output": "10 20 30 40 50",
        "test_cases": [
            {"input": "5\n50 20 40 10 30", "expected_output": "10 20 30 40 50"}
        ],
        "reference_code": '#include <stdio.h>\nint main() {\n    int n, a[100];\n    scanf("%d", &n);\n    for(int i=0; i<n; i++) scanf("%d", &a[i]);\n    for(int i=0; i<n-1; i++) for(int j=0; j<n-i-1; j++)\n        if(a[j]>a[j+1]) { int t=a[j]; a[j]=a[j+1]; a[j+1]=t; }\n    for(int i=0; i<n; i++) printf("%d ", a[i]);\n    printf("\\n");\n    return 0;\n}\n',
        "faculty_verified": True,
        "published": True
    }
]


# ── 3. Database Initialization & Auto-Seeding Engine ───────────

def init_db_and_seed():
    """
    Creates database schema across PostgreSQL (Supabase) or SQLite,
    applies safe schema updates, and auto-seeds curriculum data.
    """
    # 1. Create all tables
    Base.metadata.create_all(bind=engine)

    # 2. Safely apply column additions if tables already existed
    is_sqlite = "sqlite" in str(engine.url)
    with engine.connect() as conn:
        migrations = [
            ("problems", "requires_input", "BOOLEAN DEFAULT TRUE" if not is_sqlite else "BOOLEAN DEFAULT 1"),
            ("problems", "allows_fixed_output", "BOOLEAN DEFAULT FALSE" if not is_sqlite else "BOOLEAN DEFAULT 0"),
            ("manual_programs", "objective", "TEXT"),
            ("manual_programs", "input_description", "TEXT"),
            ("manual_programs", "output_description", "TEXT"),
            ("manual_programs", "test_cases", "TEXT DEFAULT '[]'"),
            ("manual_programs", "expected_output", "TEXT"),
            ("manual_programs", "additional_requirements", "TEXT"),
            ("manual_programs", "validation_report", "TEXT DEFAULT '{}'"),
        ]
        for tbl, col, col_def in migrations:
            try:
                if is_sqlite:
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}"))
                else:
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS {col} {col_def}"))
                conn.commit()
            except Exception:
                pass

    db = SessionLocal()
    try:
        # 1. Seed Users if not present
        if db.query(User).count() == 0:
            default_users = [
                User(user_id="STU2024001", full_name="Suravi R", role="student", current_xp=2840, level=8, rank="Code Architect", streak_days=5, section="A"),
                User(user_id="STU2024002", full_name="Rahul M", role="student", current_xp=2200, level=6, rank="Debugger", streak_days=3, section="A"),
                User(user_id="STU2024003", full_name="Priya K", role="student", current_xp=3450, level=10, rank="Problem Solver", streak_days=7, section="A"),
                User(user_id="STU2024004", full_name="Amit S", role="student", current_xp=950, level=3, rank="Explorer", streak_days=1, section="B"),
                User(user_id="STU2024005", full_name="Ananya D", role="student", current_xp=2600, level=7, rank="Code Crafter", streak_days=4, section="A"),
                User(user_id="STU2024006", full_name="Vikram T", role="student", current_xp=1800, level=5, rank="Logic Builder", streak_days=2, section="B"),
                User(user_id="FAC2024001", full_name="Dr. Anand Kumar", role="faculty", email="anand.kumar@college.edu"),
                User(user_id="FAC2024002", full_name="Prof. Meenakshi S", role="faculty", email="meenakshi.s@college.edu")
            ]
            db.add_all(default_users)
            db.commit()

        # 2. Seed Problems & Test Cases
        if db.query(Problem).count() == 0:
            for p_data in RICH_PROBLEMS:
                test_cases = p_data.get("test_cases", [])
                p_id = p_data["id"]
                req_input = p_id != 1
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

        # 3. Seed Write-Ups
        if db.query(WriteUp).count() == 0:
            for w_data in RICH_WRITEUPS:
                w = WriteUp(
                    id=w_data["id"],
                    title=w_data["title"],
                    description=w_data["description"],
                    topics=w_data["topics"],
                    duration_minutes=w_data["duration_minutes"],
                    question_ids=json.dumps(w_data["question_ids"]),
                    ai_policy=w_data.get("ai_policy", "limited"),
                    is_active=True
                )
                db.add(w)
            db.commit()

        # 4. Seed Exams
        if db.query(Exam).count() == 0:
            for e_data in RICH_EXAMS:
                e = Exam(
                    id=e_data["id"],
                    title=e_data["title"],
                    description=e_data["description"],
                    topics=e_data["topics"],
                    duration_minutes=e_data["duration_minutes"],
                    question_ids=json.dumps(e_data["question_ids"]),
                    is_active=True
                )
                db.add(e)
            db.commit()

        # 5. Seed Pre-loaded Verified Lab Manual for Faculty Portal
        if db.query(LabManual).count() == 0:
            manual = LabManual(
                id=1,
                faculty_id="FAC2024001",
                file_name="CS101_Programming_in_C_Lab_Manual.pdf",
                file_path="/manuals/CS101_Programming_in_C_Lab_Manual.pdf",
                processing_status="completed",
                total_detected_programs=len(SAMPLE_MANUAL_PROGRAMS),
                verified_programs=len(SAMPLE_MANUAL_PROGRAMS)
            )
            db.add(manual)
            db.flush()

            for prog in SAMPLE_MANUAL_PROGRAMS:
                mp = ManualProgram(
                    manual_id=manual.id,
                    program_number=prog["program_number"],
                    title=prog["title"],
                    objective=prog["objective"],
                    problem_statement=prog["problem_statement"],
                    input_description=prog["input_description"],
                    output_description=prog["output_description"],
                    topic=prog["topic"],
                    input_format=prog["input_format"],
                    output_format=prog["output_format"],
                    constraints=prog["constraints"],
                    sample_input=prog["sample_input"],
                    sample_output=prog["sample_output"],
                    test_cases=json.dumps(prog["test_cases"]),
                    reference_code=prog["reference_code"],
                    expected_output=prog["expected_output"],
                    faculty_verified=prog["faculty_verified"],
                    published=prog["published"]
                )
                db.add(mp)

            # Add Topics
            db.add(ProgramTopic(manual_id=manual.id, topic_name="Conditionals & Math Library", unit_number="Unit 2"))
            db.add(ProgramTopic(manual_id=manual.id, topic_name="2D Arrays & Matrices", unit_number="Unit 4"))
            db.add(ProgramTopic(manual_id=manual.id, topic_name="Arrays & Sorting", unit_number="Unit 4"))
            db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    init_db_and_seed()
    print("Database schema created and rich curriculum data seeded successfully.")
