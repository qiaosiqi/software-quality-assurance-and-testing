@echo off
REM First-time setup: create venv, install deps, install Playwright Chromium.
REM Daily launch uses start.bat. Pure ASCII to keep cmd cp936 happy.

cd /d "%~dp0"

set "VENV_PY=%~dp0.venv\Scripts\python.exe"

if not exist .venv (
    echo [setup] creating venv at .venv ...
    REM prefer py launcher; falls back to python only if py is unavailable
    where py >nul 2>nul
    if errorlevel 1 (
        python -m venv .venv
    ) else (
        py -3 -m venv .venv
    )
) else (
    echo [setup] .venv already exists, skipping creation
)

if not exist "%VENV_PY%" (
    echo [setup] ERROR: venv creation failed, missing %VENV_PY%
    pause
    exit /b 1
)

echo [setup] python: %VENV_PY%
echo [setup] upgrading pip ...
"%VENV_PY%" -m pip install --upgrade pip

echo [setup] installing requirements ...
"%VENV_PY%" -m pip install -r requirements.txt

echo [setup] installing Playwright Chromium (about 100MB on first run) ...
"%VENV_PY%" -m playwright install chromium

echo.
echo [setup] done. run start.bat to launch the GUI.
pause
