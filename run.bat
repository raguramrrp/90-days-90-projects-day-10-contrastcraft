@echo off
setlocal

echo =====================================================================
echo   ContrastCraft — Automated Web Accessibility Contrast Auditor
echo   Day 10: 90 Days - 90 Projects Challenge
echo =====================================================================
echo.

cd /d "%~dp0"

:: Activate virtual environment if present
if exist .\.venv\Scripts\activate.bat (
    call .\.venv\Scripts\activate.bat
)

set PYTHONPATH=%~dp0

echo Starting ContrastCraft server...
echo Local Web Application: http://127.0.0.1:8000
echo API Documentation:    http://127.0.0.1:8000/docs
echo.
echo Press CTRL+C in this terminal window to stop the server.
echo.

python app.py --open %*

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] ContrastCraft exited with error code %errorlevel%.
    pause
)
