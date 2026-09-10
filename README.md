# SMART LAB: An Intelligent Programming Assessment & Error Explanation System

SMART LAB is a comprehensive, AI-powered C programming laboratory management, automated assessment, and intelligent debugging guidance platform designed for university laboratory courses.

---

## Key Features

1. **Local GCC/MinGW C Compilation & Execution Pipeline**
   - Direct subprocess execution of C code using standard GCC.
   - Unique temporary file isolation with automatic cleanup.
   - Execution timeout limits (prevents infinite loops) and stdin piping.
   - Zero AI overhead on clean execution (Groq API is bypassed on success).

2. **Groq AI Educational Error Guidance**
   - Captures raw compiler `stderr` and maps error tokens.
   - Intelligent heuristic line detection (pinpoints unclosed braces or missing semicolons on preceding lines).
   - Generates point-wise explanations: **What went wrong**, **Why it happened**, and **Step-by-step how to fix**.
   - Strict pedagogical constraints: **Never gives away the full solution or copy-paste code**.

3. **Multi-Tier Test Case Verification**
   - Public and hidden test cases evaluated independently.
   - Whitespace and output normalization.
   - Accepts different valid algorithms (e.g. ternary operators, pointer arithmetic, custom functions).

4. **Anti-Hardcoding & Static AST Analysis**
   - Detects constant `printf` statements matching expected outputs when user input (`scanf`) was required.
   - Assigns a hardcoding risk score and flags submissions for faculty review without punitive false accusations.

5. **Faculty PDF Lab Manual Extraction**
   - Upload college laboratory syllabus manuals as PDF documents.
   - Automatically extracts distinct programming experiments, aims, input/output descriptions, test cases, and reference code.
   - Faculty verification queue: extracted programs must be reviewed and approved before becoming student-visible.

6. **Weekly Write-Up & Examination Modes**
   - **Weekly Write-Ups**: Timed session with draft auto-saving and authentic multi-problem grading.
   - **Examination Mode**: AI debugging guidance is strictly blocked by the backend, enforcing independent student performance.

7. **Student Progress & Faculty Telemetry**
   - Dynamic concept mastery tracking (Variables & I/O, Conditionals, Loops, Arrays, Functions, Pointers).
   - Faculty command console with class average, difficult concept failure rates, and anti-cheating tab-switch event logs.

---

## Architecture Pipeline

```text
STUDENT WORKFLOW:
Student Browser ───► POST /api/compiler/run ───► FastAPI Backend
                                                        │
                                                        ▼
                                                 Temporary .c File
                                                        │
                                                        ▼
                                                   GCC / MinGW
                                                        │
                              ┌─────────────────────────┴─────────────────────────┐
                              ▼                                                   ▼
                     Compilation Error                                    Compilation Success
                              │                                                   │
                              ▼                                                   ▼
                     Extract Stderr & Line                               Execute Binary with Stdin
                              │                                                   │
                              ▼                                                   ▼
                    Groq LLM Diagnostics                                Capture Actual Stdout
                              │                                                   │
                              ▼                                                   ▼
                     Point-Wise Guidance                                Test Cases Evaluation
                     (What/Why/How to Fix)                                        │
                              │                                                   ▼
                              └─────────────────────────┬─────────────────────────┘
                                                        │
                                                        ▼
                                              Structured JSON Output
                                                        │
                                                        ▼
                                              Student UI Diagnostics
```

---

## Technology Stack

- **Frontend**: HTML5, Vanilla CSS (Design System Tokens), JavaScript (ES6+), CodeMirror 5, Three.js (Particle backgrounds & core sphere), GSAP.
- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic, SQLAlchemy.
- **Compiler Toolchain**: GCC (MSYS2 / MinGW-w64 on Windows, `gcc` on Linux/macOS).
- **AI Engine**: Groq Cloud API (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`, `groq/compound`).
- **Database**: SQLite (local zero-configuration) or PostgreSQL (Supabase).

---

## Prerequisites & Installation

### 1. Install GCC / MinGW
Ensure `gcc` is installed and added to your system `PATH`.
Verify in terminal:
```bash
gcc --version
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the project root or in `backend/`:
```env
# Required for AI Error Explanations
GROQ_API_KEY=gsk_your_groq_api_key_here

# Optional: Supabase PostgreSQL (leave unset to use local SQLite data/ailab.db)
# DATABASE_URL=postgresql://user:password@host:5432/dbname

PORT=8000
```

---

## Running the Application Locally

### Method A: Start Script (Windows)
Double-click or run:
```cmd
start.bat
```

### Method B: Manual Command
```bash
python main.py
```
Or directly with Uvicorn:
```bash
uvicorn app:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

Once started, open your browser at:
- **Application URL**: `http://localhost:8000`
- **Interactive API Docs**: `http://localhost:8000/docs`

---

## Running Integration Tests

Run the complete 11-stage integration test suite:
```bash
python backend/test_suite.py
```

All 11 workflows will be executed and verified end-to-end:
```text
test_01_correct_c_program ... ok
test_02_compilation_error_groq_guidance ... ok
test_03_runtime_timeout ... ok
test_04_wrong_logic_test_failure ... ok
test_05_hardcoded_output_detection ... ok
test_06_different_valid_solutions_accepted ... ok
test_07_pdf_manual_extraction ... ok
test_08_practice_challenge_generation ... ok
test_09_student_progress_metrics ... ok
test_10_writeup_workflow ... ok
test_11_exam_workflow ... ok
```

---

## API Reference Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate student or faculty profile |
| `GET` | `/api/problems` | List active laboratory problem bank entries |
| `GET` | `/api/problems/{id}` | Detail view of problem with starter code & hints |
| `POST` | `/api/compiler/run` | Compile & run C code against sample input |
| `POST` | `/api/submissions` | Submit solution for full test-case grading |
| `GET` | `/api/student/progress` | Dynamic concept mastery breakdown & submission history |
| `GET` | `/api/faculty/dashboard` | Class performance analytics, difficult concepts, activity logs |
| `POST` | `/api/faculty/manual/upload` | Upload & extract PDF laboratory manual |
| `POST` | `/api/faculty/problems/create` | Manually author problem statements and test suites |
| `POST` | `/api/writeups/{id}/start` | Start/resume timed weekly write-up session |
| `POST` | `/api/writeups/{id}/submit` | Grade and store weekly write-up |
| `POST` | `/api/exams/{id}/start` | Start proctored examination (AI disabled) |
| `POST` | `/api/exams/{id}/submit` | Submit and grade practical examination |
| `POST` | `/api/practice/challenge` | Generate adaptive AI practice challenge |

---

## Security & Sandboxing Considerations

1. **Subprocess Isolation**: Student programs are executed via isolated child processes with strict execution timeouts (default 10s).
2. **Resource Constraints**: Long-running loops or malicious recursion are terminated before exhausting system resources.
3. **Production Deployment**: For production web deployment, containerized isolation (such as Docker or gVisor) is recommended to prevent host filesystem access from arbitrary C binaries.
