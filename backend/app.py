import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

app = FastAPI(title="AI-Powered C Programming Laboratory Matrix", version="2.0")

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


@app.get("/api/health")
def health():
    return {"status": "ok", "matrix": "active"}


# Serve static frontend at root with clean URL routing fallbacks
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.exists(frontend_path):
    @app.middleware("http")
    async def clean_url_middleware(request: Request, call_next):
        path = request.url.path
        # If accessing non-API path without extension, check if .html file exists
        if not path.startswith("/api") and "." not in os.path.basename(path) and path != "/":
            relative_path = path.lstrip("/") + ".html"
            html_file = os.path.join(frontend_path, relative_path)
            if os.path.exists(html_file):
                return FileResponse(html_file)
        return await call_next(request)

    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
