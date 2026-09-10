"""
Comprehensive End-to-End Test Suite for SMART LAB:
An Intelligent Programming Assessment and Error Explanation System

Tests all 11 Core Verification Workflows:
1. Valid C program compilation & execution (GCC direct, zero Groq overhead)
2. Compilation error handling & Groq AI educational explanation (no full solution)
3. Infinite loop / Runtime timeout protection
4. Wrong logic / Test case failure diagnosis
5. Anti-hardcoding detection (printf-only output without input reading flagged)
6. Different valid solutions accepted (e.g. ternary, bitwise, varied algorithms)
7. PDF Lab manual processing & experiment validation
8. AI Practice Challenge generation
9. Student progress & dynamic concept mastery calculation
10. Weekly Write-Up submission & GCC test-case evaluation
11. Practical Examination submission with AI disabled enforcement
"""

import os
import sys
import json
import unittest

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app import app
from database import init_db_and_seed, SessionLocal, Problem, TestCase, User, Submission, WriteUp, Exam
from services.gcc_service import compile_and_run
from services.groq_service import analyze_compiler_error
from services.anti_hardcoding_service import analyze_c_code_structure
from services.pdf_extraction_service import fallback_heuristic_extraction, validate_extracted_experiment


class SmartLabIntegrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n========================================================")
        print("STARTING SMART LAB INTEGRATION TEST SUITE")
        print("========================================================")
        init_db_and_seed()
        cls.client = TestClient(app)

    # ── TEST 1: Correct C Program ────────────────────────────────
    def test_01_correct_c_program(self):
        print("\n[TEST 1] Testing Valid C Program Execution (GCC Only, Zero Groq Calls)...")
        code = """#include <stdio.h>
int main() {
    int x = 10, y = 20;
    printf("Result: %d\\n", x + y);
    return 0;
}"""
        res = self.client.post("/api/compiler/run", json={"code": code, "mode": "practice"}).json()
        self.assertTrue(res.get("success"), f"Execution failed: {res}")
        self.assertEqual(res.get("output"), "Result: 30")
        self.assertNotIn("ai_feedback", res, "Groq should NOT be called for clean execution!")
        print("  [OK] GCC compiled and executed successfully with exact stdout.")
        print("  [OK] Groq API was bypassed cleanly.")

    # ── TEST 2: Compilation Error with Groq Guidance ─────────────
    def test_02_compilation_error_groq_guidance(self):
        print("\n[TEST 2] Testing GCC Error Capture & Groq Educational Guidance...")
        broken_code = """#include <stdio.h>
int main() {
    printf("Hello World")
    return 0;
}"""
        res = self.client.post("/api/compiler/run", json={"code": broken_code, "mode": "practice"}).json()
        self.assertFalse(res.get("success"))
        self.assertIn("compiler_error", res)
        self.assertIn("ai_feedback", res)

        feedback = res["ai_feedback"]
        self.assertFalse(feedback.get("ai_disabled", False))
        self.assertIn("explanation", feedback)
        self.assertIn("why_it_happened", feedback)
        self.assertIn("how_to_fix", feedback)
        # Ensure no complete copy-paste solution is given in the explanation
        self.assertNotIn("int main() {\n    printf(\"Hello World\");", feedback.get("explanation", ""))
        print(f"  [OK] GCC detected syntax error at line: {res.get('line')}")
        print(f"  [OK] Groq returned structured educational explanation: {feedback.get('explanation')[:60]}...")

    # ── TEST 3: Runtime Timeout ──────────────────────────────────
    def test_03_runtime_timeout(self):
        print("\n[TEST 3] Testing Infinite Loop & Runtime Timeout Protection...")
        infinite_loop_code = """#include <stdio.h>
int main() {
    while(1) {
        // infinite loop
    }
    return 0;
}"""
        res = compile_and_run(infinite_loop_code, timeout_sec=2)
        self.assertFalse(res.get("success"))
        self.assertIn("timed out", res.get("compiler_error", "").lower())
        print("  [OK] Subprocess safely terminated execution after timeout limit.")

    # ── TEST 4: Wrong Logic Test Failure ─────────────────────────
    def test_04_wrong_logic_test_failure(self):
        print("\n[TEST 4] Testing Wrong Logic / Test Case Output Mismatch...")
        # Problem 2: Sum of Two Numbers (expected "Sum = 15" for input "5 10")
        wrong_logic_code = """#include <stdio.h>
int main() {
    int a, b;
    if (scanf("%d %d", &a, &b) == 2) {
        printf("Sum = %d\\n", a * b); // Multiplies instead of adds!
    }
    return 0;
}"""
        res = self.client.post("/api/compiler/run", json={"problem_id": 2, "code": wrong_logic_code, "mode": "practice"}).json()
        self.assertTrue(res.get("success"))
        self.assertFalse(res.get("test_passed"))
        self.assertIn("ai_feedback", res)
        print("  [OK] Test mismatch identified (Output: Sum = 50 vs Expected: Sum = 15).")
        print("  [OK] Groq provided diagnostic feedback explaining the arithmetic discrepancy.")

    # ── TEST 5: Hardcoded / Printf-Only Solution Detection ────────
    def test_05_hardcoded_output_detection(self):
        print("\n[TEST 5] Testing Anti-Hardcoding Static & Dynamic Detection...")
        # Problem 2 requires input (5 10) -> student simply prints "Sum = 15"
        fake_code = """#include <stdio.h>
int main() {
    printf("Sum = 15\\n");
    return 0;
}"""
        res = self.client.post("/api/submissions", json={"student_id": "STU2024001", "problem_id": 2, "code": fake_code}).json()
        self.assertTrue(res.get("is_hardcoded"))
        self.assertEqual(res.get("status"), "POTENTIALLY_HARDCODED")
        self.assertGreaterEqual(res.get("hardcoding_risk_score", 0), 0.70)
        print(f"  [OK] Solution flagged as POTENTIALLY_HARDCODED (Risk Score: {res.get('hardcoding_risk_score')}).")

    # ── TEST 6: Different Valid Solutions Accepted ───────────────
    def test_06_different_valid_solutions_accepted(self):
        print("\n[TEST 6] Testing Acceptance of Alternative Valid Algorithms...")
        # Problem 2: Sum of two numbers using pointer arithmetic / while loop
        alt_valid_code = """#include <stdio.h>
int main() {
    int a, b, *p = &a, *q = &b;
    if (scanf("%d %d", p, q) == 2) {
        int sum = 0;
        sum = *p;
        sum += *q;
        printf("Sum = %d\\n", sum);
    }
    return 0;
}"""
        res = self.client.post("/api/submissions", json={"student_id": "STU2024001", "problem_id": 2, "code": alt_valid_code}).json()
        self.assertFalse(res.get("is_hardcoded"))
        self.assertEqual(res.get("status"), "VALID_SOLUTION")
        self.assertEqual(res.get("score"), 10.0)
        self.assertEqual(res.get("passed_test_cases"), res.get("total_test_cases"))
        print("  [OK] Alternative valid algorithm accepted and awarded full 10.0 marks.")

    # ── TEST 7: PDF Manual Program Extraction ────────────────────
    def test_07_pdf_manual_extraction(self):
        print("\n[TEST 7] Testing PDF Manual Program Extraction & Validation...")
        sample_manual_text = """
        DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING
        C PROGRAMMING LABORATORY MANUAL

        Experiment 1: Roots of Quadratic Equation
        Aim: To write a C program to find the roots of a quadratic equation.
        Problem Statement: Write a C program to compute the real and imaginary roots of ax^2 + bx + c = 0.
        Input Format: Three space-separated float numbers a, b, c.
        Output Format: Roots: r1 and r2
        Sample Input: 1 -5 6
        Sample Output: Roots: 3.00 and 2.00
        Reference Code:
        #include <stdio.h>
        #include <math.h>
        int main() {
            float a, b, c;
            if (scanf("%f %f %f", &a, &b, &c) == 3) {
                float d = b*b - 4*a*c;
                float r1 = (-b + sqrt(d))/(2*a);
                float r2 = (-b - sqrt(d))/(2*a);
                printf("Roots: %.2f and %.2f\\n", r1, r2);
            }
            return 0;
        }

        Experiment 2: Linear Search in Array
        Aim: To search for a key element in an integer array.
        Problem Statement: Write a C program to read N integers and search for a key element.
        Sample Input: 5\\n10 20 30 40 50\\n30
        Sample Output: Found at index 2
        """
        programs = fallback_heuristic_extraction(sample_manual_text)
        self.assertGreaterEqual(len(programs), 2)
        p1 = programs[0]
        self.assertIn("quadratic", p1["title"].lower())
        self.assertTrue(p1["validation_report"]["valid_syntax"])
        self.assertTrue(p1["validation_report"]["has_main"])
        print(f"  [OK] Extracted {len(programs)} distinct laboratory experiments from manual text.")
        print(f"  [OK] Validated Experiment 1 ('{p1['title']}'): Syntax Valid = {p1['validation_report']['valid_syntax']}.")

    # ── TEST 8: AI Practice Challenge Generation ─────────────────
    def test_08_practice_challenge_generation(self):
        print("\n[TEST 8] Testing Adaptive AI Practice Challenge Generation...")
        res = self.client.post("/api/practice/challenge", json={"student_id": "STU2024001", "concept": "Arrays", "difficulty": "medium"}).json()
        self.assertTrue(res.get("success"))
        self.assertIn("problem_id", res)
        prob = res.get("problem", {})
        self.assertIn("starter_code", prob)
        self.assertIn("Arrays", str(prob.get("concepts", [])))
        clean_title = prob.get('title', '').encode('ascii', 'ignore').decode('ascii')
        print(f"  [OK] Generated practice challenge: '{clean_title}' (ID: {res.get('problem_id')}).")

    # ── TEST 9: Student Progress Calculation ─────────────────────
    def test_09_student_progress_metrics(self):
        print("\n[TEST 9] Testing Student Progress & Dynamic Concept Breakdown...")
        res = self.client.get("/api/student/progress?student_id=STU2024001").json()
        self.assertTrue(res.get("success"))
        profile = res.get("profile", {})
        self.assertIn("user_id", profile)
        self.assertIn("current_xp", profile)
        self.assertIn("level", profile)

        concepts = res.get("concepts_breakdown", [])
        self.assertGreater(len(concepts), 0)
        print(f"  [OK] Student Profile loaded: Level {profile.get('level')}, XP: {profile.get('current_xp')}.")
        print(f"  [OK] Calculated {len(concepts)} dynamic concept mastery tracks.")

    # ── TEST 10: Write-Up Mode ───────────────────────────────────
    def test_10_writeup_workflow(self):
        print("\n[TEST 10] Testing Weekly Laboratory Write-Up Session & Evaluation...")
        # Start writeup session
        start_res = self.client.post("/api/writeups/1/start", json={"student_id": "STU2024001"}).json()
        self.assertTrue(start_res.get("success"))
        self.assertIn("writeup", start_res)

        # Submit writeup with valid solutions for problem 3 (Largest of 3) and problem 5 (Factorial)
        code_map = {
            "3": '#include <stdio.h>\nint main() { int a, b, c; if (scanf("%d %d %d", &a, &b, &c) == 3) { int max = (a>b)?((a>c)?a:c):((b>c)?b:c); printf("Largest = %d\\n", max); } return 0; }',
            "5": '#include <stdio.h>\nint main() { int n; if (scanf("%d", &n) == 1) { long long fact = 1; for (int i = 1; i <= n; i++) fact *= i; printf("Factorial = %lld\\n", fact); } return 0; }'
        }
        sub_res = self.client.post("/api/writeups/1/submit", json={"student_id": "STU2024001", "code_map": code_map}).json()
        self.assertTrue(sub_res.get("success"))
        self.assertEqual(sub_res.get("status"), "submitted")
        self.assertGreater(sub_res.get("score"), 0.0)
        print(f"  [OK] Write-up submitted and evaluated with real marks: {sub_res.get('score')} / 10.0.")

    # ── TEST 11: Examination Mode with AI Disabled ───────────────
    def test_11_exam_workflow(self):
        print("\n[TEST 11] Testing Practical Examination Mode & Strict AI Disabled Policy...")
        # Start exam session
        start_res = self.client.post("/api/exams/1/start", json={"student_id": "STU2024001"}).json()
        self.assertTrue(start_res.get("success"))
        self.assertEqual(start_res.get("exam", {}).get("ai_policy"), "none")

        # Verify AI error explanation is blocked during exam mode
        broken_code = "int main() { return }"
        ai_res = analyze_compiler_error(broken_code, "error: expected ';'", 1, mode="exam")
        self.assertTrue(ai_res.get("ai_disabled"))
        self.assertIn("disabled", ai_res.get("explanation", "").lower())
        print("  [OK] Backend strictly verified AI Guidance is disabled during examinations.")

        # Submit exam code for problem 2 (Sum of 2) and problem 4 (Even/Odd)
        code_map = {
            "2": '#include <stdio.h>\nint main() { int a, b; if (scanf("%d %d", &a, &b) == 2) printf("Sum = %d\\n", a + b); return 0; }',
            "4": '#include <stdio.h>\nint main() { int n; if (scanf("%d", &n) == 1) { if (n % 2 == 0) printf("Even\\n"); else printf("Odd\\n"); } return 0; }'
        }
        sub_res = self.client.post("/api/exams/1/submit", json={"student_id": "STU2024001", "code_map": code_map}).json()
        self.assertTrue(sub_res.get("success"))
        self.assertEqual(sub_res.get("status"), "submitted")
        self.assertEqual(sub_res.get("score"), 10.0)
        print(f"  [OK] Practical Exam evaluated with GCC MinGW. Score: {sub_res.get('score')} / 10.0.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
