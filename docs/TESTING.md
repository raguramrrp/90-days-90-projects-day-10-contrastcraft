# Testing Strategy & Verification Report — ContrastCraft

## 1. Test Architecture & Coverage Summary

ContrastCraft uses `pytest` with a dedicated suite of 34 unit, integration, and safety tests covering all core modules.

| Test File | Focus Area | Status | Count |
| :--- | :--- | :---: | :---: |
| `test_contrast.py` | WCAG relative luminance, channel linearization, 21:1 extremes, 1:1 equal colors, 4.5:1 boundary | **PASS** | 5 |
| `test_colors.py` | 3/4/6/8-digit Hex, RGB/RGBA comma and slash syntax, HSL/HSLA, named colors, CSS variables, alpha compositing, dynamic gradients | **PASS** | 7 |
| `test_classifier.py` | Normal text AA & AAA, large text threshold logic (18pt / 14pt bold), non-text UI component boundaries (3.0:1) | **PASS** | 4 |
| `test_parser.py` | HTML DOM tree building, semantic role detection, specificity tuples `(inline, ID, class, tag)`, CSS cascade inheritance | **PASS** | 4 |
| `test_recommender.py` | Hue-preserving lightness search, mathematical ratio verification of suggestions, preset palette availability | **PASS** | 3 |
| `test_patcher.py` | Surgical CSS declaration replacement, unified diff generation, explicit approval safety gate, `.bak` backup creation | **PASS** | 2 |
| `test_reporter.py` | JSON export schema, HTML report generation with safe HTML escaping against XSS, corrected CSS export | **PASS** | 3 |
| `test_session_store.py` | SQLite session CRUD operations, session comparison with score delta and failure reduction calculation | **PASS** | 1 |
| `test_api.py` | FastAPI endpoint integration (health, presets, audit, recommend, patch, session lifecycle) | **PASS** | 5 |
| **Total** | | **PASS** | **34 / 34** |

---

## 2. Executing Automated Tests

### Windows Batch Script
```cmd
test.bat
```

### Manual PowerShell Execution
```powershell
$env:PYTHONPATH = "d:\90 days\90-days-90-projects-day-10-contrastcraft"
.\.venv\Scripts\python.exe -m pytest backend/tests -v
```

---

## 3. Key Test Cases Detailed

### A. Relative Luminance & Contrast Extremes
- **Test:** Black `#000000` on White `#FFFFFF` and White on Black.
- **Verification:** Relative luminance computes to $0.0$ and $1.0$. Contrast ratio computes to exactly $21.0:1$.
- **Test:** Equal colors `#808080` on `#808080`.
- **Verification:** Contrast ratio computes to exactly $1.0:1$.

### B. Canonical 4.5:1 Boundary Testing
- **Test:** `#767676` on `#FFFFFF` vs `#777777` on `#FFFFFF`.
- **Verification:** `#767676` produces $4.54:1$ (passes AA normal text); `#777777` produces $4.47:1$ (fails AA normal text).

### C. Patch Safety Gate
- **Test:** Attempting to write a patched file without `explicit_approval=True`.
- **Verification:** Function rejects disk write with error message; source file remains completely untouched.
- **Test:** Applying patch with `explicit_approval=True`.
- **Verification:** File is updated with targeted change; `.bak` backup file is created with original content.

### D. XSS Sanitization in HTML Reports
- **Test:** Injecting malicious `<script>alert(1)</script>` into selectors and element text.
- **Verification:** Output HTML encodes entities as `&lt;script&gt;alert(1)&lt;/script&gt;`, neutralising execution risks.
