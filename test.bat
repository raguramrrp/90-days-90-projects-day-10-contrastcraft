@echo off
setlocal

echo =====================================================================
echo   Running ContrastCraft Automated Test Suite (pytest)
echo   Mathematical Accuracy, WCAG Criteria, Cascade, Diff and Safety Tests
echo =====================================================================
echo.

cd /d "%~dp0"

if exist .\.venv\Scripts\activate.bat (
    call .\.venv\Scripts\activate.bat
)

set PYTHONPATH=%~dp0

if exist .\.venv\Scripts\pytest.exe (
    .\.venv\Scripts\pytest.exe backend\tests -v
) else if exist .\.venv\Scripts\python.exe (
    .\.venv\Scripts\python.exe -m pytest backend\tests -v
) else (
    python -m pytest backend\tests -v
)

set TEST_EXIT_CODE=%errorlevel%

echo.
if %TEST_EXIT_CODE% equ 0 (
    echo [PASS] All automated tests passed successfully!
) else (
    echo [FAIL] Automated tests failed with exit code %TEST_EXIT_CODE%.
)

exit /b %TEST_EXIT_CODE%
