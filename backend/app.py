import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

# Mount Routers
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


# Serve static frontend at root
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

