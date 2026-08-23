"""
Deployment Verification Script — Tests static routes, API endpoints, and clean URLs.
"""
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_deployment_routes():
    print("\n--- 1. Testing Root Index Route (/) ---")
    res_root = client.get("/")
    print("Status:", res_root.status_code)
    assert res_root.status_code == 200

    print("\n--- 2. Testing API Health (/api/health) ---")
    res_health = client.get("/api/health")
    print("Status:", res_health.status_code, "Body:", res_health.json())
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    print("\n--- 3. Testing Clean URL HTML Fallbacks (/login, /student/lab, /faculty/dashboard) ---")
    for clean_path in ["/login", "/student/lab", "/student/dashboard", "/faculty/dashboard"]:
        res = client.get(clean_path)
        print(f"Path: {clean_path} -> Status: {res.status_code}")
        assert res.status_code == 200

    print("\n--- 4. Testing Explicit HTML Paths (/index.html, /login.html, /student/lab.html) ---")
    for html_path in ["/index.html", "/login.html", "/student/lab.html", "/student/dashboard.html", "/faculty/dashboard.html"]:
        res = client.get(html_path)
        print(f"Path: {html_path} -> Status: {res.status_code}")
        assert res.status_code == 200

    print("\n--- 5. Testing API Problems (/api/problems) ---")
    res_prob = client.get("/api/problems")
    print("Status:", res_prob.status_code, "Total Problems:", len(res_prob.json().get("problems", [])))
    assert res_prob.status_code == 200

    print("\nALL DEPLOYMENT ROUTE VERIFICATIONS PASSED WITH ZERO 404 ERRORS!")

if __name__ == "__main__":
    test_deployment_routes()
