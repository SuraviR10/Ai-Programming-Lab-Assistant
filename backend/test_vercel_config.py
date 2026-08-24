import json
import os
import re
import sys

def test_vercel_routes():
    print("--- 1. Testing vercel.json Syntax & Routes ---")
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vercel_path = os.path.join(root_dir, "vercel.json")
    
    with open(vercel_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    assert config["version"] == 2
    assert len(config["builds"]) > 0
    assert len(config["routes"]) > 0
    
    # Check that all dest strings start with leading slash
    for r in config["routes"]:
        dest = r["dest"]
        assert dest.startswith("/"), f"Route dest '{dest}' must start with '/'"
        
    print("vercel.json JSON syntax and destination leading slashes verified.")
    
    # Test sample URLs through route regex matching
    sample_urls = [
        ("/", "/frontend/index.html"),
        ("/login", "/frontend/login.html"),
        ("/student/dashboard", "/frontend/student/dashboard.html"),
        ("/student/lab", "/frontend/student/lab.html"),
        ("/student/problems", "/frontend/student/problems.html"),
        ("/student/progress", "/frontend/student/progress.html"),
        ("/student/achievements", "/frontend/student/achievements.html"),
        ("/faculty/dashboard", "/frontend/faculty/dashboard.html"),
        ("/faculty/manual", "/frontend/faculty/manual.html"),
        ("/student/lab.html", "/frontend/student/lab.html"),
        ("/css/base.css", "/frontend/css/base.css"),
        ("/js/api.js", "/frontend/js/api.js"),
        ("/api/health", "/api/index.py"),
        ("/api/problems", "/api/index.py"),
    ]
    
    for url, expected_dest in sample_urls:
        matched = False
        for r in config["routes"]:
            pattern = "^" + r["src"] + "$"
            m = re.match(pattern, url)
            if m:
                # Resolve captures
                actual_dest = r["dest"]
                for i, group in enumerate(m.groups(), start=1):
                    actual_dest = actual_dest.replace(f"${i}", group)
                assert actual_dest == expected_dest, f"URL {url} mapped to {actual_dest}, expected {expected_dest}"
                matched = True
                break
        assert matched, f"URL {url} did not match any route in vercel.json"
        
        # Verify file exists on disk (if not /api/index.py)
        rel_path = expected_dest.lstrip("/")
        disk_path = os.path.join(root_dir, rel_path)
        assert os.path.exists(disk_path), f"File referenced by route does not exist: {disk_path}"
        print(f"URL: {url:<25} -> {expected_dest:<35} [EXISTS on disk]")
        
    print("\n--- 2. Testing API Serverless Handler (api/index.py) ---")
    sys.path.insert(0, os.path.join(root_dir, "api"))
    import index
    from fastapi.testclient import TestClient
    client = TestClient(index.app)
    
    res = client.get("/api/health")
    assert res.status_code == 200
    print("Health check response:", res.json())
    
    res_prob = client.get("/api/problems")
    assert res_prob.status_code == 200
    print("Problems count:", len(res_prob.json().get("problems", [])))
    
    print("\nALL VERCEL DEPLOYMENT CONFIGURATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_vercel_routes()
