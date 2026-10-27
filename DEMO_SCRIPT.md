# ContrastCraft — 90-Second Recruiter & Engineering Demo Script

Use this script during portfolio reviews, hackathons, or technical interviews to demonstrate ContrastCraft's architecture, mathematical accuracy, and safe developer workflow.

---

## ⏱️ Timeline & Step-by-Step Sequence

### 0:00 - 0:15 | The Hook & Problem Statement
> *"Hi, I'm Ragu Ram. In modern web development, color contrast accessibility failures affect over 80% of websites, often because designers pick aesthetic muted grays that fail WCAG 2.1 Level AA requirements. Today I built **ContrastCraft**, an automated, local-first web accessibility contrast auditor and CSS patch studio."*

**Action:**
1. Open `http://127.0.0.1:8000`.
2. Point out the custom, developer-oriented UI with dark/light theme toggle.

---

### 0:15 - 0:35 | Input & Real Cascade Analysis
> *"ContrastCraft doesn't just evaluate hardcoded hex codes. It parses the actual HTML DOM hierarchy, evaluates CSS custom properties, inherits cascading parent backgrounds, and computes relative luminance using the exact W3C sRGB linearization formula."*

**Action:**
1. Click **"📁 Load Sample Showcase"**.
2. Point out the sample portfolio containing high-contrast text, normal-text AA failures, large-text headings, UI component borders, and CSS variables.
3. Click **"⚡ Run Contrast Audit"** (or press `Alt + A`).
4. Watch the status indicator switch to `Audited 8 elements` and navigate to **Audit Findings**.

---

### 0:35 - 0:55 | Audit Findings & Grounded Confidence Ratings
> *"Here on the Findings screen, each element is classified against official WCAG criteria: SC 1.4.3 for normal text at 4.5:1, SC 1.4.3 for large text at 3.0:1, and SC 1.4.11 for non-text UI boundaries. Notice we distinguish verified static findings from items that need browser rendering, like CSS gradients."*

**Action:**
1. Click **"Inspect"** on the failing `.hero-caption` subtitle (ratio 2.60:1 vs 4.5:1 requirement).
2. Point out the element hierarchy, calculated luminance values, and exact severity rating in the Inspector drawer.

---

### 0:55 - 1:15 | Fix Studio: Hue-Preserving Mathematics & Live Preview
> *"Rather than blindly replacing failing colors with black or white, ContrastCraft features a recommendation engine that converts the color to HSL and performs an iterative lightness search to find the minimal visual shift that mathematically satisfies WCAG."*

**Action:**
1. Click **"Open in Fix Studio & Preview"**.
2. Select the minimal shift suggestion card.
3. Show the **Unified CSS Diff** displaying the exact targeted declaration change.
4. Switch the **Live Preview** between "Proposed Fix" and "Original View" to demonstrate how the isolated iframe highlights the target element.

---

### 1:15 - 1:30 | Safe Patching, Re-analysis & Export
> *"Safety is a core tenet: ContrastCraft never overwrites unrelated CSS declarations or modifies source files without explicit confirmation. When approved, it re-analyzes the working copy in real-time."*

**Action:**
1. Click **"✨ Apply Patch"** & confirm in the modal.
2. Note the instant re-analysis: compliance score increases from 75% to 87.5%!
3. Switch to **Sessions & Reports** and click **"Download Standalone HTML Report"** to show the self-contained, printable client deliverable.
4. Conclude: *"ContrastCraft is tested with 34 automated unit and integration tests and is 100% offline and local-first."*
