@echo off
title AI Lab Assistant

echo Killing any process on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

cd /d "%~dp0backend"
echo Starting server...
start "AI Lab Assistant Server" cmd /k "python -m uvicorn app:app --port 8000"

echo Waiting for server to start...
timeout /t 3 /nobreak >nul
start "" "http://localhost:8000"
