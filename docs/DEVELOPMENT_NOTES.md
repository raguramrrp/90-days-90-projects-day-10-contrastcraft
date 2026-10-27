# Development Notes & Technical Decisions — ContrastCraft

## 1. Technical Decisions & Trade-Offs

### 1.1 Local-First Architecture Over Cloud Services
- **Decision:** Build a self-contained local Python backend with FastAPI and a modern vanilla JavaScript frontend.
- **Rationale:** Web source code and corporate design systems frequently contain proprietary IP. Accessibility tooling must run completely offline without transmitting source code to third-party cloud APIs.
- **Trade-off:** Static parsing in Python cannot execute arbitrary runtime JavaScript (e.g. client-side React hydration or Canvas pixel rendering). We solved this by providing honest confidence classifications (`verified`, `potential`, and `needs_browser_verification`) rather than fabricating assumptions.

### 1.2 Python Standard Library for DOM Parsing
- **Decision:** Use Python's built-in `html.parser.HTMLParser` rather than third-party C-extensions like `lxml` or heavy external engines.
- **Rationale:** Ensures flawless portability across Windows, Linux, and macOS without requiring C++ compilation toolchains. The custom `HTMLTreeBuilder` builds a lightweight DOM tree with full parent-child links and line numbers.

### 1.3 Exact WCAG Mathematical Implementation
- **Decision:** Separate the relative luminance calculation engine completely from UI presentation logic.
- **Rationale:** Guarantees that internal threshold evaluations use exact unrounded floating-point calculations. Ratios are only formatted as string representations (e.g. `4.54:1`) at display time.

### 1.4 Hue-Preserving Recommendation Engine vs Inversion
- **Decision:** Adjust lightness in HSL color space while preserving hue and saturation.
- **Rationale:** Designers reject accessibility tools that blindly invert colors to `#000000` or `#FFFFFF`. Searching along the lightness dimension allows ContrastCraft to preserve the aesthetic intent while achieving mathematically proven WCAG compliance.

---

## 2. Assumptions & Limitations

1. **Static Analysis Boundaries:**
   - Elements rendered dynamically by client-side JavaScript or WebGL cannot be evaluated statically.
   - Background images and gradients are flagged honestly as `needs_browser_verification` because static analysis cannot determine which pixel of a gradient or photograph underlies the text.
2. **Font Metrics Approximation:**
   - In static analysis without a full browser layout engine, font sizes in relative units (`rem`, `em`) are resolved assuming a standard 16px root font size unless specified on `:root`.

---

## 3. Directory Structure
```
90-days-90-projects-day-10-contrastcraft/
├── backend/
│   ├── app/
│   │   ├── api/routes.py            # REST API endpoints
│   │   ├── core/
│   │   │   ├── colors.py            # Color parsing & alpha compositing
│   │   │   ├── contrast.py          # WCAG relative luminance & contrast formulas
│   │   │   ├── classifier.py        # WCAG criteria classification
│   │   │   ├── html_parser.py       # HTML DOM tree builder
│   │   │   ├── css_parser.py        # CSS parsing, specificity & cascade resolver
│   │   │   ├── analyzer.py          # Main audit engine
│   │   │   ├── recommender.py       # Hue-preserving recommendation engine
│   │   │   ├── patcher.py           # CSS patch generator & unified diff
│   │   │   └── reporter.py          # HTML/JSON report generators
│   │   ├── database/
│   │   │   └── session_store.py     # SQLite persistence
│   │   └── main.py                  # FastAPI app entry point
│   └── tests/                       # 34 comprehensive automated tests
├── frontend/                        # Accessible Single Page Application
├── examples/                        # Sample portfolio & styles showcase
├── docs/                            # In-depth technical documentation
├── setup.bat / run.bat / test.bat   # Windows automation scripts
└── README.md / QUICKSTART.md
```
