import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_manual_problem_creation_and_listing():
    print("Testing manual problem creation...")
    payload = {
        "title": "Calculate Factorial",
        "topic": "Recursion & Functions",
        "difficulty": "easy",
        "description": "Write a C program to calculate the factorial of a given non-negative integer N.",
        "input_format": "A single non-negative integer N",
        "output_format": "Factorial value as integer",
        "sample_input": "5",
        "sample_output": "120",
        "starter_code": "#include <stdio.h>\n\nint main() {\n    int n;\n    scanf(\"%d\", &n);\n    long long fact = 1;\n    for(int i = 1; i <= n; i++) fact *= i;\n    printf(\"%lld\", fact);\n    return 0;\n}",
        "expected_output": "120",
        "xp_reward": 100,
        "test_cases": [
            {"input_data": "5", "expected_output": "120", "is_hidden": False},
            {"input_data": "0", "expected_output": "1", "is_hidden": False},
            {"input_data": "6", "expected_output": "720", "is_hidden": True}
        ]
    }

    res = client.post("/api/faculty/problems/create", json=payload)
    print("Create status:", res.status_code, res.json())
    assert res.status_code == 200
    assert res.json()["success"] is True
    prob_id = res.json()["problem_id"]

    print("Testing problem listing...")
    res_list = client.get("/api/faculty/problems")
    assert res_list.status_code == 200
    problems = res_list.json()["problems"]
    found = any(p["id"] == prob_id for p in problems)
    assert found is True
    print(f"Problem #{prob_id} successfully found in problem bank!")

    print("Testing tab switch telemetry logging...")
    activity_payload = {
        "student_id": "STU2024001",
        "action": "tab_switch",
        "details": "Student STU2024001 switched away from Lab window (Violation #1)"
    }
    act_res = client.post("/api/student/activity", json=activity_payload)
    print("Activity log status:", act_res.status_code, act_res.json())
    assert act_res.status_code == 200
    assert act_res.json()["success"] is True

    print("Testing dashboard telemetry update...")
    dash_res = client.get("/api/faculty/dashboard")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "metrics" in dash_data
    assert dash_data["metrics"]["tab_switches_total"] >= 1
    print("Total tab switches recorded:", dash_data["metrics"]["tab_switches_total"])

    print("Testing problem deletion...")
    del_res = client.delete(f"/api/faculty/problems/{prob_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True
    print("Problem deleted successfully!")

    print("\n ALL BACKEND TESTS PASSED SUCCESSFULLY! ")

if __name__ == "__main__":
    test_manual_problem_creation_and_listing()
