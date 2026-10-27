# Quickstart Guide — ContrastCraft

Get ContrastCraft up and running on Windows in under 60 seconds.

---

## ⚡ Method 1: Automated Windows Batch Scripts (Recommended)

### 1. Initial Setup
Double-click `setup.bat` or run in PowerShell:
```powershell
.\setup.bat
```
This verifies Python, initializes the project virtual environment (`.venv`), installs required dependencies, and sets up the local SQLite database.

### 2. Launch Application
Double-click `run.bat` or run:
```powershell
.\run.bat
```
Your browser will automatically open to:
```
http://127.0.0.1:8000
```

### 3. Run Automated Tests
Double-click `test.bat` or run:
```powershell
.\test.bat
```

---

## 🛠️ Method 2: Manual PowerShell Setup

If you prefer executing commands directly in PowerShell:

```powershell
# 1. Navigate to project root
cd "d:\90 days\90-days-90-projects-day-10-contrastcraft"

# 2. Create virtual environment
py -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Run automated test suite
python -m pytest backend/tests -v

# 6. Start the server
python app.py --open
```

---

## 🚀 First 60-Second Walkthrough

1. **Load Demo:** On the Workspace screen, click **"📁 Load Sample Showcase"**.
2. **Execute Scan:** Click **"⚡ Run Contrast Audit"** (or press `Alt + A`).
3. **Inspect Violations:** In the Audit Findings table, review failing elements (e.g., subtitle `#94A3B8` on `#FFFFFF` with 2.60:1 contrast). Click **"Inspect"** to view element hierarchy and luminance.
4. **Fix Studio:** Click **"Fix in Studio"** to see automated hue-preserving lightness recommendations. Select an alternative and preview the before/after difference.
5. **Preview & Patch:** Inspect the unified CSS diff and isolated sandboxed preview. Click **"✨ Apply Patch"** with explicit confirmation.
6. **Export Report:** Go to **Sessions & Reports** and click **"📑 Download Standalone HTML Report"**.
