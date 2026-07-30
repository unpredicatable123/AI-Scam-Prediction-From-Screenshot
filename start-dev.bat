@echo off
REM Starts both the AI service (FastAPI, port 8000) and the frontend (SvelteKit, port 5173).
REM Just double-click this file. Each service opens in its own window with a clear title —
REM close a window (or Ctrl+C in it) to stop that service.

echo Freeing ports 8000 and 5173 if anything is already listening on them...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

set MODEL_DIR=D:\ai-scam-detection-data\model_v2

echo Starting AI service (FastAPI) on port 8000...
start "AI Service (FastAPI :8000)" cmd /k "cd /d %~dp0apps\ai-service&& set "MODEL_DIR=%MODEL_DIR%"&& python -m uvicorn app.main:app --port 8000"

echo Starting frontend (SvelteKit) on port 5173...
start "Frontend (SvelteKit :5173)" cmd /k "cd /d %~dp0 && npm run dev"

echo.
echo Both services are starting in their own windows.
echo   AI service:  http://localhost:8000/v1/health
echo   Frontend:    http://localhost:5173
echo.
echo Give it ~10-15 seconds, then open http://localhost:5173/analyze in your browser.
/c