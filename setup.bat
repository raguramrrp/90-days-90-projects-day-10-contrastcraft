@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo   ContrastCraft - Setup & Environment Configuration
echo   Automated Web Accessibility Contrast Auditor (WCAG 2.1 / 2.2)
echo =====================================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH.
    echo Please install Python 3.10+ from https://www.python.org/ and ensure
    echo "Add Python to PATH" is checked during setup.
    pause
    exit /b 1
)

echo [OK] Python detected:
python --version
echo.

:: 2. Set up virtual environment
if not exist .venv (
    echo [INFO] Creating Python virtual environment in .venv...
    py -m venv .venv
    if %errorlevel% neq 0 (
        python -m venv .venv
    )
) else (
    echo [OK] Virtual environment .venv already exists.
)

:: 3. Activate virtual environment
if exist .\.venv\Scripts\activate.bat (
    call .\.venv\Scripts\activate.bat
) else (
    echo [ERROR] Could not find virtual environment activation script.
    pause
    exit /b 1
)

:: 4. Install dependencies
echo.
echo [INFO] Installing required dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Online dependency installation encountered an issue.
    echo If packages are already cached locally, ContrastCraft will continue using them.
)

:: 5. Initialize database
echo.
echo [INFO] Verifying local SQLite database initialization...
set PYTHONPATH=%~dp0
python -c "from backend.app.database.session_store import SessionStore; store = SessionStore(); print('[OK] Database initialized at:', store.db_path)"

echo.
echo =====================================================================
echo   Setup Completed Successfully!
echo   To launch ContrastCraft, double-click run.bat or execute:
echo     run.bat
echo =====================================================================
echo.
pause
