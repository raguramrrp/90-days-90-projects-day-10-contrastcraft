# User Guide — ContrastCraft

A comprehensive walkthrough for auditing web pages, evaluating contrast ratios, testing color fixes, and exporting reports.

---

## 1. Getting Started

1. Start ContrastCraft by double-clicking `run.bat` or executing `python app.py` in your terminal.
2. Open your browser to `http://127.0.0.1:8000`.
3. Choose your preferred visual theme (Light or Dark) using the theme toggle in the upper right.

---

## 2. Choosing an Input Method

On the **Workspace & Input** screen, select from three input options:

### A. Paste HTML & CSS
- Paste your HTML markup in the left editor and your CSS stylesheet declarations in the right editor.
- Useful for quick snippet verification, design system tokens, or inspecting specific components.
- Click **"⚡ Run Contrast Audit"** (or press `Alt + A`).

### B. Upload HTML/CSS Files
- Drag and drop your `.html` and `.css` files into the designated dropzone.
- Files are parsed directly into memory without uploading to any remote server.

### C. Analyze Local Project Folder
- Specify the absolute or relative path to a local project directory (e.g., `D:\my-website`).
- ContrastCraft scans HTML files and resolves linked stylesheets while automatically skipping build directories (`node_modules`, `.git`, `dist`, `build`, `.venv`).

---

## 3. Reviewing Audit Findings

Once the audit completes, you are automatically transitioned to **Audit Findings**:
1. **Overview Statistics:** Check the Compliance Score gauge, total analyzed elements, Level AA passes/failures, Level AAA passes, and items needing verification.
2. **Search:** Filter findings instantly by selector name, sample text, or color hex code using the search bar (`Alt + S`).
3. **Filter Pills:** Filter by `AA Failures`, `AA Passes`, `AAA Failures`, `UI Boundary Failures`, or `Needs Verification`.
4. **Inspector Drawer:** Click **"Inspect"** on any finding row to view detailed element hierarchy, line numbers, calculated relative luminance, and exact WCAG criteria explanations.

---

## 4. Remediation in Fix Studio

To fix a failing contrast ratio:
1. Click **"Fix in Studio"** from any failing row or from the Inspector drawer.
2. **Review Verified Recommendations:** The Fix Studio displays candidate colors computed by the hue-preserving recommendation engine:
   - *Minimal Shift:* Darkens or lightens the original color just enough to pass the 4.5:1 threshold while preserving the original hue.
   - *Enhanced AAA Target:* Recommends an enhanced shade meeting the strict 7.0:1 standard.
   - *High-Contrast Anchor:* Provides maximum contrast boundaries (pure black or pure white).
3. **Select a Candidate:** Click any suggestion card. The **Unified CSS Diff** immediately updates to show the proposed rule change.
4. **Live Sandboxed Preview:**
   - Use the **Proposed Fix** vs **Original** toggle to compare visual legibility.
   - Click the responsive viewport buttons (`Mobile 375px`, `Tablet 768px`, `Full`) to evaluate responsive readability.
   - The target element is automatically highlighted with a pulsing blue indicator so you can spot it immediately.
5. **Apply Patch:**
   - To save the patch file, click **"💾 Export .diff"**.
   - To apply the patch to your working copy, click **"✨ Apply Patch"** and confirm in the safety dialog. ContrastCraft will update the CSS and immediately re-audit the result to confirm compliance.

---

## 5. Design Token Inventory

Navigate to **Design Tokens**:
- View all declared CSS variables (`--primary`, `--text-muted`, etc.) along with their resolved color swatches.
- View usage frequency and count of associated contrast violations.
- Review proposed token-level replacements to resolve multiple violations across your design system simultaneously.

---

## 6. Exporting Reports & Session Persistence

Navigate to **Sessions & Reports**:
- **Save Current Audit Session:** Save your audit snapshot to local SQLite for future reference.
- **Compare Sessions:** View score improvements and failure reductions between a baseline audit and a post-patch audit.
- **Download HTML Report:** Generates a self-contained, printable, responsive HTML audit report with executive metrics and detailed tables.
- **Download JSON Data:** Exports raw machine-readable JSON for integration into CI/CD workflows or archival.
- **Download Corrected CSS:** Downloads an accessible stylesheet containing all approved contrast fixes.
