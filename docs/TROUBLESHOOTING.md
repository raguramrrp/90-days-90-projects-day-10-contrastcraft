# Troubleshooting Guide — ContrastCraft

Common issues, diagnostics, and quick resolutions for Windows and cross-platform environments.

---

## 1. Port 8000 Already in Use

### Symptom:
`ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): only one usage of each socket address is normally permitted`

### Resolution:
Set an alternative port using the `PORT` environment variable:
```powershell
$env:PORT = "8080"
python app.py
```
Or specify the port argument directly:
```powershell
python -m uvicorn backend.app.main:app --port 8080
```

---

## 2. PowerShell Execution Policy Restricts Virtual Environment Activation

### Symptom:
`.\.venv\Scripts\Activate.ps1 : File cannot be loaded because running scripts is disabled on this system.`

### Resolution:
Run `setup.bat` or `run.bat` (which use CMD and bypass PowerShell execution policies), or run PowerShell with `Bypass`:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 3. "ModuleNotFoundError: No module named 'backend'"

### Symptom:
Running `pytest` directly produces module import errors.

### Resolution:
Ensure `PYTHONPATH` points to the project root:
```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest backend/tests -v
```
Alternatively, simply run `test.bat`, which automatically sets `PYTHONPATH` to the script's directory.

---

## 4. Why Does My Finding Say "Needs Verification"?

### Explanation:
ContrastCraft practices **honest accessibility reporting**. If an element uses:
- A CSS gradient (`linear-gradient(...)`)
- A background image (`url(...)`)
- An unresolved CSS custom property with missing fallback

Static analysis cannot know with certainty which pixel of an image or gradient is directly behind a given word. ContrastCraft labels these as `needs_browser_verification` so developers can inspect the rendered page in browser DevTools rather than trusting a fabricated score.
