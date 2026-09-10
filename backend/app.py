import os
import sys
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

# Ensure backend directory is in sys.path for root deployments
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db_and_seed
from routes.auth import router as auth_router
from routes.problems import router as problems_router
from routes.submissions import router as submissions_router
from routes.writeups import router as writeups_router
from routes.exams import router as exams_router
from routes.student import router as student_router
from routes.faculty import router as faculty_router

# Initialize database tables and seed data
init_db_and_seed()

app = FastAPI(title="SMART LAB: AI-Powered C Programming Laboratory Matrix", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router)
app.include_router(problems_router)
app.include_router(submissions_router)
app.include_router(writeups_router)
app.include_router(exams_router)
app.include_router(student_router)
app.include_router(faculty_router)


# ── Health Check ───────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "matrix": "active"}


# ── Multi-Environment Frontend Resolution ──────────────────────
candidate_dirs = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend")),
    os.path.abspath(os.path.join(os.getcwd(), "frontend")),
    "/var/task/frontend",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend")),
]

frontend_dir = None
for cd in candidate_dirs:
    if os.path.exists(cd):
        frontend_dir = cd
        break


def get_frontend_file(rel_path: str):
    if not frontend_dir:
        return None
    full_path = os.path.join(frontend_dir, rel_path)
    if os.path.exists(full_path):
        return full_path
    if not full_path.endswith(".html"):
        html_path = full_path + ".html"
        if os.path.exists(html_path):
            return html_path
    return None


# ── Explicit Frontend Page Endpoints ────────────────────────────

@app.get("/", response_class=FileResponse)
@app.get("/index.html", response_class=FileResponse)
def serve_root():
    f = get_frontend_file("index.html")
    if f and os.path.exists(f):
        return FileResponse(f)
    return HTMLResponse("<h1>SMART LAB Matrix Online</h1><p>Frontend assets initializing...</p>")


@app.get("/login", response_class=FileResponse)
@app.get("/login.html", response_class=FileResponse)
def serve_login():
    f = get_frontend_file("login.html")
    if f and os.path.exists(f):
        return FileResponse(f)
    raise HTTPException(status_code=404, detail="login.html not found")


@app.get("/student/{page}")
def serve_student_page(page: str):
    clean_page = page if page.endswith(".html") else f"{page}.html"
    f = get_frontend_file(os.path.join("student", clean_page))
    if f and os.path.exists(f):
        return FileResponse(f)
    raise HTTPException(status_code=404, detail=f"Student page '{page}' not found")


@app.get("/faculty/{page}")
def serve_faculty_page(page: str):
    clean_page = page if page.endswith(".html") else f"{page}.html"
    f = get_frontend_file(os.path.join("faculty", clean_page))
    if f and os.path.exists(f):
        return FileResponse(f)
    raise HTTPException(status_code=404, detail=f"Faculty page '{page}' not found")


# ── Mount Static Assets ─────────────────────────────────────────

if frontend_dir:
    css_dir = os.path.join(frontend_dir, "css")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
        app.mount("/frontend/css", StaticFiles(directory=css_dir), name="frontend_css")

    js_dir = os.path.join(frontend_dir, "js")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
        app.mount("/frontend/js", StaticFiles(directory=js_dir), name="frontend_js")

    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend_dir")
