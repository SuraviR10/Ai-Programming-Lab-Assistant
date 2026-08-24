"""
System Integration Test Suite — AI-Powered Intelligent C Programming Lab
Executes local verification for:
1. GCC Compiler toolchain execution
2. Groq AI Error Tutor & model fallback
3. Conditional execution (No Groq API call on compilation success)
4. Anti-Hardcoding AST analysis & Groq semantic verification
5. Faculty suspicious submission review endpoints
"""

import os
import json
from fastapi.testclient import TestClient
from app import app
from database import init_db_and_seed
from services.groq_service import analyze_compiler_error

print("Initializing Database & Auto-Seeding...")
init_db_and_seed()

client = TestClient(app)


def test_clean_compilation_no_groq():
    print("\n--- 1. Testing Program WITHOUT Errors (Direct GCC Output, No Groq Call) ---")
    valid_c = '#include <stdio.h>\nint main() {\n    printf("Output: 42\\n");\n    return 0;\n}'
    res = client.post("/api/compiler/run", json={"code": valid_c, "mode": "practice"}).json()

    print("Success:", res.get("success"))
    print("Output:", res.get("output"))
    print("AI Feedback Present:", "ai_feedback" in res)

    assert res.get("success") is True
    assert res.get("output").strip() == "Output: 42"
    assert "ai_feedback" not in res
    print("PASSED: Direct GCC output returned, Groq API bypassed cleanly.")


def test_syntax_error_groq_instructions():
    print("\n--- 2. Testing Program WITH Syntax Error (Groq Instructional Guidance) ---")
    error_c = '#include <stdio.h>\nint main() {\n    printf("Hello World")\n    return 0;\n}'
    res = client.post("/api/compiler/run", json={"code": error_c, "mode": "practice"}).json()

    print("Success:", res.get("success"))
    print("Line:", res.get("line"))
    print("AI Explanation:", res.get("ai_feedback", {}).get("explanation"))
    print("AI Hint:", res.get("ai_feedback", {}).get("hint"))
    print("AI Concept:", res.get("ai_feedback", {}).get("concept"))

    assert res.get("success") is False
    assert "ai_feedback" in res
    assert res.get("ai_feedback", {}).get("ai_disabled") is False
    print("PASSED: Syntax error detected and Groq guidance instructions generated.")


def test_anti_hardcoding_and_creativity():
    print("\n--- 3. Testing Anti-Hardcoding & Creativity Recognition ---")
    # Hello World (no input required)
    hello_c = '#include <stdio.h>\nint main() { printf("Hello, World!\\n"); return 0; }'
    r_hello = client.post("/api/submissions", json={"student_id": "STU2024001", "problem_id": 1, "code": hello_c}).json()
    assert r_hello.get("is_hardcoded") is False
    assert r_hello.get("score") == 10.0

    # Hardcoded Sum solution
    fake_sum_c = '#include <stdio.h>\nint main() { printf("Sum = 15\\n"); return 0; }'
    r_fake = client.post("/api/submissions", json={"student_id": "STU2024001", "problem_id": 2, "code": fake_sum_c}).json()
    assert r_fake.get("is_hardcoded") is True
    assert r_fake.get("status") == "POTENTIALLY_HARDCODED"

    # Creative Even/Odd solution
    creative_c = '#include <stdio.h>\nint main() { int n; if(scanf("%d", &n)==1) { if((n & 1) == 0) printf("Even\\n"); else printf("Odd\\n"); } return 0; }'
    r_creative = client.post("/api/submissions", json={"student_id": "STU2024001", "problem_id": 4, "code": creative_c}).json()
    assert r_creative.get("is_creative") is True
    assert r_creative.get("xp_earned") >= 150

    print("PASSED: Anti-hardcoding and creativity checks verified.")


def test_faculty_suspicious_review():
    print("\n--- 4. Testing Faculty Suspicious Submissions API ---")
    r_susp = client.get("/api/faculty/suspicious_submissions").json()
    list_susp = r_susp.get("suspicious_submissions", [])
    assert len(list_susp) > 0
    print("Flagged Count:", len(list_susp))
    print("PASSED: Faculty telemetry loaded suspicious submissions.")


def test_ai_practice_and_activity_logging():
    print("\n--- 5. Testing AI Practice Mode Challenge & Activity Telemetry ---")
    r_chal = client.post("/api/practice/challenge", json={"student_id": "STU2024001", "concept": "Arrays", "difficulty": "medium"}).json()
    assert r_chal.get("success") is True
    assert "problem_id" in r_chal
    print("Generated Challenge Problem ID:", r_chal.get("problem_id"))

    r_act = client.post("/api/student/activity", json={"student_id": "STU2024001", "action": "tab_switch", "details": "Window blur detected"}).json()
    assert r_act.get("success") is True
    print("PASSED: AI Practice challenge generator and tab switch activity logging verified.")


def test_pdf_lab_manual_upload_and_verification():
    print("\n--- 6. Testing PDF Lab Manual Upload & Faculty Verification Module ---")
    import io

    # Create dummy PDF bytes for testing upload
    pdf_content = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<< /Root 1 0 R >>\n%%EOF"
    file_tuple = ("test_manual.pdf", io.BytesIO(pdf_content), "application/pdf")

    # Upload PDF Manual
    res_upload = client.post("/api/faculty/manual/upload", files={"file": file_tuple}).json()
    print("Upload Response:", res_upload)
    assert res_upload.get("success") is True
    manual_id = res_upload.get("manual_id")
    assert manual_id is not None
    assert res_upload.get("total_detected") >= 3

    # Get Detected Programs for Review
    res_programs = client.get(f"/api/faculty/manual/{manual_id}/programs").json()
    assert res_programs.get("success") is True
    progs = res_programs.get("programs", [])
    assert len(progs) > 0
    p1 = progs[0]
    print("Detected Program 1:", p1.get("title"))

    # Edit Program Details as Faculty
    res_edit = client.put(f"/api/faculty/manual/program/{p1['id']}", json={
        "title": "Largest of Three (Verified)",
        "faculty_verified": True
    }).json()
    assert res_edit.get("success") is True

    # Approve & Publish to Student Bank
    res_approve = client.post(f"/api/faculty/manual/program/{p1['id']}/approve").json()
    assert res_approve.get("success") is True

    # Verify published problem exists in student problem bank
    res_bank = client.get("/api/problems").json()
    problem_titles = [p["title"] for p in res_bank.get("problems", [])]
    assert "Largest of Three (Verified)" in problem_titles
    print("PASSED: PDF Manual upload, exercise detection, faculty verification, and publication verified.")


if __name__ == "__main__":
    test_clean_compilation_no_groq()
    test_syntax_error_groq_instructions()
    test_anti_hardcoding_and_creativity()
    test_faculty_suspicious_review()
    test_ai_practice_and_activity_logging()
    test_pdf_lab_manual_upload_and_verification()
    print("\nALL SYSTEM INTEGRATION TESTS COMPLETED SUCCESSFULLY WITH ZERO ERRORS!")


