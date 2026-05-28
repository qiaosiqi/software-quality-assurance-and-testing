@echo off
REM Daily launcher. Uses absolute path to .venv python.exe to bypass
REM PATH / conda activate quirks. Pure ASCII to keep cmd cp936 happy.

cd /d "%~dp0"

set "VENV_PY=%~dp0.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [start] venv python not found: %VENV_PY%
    echo [start] run setup.bat first.
    pause
    exit /b 1
)

REM open browser after 3s so uvicorn has time to bind
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8000"

echo [start] python: %VENV_PY%
echo [start] launching uvicorn on http://localhost:8000  (Ctrl+C to stop)
"%VENV_PY%" -m uvicorn server.main:app --port 8000
