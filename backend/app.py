import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes.compiler import router as compiler_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compiler_router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve frontend
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))
