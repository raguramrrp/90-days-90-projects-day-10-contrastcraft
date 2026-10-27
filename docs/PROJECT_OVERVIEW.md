# Project Overview — ContrastCraft

## 1. Executive Summary
**ContrastCraft** is an automated web accessibility color contrast auditing and remediation studio designed for software engineers, accessibility reviewers, and UI/UX designers. It inspects HTML markup and CSS stylesheets to identify color contrast violations against Web Content Accessibility Guidelines (WCAG 2.1 & 2.2), computes mathematical contrast ratios using official W3C relative luminance formulas, and offers a safe, patch-first remediation workflow with isolated sandboxed live previews.

---

## 2. Problem Statement
The WebAIM Million annual accessibility report consistently reveals that **low contrast text is the #1 accessibility barrier on the web**, detected on over **81% of home pages**.
Traditional developer tools suffer from several practical deficiencies:
1. **Shallow Evaluation:** Chrome DevTools evaluates elements one at a time via element inspection, lacking a cohesive project-wide token audit.
2. **Brute Force Inversion:** Many automated linters or auto-fixers naively replace failing colors with `#000000` or `#FFFFFF`, completely destroying the designer's color palette.
3. **Destructive Overwriting:** Automated tools risk corrupting complex CSS stylesheets or modifying source files without granular diffs and explicit approval.
4. **Cloud / LLM Dependency:** Many recent tools send private source code to external cloud LLM APIs, raising intellectual property and privacy concerns.

ContrastCraft solves these problems with a 100% local-first, mathematically rigorous, hue-preserving, and non-destructive architecture.

---

## 3. Product Scope & Capabilities
| Capability | Description |
| :--- | :--- |
| **Input Flexibility** | Direct HTML/CSS paste, file upload dropzone, or restricted local project folder analysis. |
| **Cascade Resolution** | Resolves inherited text colors, transparent background tree traversals, and selector specificity. |
| **Color Parsing** | Supports 3/4/6/8-digit Hex, standard and CSS4 slash-syntax RGB/RGBA, HSL/HSLA, 140+ W3C named colors, and CSS custom properties (`var(--token)`). |
| **Alpha Compositing** | Deterministic Porter-Duff 'over' operator compositing for semi-transparent layers over opaque backgrounds. |
| **WCAG Success Criteria** | Distinguishes SC 1.4.3 Level AA (4.5:1 normal text, 3.0:1 large text), SC 1.4.6 Level AAA (7.0:1 normal, 4.5:1 large), and SC 1.4.11 Non-text Contrast (3.0:1 UI boundaries). |
| **Confidence Classification** | Grounded classification labeling findings as `verified`, `potential` (contextual cascade), or `needs_browser_verification` (gradients, images). |
| **Hue-Preserving Fix Studio** | Minimal-shift lightness optimization in HSL space, high-contrast anchors, and accessible palette presets. |
| **Isolated Preview** | Sandboxed `<iframe>` rendering with mobile, tablet, and desktop responsive width toggles and target element pulsing outline. |
| **Safe Patching** | Unified CSS diff viewer, `.diff` export, `.bak` file creation on disk writes, and explicit confirmation requirements. |
| **Session Persistence** | Local SQLite storage for saving, renaming, deleting, and comparing audit sessions with score delta metrics. |
| **Offline Privacy** | Operates entirely locally on `http://127.0.0.1:8000` with zero external network calls or cloud dependencies. |
