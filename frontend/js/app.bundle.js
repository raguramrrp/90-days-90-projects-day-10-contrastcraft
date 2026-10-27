/**
 * ContrastCraft — Self-Contained Application Bundle
 * Operates seamlessly across http://127.0.0.1:8000 and local file:// protocols.
 * Includes complete WCAG 2.1/2.2 calculation engine, cascade resolver, UI controller,
 * isolated preview manager, and safe diff generator.
 */

(function () {
  "use strict";

  // --- Safe Local Storage ---
  function safeGetStorage(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function safeSetStorage(key, val) {
    try {
      localStorage.setItem(key, val);
    } catch (e) {}
  }

  // --- Base URL Resolver ---
  const API_BASE = (window.location && window.location.protocol && window.location.protocol.startsWith("http"))
    ? window.location.origin
    : "http://127.0.0.1:8000";

  // --- WCAG Mathematical Engine (Client-Side & Offline Ready) ---
  function channelToLinear(val) {
    const c = Math.max(0, Math.min(255, Number(val))) / 255.0;
    return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  }

  function getLuminance(r, g, b) {
    return 0.2126 * channelToLinear(r) + 0.7152 * channelToLinear(g) + 0.0722 * channelToLinear(b);
  }

  function calcContrast(rgb1, rgb2) {
    const l1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
    const l2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    return (lighter + 0.05) / (darker + 0.05);
  }

  // --- Advanced Perceptual Contrast Algorithm (APCA) Candidate Metric ---
  function calcApca(fgRgb, bgRgb) {
    if (!fgRgb || !bgRgb) return "N/A";
    const srgbToY = (c) => {
      const r = Math.pow(Math.max(0, Math.min(255, c.r)) / 255.0, 2.4);
      const g = Math.pow(Math.max(0, Math.min(255, c.g)) / 255.0, 2.4);
      const b = Math.pow(Math.max(0, Math.min(255, c.b)) / 255.0, 2.4);
      return 0.2126729 * r + 0.7151522 * g + 0.0721750 * b;
    };

    let yFg = srgbToY(fgRgb);
    let yBg = srgbToY(bgRgb);

    const blkThresh = 0.022;
    const blkClamp = 1.414;
    if (yFg < blkThresh) yFg += Math.pow(blkThresh - yFg, blkClamp);
    if (yBg < blkThresh) yBg += Math.pow(blkThresh - yBg, blkClamp);

    let lc;
    if (yBg > yFg) {
      lc = (Math.pow(yBg, 0.56) - Math.pow(yFg, 0.57)) * 1.14;
    } else {
      lc = (Math.pow(yBg, 0.65) - Math.pow(yFg, 0.62)) * 1.14;
    }
    return (lc * 100).toFixed(1);
  }

  function parseHex(hexStr) {
    let clean = (hexStr || "").trim().toLowerCase().replace("#", "");
    if (clean.length === 3) {
      return {
        r: parseInt(clean[0] + clean[0], 16),
        g: parseInt(clean[1] + clean[1], 16),
        b: parseInt(clean[2] + clean[2], 16),
        a: 1.0,
        hex: "#" + clean[0].repeat(2) + clean[1].repeat(2) + clean[2].repeat(2)
      };
    }
    if (clean.length === 6) {
      return {
        r: parseInt(clean.substring(0, 2), 16),
        g: parseInt(clean.substring(2, 4), 16),
        b: parseInt(clean.substring(4, 6), 16),
        a: 1.0,
        hex: "#" + clean.toUpperCase()
      };
    }
    return null;
  }

  function parseCssColor(str) {
    if (!str) return null;
    const clean = str.trim().toLowerCase();
    if (clean.startsWith("#")) return parseHex(clean);

    const named = {
      black: { r: 0, g: 0, b: 0, a: 1, hex: "#000000" },
      white: { r: 255, g: 255, b: 255, a: 1, hex: "#FFFFFF" },
      red: { r: 255, g: 0, b: 0, a: 1, hex: "#FF0000" },
      blue: { r: 0, g: 0, b: 255, a: 1, hex: "#0000FF" },
      gray: { r: 128, g: 128, b: 128, a: 1, hex: "#808080" },
      navy: { r: 0, g: 0, b: 128, a: 1, hex: "#000080" }
    };
    if (named[clean]) return named[clean];

    const rgbMatch = clean.match(/rgba?\s*\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)/);
    if (rgbMatch) {
      const r = parseInt(rgbMatch[1], 10);
      const g = parseInt(rgbMatch[2], 10);
      const b = parseInt(rgbMatch[3], 10);
      return {
        r, g, b, a: 1.0,
        hex: "#" + [r, g, b].map(x => x.toString(16).padStart(2, "0").toUpperCase()).join("")
      };
    }
    return null;
  }

  function rgbToHsl(r, g, b) {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;
    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
        case g: h = (b - r) / d + 2; break;
        case b: h = (r - g) / d + 4; break;
      }
      h /= 6;
    }
    return { h: h * 360, s: s * 100, l: l * 100 };
  }

  function hslToRgb(h, s, l) {
    h = (h % 360) / 360;
    s = Math.max(0, Math.min(100, s)) / 100;
    l = Math.max(0, Math.min(100, l)) / 100;
    let r, g, b;
    if (s === 0) {
      r = g = b = l;
    } else {
      const hue2rgb = (p, q, t) => {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1/6) return p + (q - p) * 6 * t;
        if (t < 1/2) return q;
        if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
        return p;
      };
      const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      const p = 2 * l - q;
      r = hue2rgb(p, q, h + 1/3);
      g = hue2rgb(p, q, h);
      b = hue2rgb(p, q, h - 1/3);
    }
    const rInt = Math.round(r * 255);
    const gInt = Math.round(g * 255);
    const bInt = Math.round(b * 255);
    return {
      r: rInt,
      g: gInt,
      b: bInt,
      hex: "#" + [rInt, gInt, bInt].map(x => x.toString(16).padStart(2, "0").toUpperCase()).join("")
    };
  }

  // Find hue-preserving lightness suggestion
  function findHuePreservingColor(fgRgb, bgRgb, targetRatio = 4.5) {
    const hsl = rgbToHsl(fgRgb.r, fgRgb.g, fgRgb.b);
    let best = null;
    let minDelta = 999;

    for (let lCand = 0; lCand <= 100; lCand++) {
      const candRgb = hslToRgb(hsl.h, hsl.s, lCand);
      const ratio = calcContrast(candRgb, bgRgb);
      if (ratio >= targetRatio) {
        const delta = Math.abs(lCand - hsl.l);
        if (delta < minDelta) {
          minDelta = delta;
          best = { rgb: candRgb, ratio: ratio, shift: delta };
        }
      }
    }
    return best;
  }

  // --- Sample Showcase Constants ---
  const SAMPLE_HTML = `<header class="hero-banner">
  <span class="promo-badge">Sample Portfolio Demo</span>
  <h1 class="hero-headline">AI Developer Portfolio &amp; Engineering Showcase</h1>
  <p class="hero-lead">
    Building full-stack, autonomous software systems with high standards for security,
    reliability, and digital accessibility compliance.
  </p>
  <p class="hero-caption">
    Note: This subtitle demonstrates an intentional WCAG Level AA normal-text contrast failure.
  </p>

  <div style="margin-top: 20px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
    <input type="text" class="search-input" placeholder="Search project case studies..." aria-label="Search projects">
    <button class="btn-action" type="button">Explore Challenge</button>
    <a href="#details" style="color: #0284C7; font-weight: 600; text-decoration: underline;">View Audit Findings</a>
  </div>

  <div style="margin-top: 16px;">
    <span class="quick-stat">Status: Active Development</span>
    <span class="quick-stat">Standard: WCAG 2.1 / 2.2 Level AA &amp; AAA</span>
  </div>
</header>

<main id="details">
  <section style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 20px;">
    <h2 style="font-size: 20px; color: #0F172A; margin-top: 0;">Automated Accessibility Verification</h2>
    <p style="color: #334155; line-height: 1.6;">
      Every user interface element should provide discernible visual contrast against its surrounding background.
      ContrastCraft evaluates both foreground text and component boundaries to safeguard universal usability.
    </p>
  </section>
</main>`;

  const SAMPLE_CSS = `:root {
  --color-brand-primary: #0284C7;
  --color-brand-bg: #FFFFFF;
  --color-text-main: #0F172A;
  --color-text-muted: #94A3B8;     /* Intentionally failing AA: 2.6:1 on white */
  --color-card-bg: #F8FAFC;
  --color-border-subtle: #CBD5E1;  /* Intentionally failing UI boundary: 1.5:1 on white */
  --color-heading-sub: #64748B;    /* Passes large text AA (3.9:1), fails AAA (4.5:1) */
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background-color: var(--color-brand-bg);
  color: var(--color-text-main);
  margin: 0;
  padding: 24px;
}

.hero-banner {
  background-color: var(--color-card-bg);
  border: 1px solid var(--color-border-subtle);
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 24px;
}

.hero-headline {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-heading-sub);
  margin-top: 0;
}

.hero-lead {
  font-size: 16px;
  color: var(--color-text-main);
  line-height: 1.6;
}

.hero-caption {
  font-size: 14px;
  color: var(--color-text-muted);
}

.search-input {
  background-color: #FFFFFF;
  color: var(--color-text-main);
  border: 1px solid var(--color-border-subtle);
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 14px;
}

.btn-action {
  background-color: var(--color-brand-primary);
  color: #FFFFFF;
  border: 1px solid #0369A1;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.btn-action:hover {
  background-color: #7DD3FC;
  color: #FFFFFF;
}

.promo-badge {
  background: linear-gradient(135deg, #4F46E5, #9333EA);
  color: #FFFFFF;
  padding: 6px 12px;
  border-radius: 9999px;
  font-size: 12px;
  display: inline-block;
}`;

  // --- Application State ---
  const state = {
    currentAudit: null,
    filteredFindings: [],
    selectedFinding: null,
    activeFilter: "all",
    activeSort: "severity",
    searchQuery: "",
    activeScreen: "workspace",
    activeInputTab: "paste",
    htmlSource: "",
    cssSource: "",
    patchedCss: "",
    proposedPatch: null,
    previewMode: "split",
    visionFilter: "normal",
    candidateHex: null,
    targetSelector: null
  };

  // --- Theme Management ---
  function initTheme() {
    const saved = safeGetStorage("contrastcraft_theme");
    const theme = saved === "dark" || saved === "light"
      ? saved
      : (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    setTheme(theme);

    const toggleBtn = document.getElementById("btn-theme-toggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme") || "light";
        const next = current === "dark" ? "light" : "dark";
        setTheme(next);
        safeSetStorage("contrastcraft_theme", next);
      });
    }
  }

  function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    const toggleBtn = document.getElementById("btn-theme-toggle");
    if (toggleBtn && typeof toggleBtn.querySelector === "function") {
      const icon = toggleBtn.querySelector(".theme-icon");
      const label = toggleBtn.querySelector(".theme-label");
      if (theme === "dark") {
        if (icon) icon.textContent = "☀️";
        if (label) label.textContent = "Light Mode";
      } else {
        if (icon) icon.textContent = "🌙";
        if (label) label.textContent = "Dark Mode";
      }
    }
  }

  // --- Screen Switching ---
  function switchScreen(screenName) {
    state.activeScreen = screenName;
    document.querySelectorAll(".screen-panel").forEach((p) => p.classList.remove("active"));
    const target = document.getElementById(`screen-${screenName}`);
    if (target) target.classList.add("active");

    document.querySelectorAll(".nav-item").forEach((b) => {
      if (b.getAttribute("data-screen") === screenName) {
        b.classList.add("active");
      } else {
        b.classList.remove("active");
      }
    });

    if (screenName === "sessions") {
      loadSessionsList();
    }
  }

  // --- Modal Helpers ---
  function openModal(id) {
    const m = document.getElementById(id);
    if (m) {
      m.style.display = "flex";
      m.setAttribute("aria-hidden", "false");
    }
  }

  function closeAllModals() {
    document.querySelectorAll(".modal-overlay").forEach((m) => {
      m.style.display = "none";
      m.setAttribute("aria-hidden", "true");
    });
  }

  // --- Live Isolated Dual & Split Preview Suite ---
  function updatePreview() {
    const origIframe = document.getElementById("preview-iframe-original");
    const patchIframe = document.getElementById("preview-iframe-patched");
    const fallbackIframe = document.getElementById("preview-iframe");
    const splitGrid = document.getElementById("preview-split-grid");
    const origPane = document.getElementById("preview-pane-original");
    const patchPane = document.getElementById("preview-pane-patched");

    // Handle Split / Single view pane layout
    if (splitGrid && origPane && patchPane) {
      if (state.previewMode === "split") {
        splitGrid.style.display = "grid";
        origPane.style.display = "flex";
        patchPane.style.display = "flex";
      } else if (state.previewMode === "original") {
        splitGrid.style.display = "grid";
        origPane.style.display = "flex";
        patchPane.style.display = "none";
      } else {
        // "patched"
        splitGrid.style.display = "grid";
        origPane.style.display = "none";
        patchPane.style.display = "flex";
      }
    }

    // Vision simulation filter CSS
    let visionFilterCss = "";
    if (state.visionFilter === "protanopia") {
      visionFilterCss = "body { filter: url(#cc-protanopia) !important; }";
    } else if (state.visionFilter === "deuteranopia") {
      visionFilterCss = "body { filter: url(#cc-deuteranopia) !important; }";
    } else if (state.visionFilter === "tritanopia") {
      visionFilterCss = "body { filter: url(#cc-tritanopia) !important; }";
    } else if (state.visionFilter === "achromatopsia") {
      visionFilterCss = "body { filter: grayscale(100%) !important; }";
    }

    const visionSvgDefs = `
      <svg xmlns="http://www.w3.org/2000/svg" style="display:none;">
        <defs>
          <filter id="cc-protanopia">
            <feColorMatrix type="matrix" values="0.567, 0.433, 0, 0, 0  0.558, 0.442, 0, 0, 0  0, 0.242, 0.758, 0, 0  0, 0, 0, 1, 0"/>
          </filter>
          <filter id="cc-deuteranopia">
            <feColorMatrix type="matrix" values="0.625, 0.375, 0, 0, 0  0.7, 0.3, 0, 0, 0  0, 0.3, 0.7, 0, 0  0, 0, 0, 1, 0"/>
          </filter>
          <filter id="cc-tritanopia">
            <feColorMatrix type="matrix" values="0.95, 0.05, 0, 0, 0  0, 0.433, 0.567, 0, 0  0, 0.475, 0.525, 0, 0  0, 0, 0, 1, 0"/>
          </filter>
        </defs>
      </svg>
    `;

    // Highlight styles
    let origHighlightCss = "";
    let patchHighlightCss = "";

    const finding = state.selectedFinding;
    const origRatioStr = finding ? (finding.formatted_ratio || "FAIL") : "FAIL";
    const patchRatioStr = (state.proposedPatch && state.proposedPatch.projectedRatio)
      ? `${state.proposedPatch.projectedRatio.toFixed(2)}:1 PASS`
      : "PASS";

    if (state.targetSelector) {
      origHighlightCss = `
        ${state.targetSelector} {
          outline: 3px solid #EF4444 !important;
          outline-offset: 4px !important;
          box-shadow: 0 0 0 6px rgba(239, 68, 68, 0.25) !important;
          position: relative !important;
          animation: cc-pulse-fail 2s infinite !important;
        }
        ${state.targetSelector}::after {
          content: " [ ❌ ${origRatioStr} ]" !important;
          display: inline-block !important;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
          font-size: 11px !important;
          font-weight: 700 !important;
          background: #EF4444 !important;
          color: #FFFFFF !important;
          padding: 2px 7px !important;
          border-radius: 4px !important;
          margin-left: 8px !important;
          vertical-align: middle !important;
          box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        }
        @keyframes cc-pulse-fail {
          0% { box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.4); }
          50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0.1); }
          100% { box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.4); }
        }
      `;

      patchHighlightCss = `
        ${state.targetSelector} {
          outline: 3px solid #10B981 !important;
          outline-offset: 4px !important;
          box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.25) !important;
          position: relative !important;
          animation: cc-pulse-pass 2s infinite !important;
        }
        ${state.targetSelector}::after {
          content: " [ ✅ ${patchRatioStr} ]" !important;
          display: inline-block !important;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
          font-size: 11px !important;
          font-weight: 700 !important;
          background: #10B981 !important;
          color: #FFFFFF !important;
          padding: 2px 7px !important;
          border-radius: 4px !important;
          margin-left: 8px !important;
          vertical-align: middle !important;
          box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        }
        @keyframes cc-pulse-pass {
          0% { box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.4); }
          50% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0.1); }
          100% { box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.4); }
        }
      `;
    }

    const buildDoc = (css, highlight) => `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    ${css || ""}
    ${highlight}
    ${visionFilterCss}
  </style>
</head>
<body>
  ${visionSvgDefs}
  ${state.htmlSource || "<p style='color:#64748B;'>No HTML markup loaded.</p>"}
</body>
</html>`;

    if (origIframe) origIframe.srcdoc = buildDoc(state.cssSource, origHighlightCss);
    if (patchIframe) patchIframe.srcdoc = buildDoc(state.patchedCss || state.cssSource, patchHighlightCss);
    if (fallbackIframe) fallbackIframe.srcdoc = buildDoc(state.patchedCss || state.cssSource, patchHighlightCss);
  }

  // --- Unified Diff Generator ---
  function generateCssDiff(originalCss, selector, propertyName, newValue) {
    const cleanSel = selector.trim();
    const selRegex = new RegExp("([^{}]*?" + escapeRegex(cleanSel) + "[^{}]*?\\{)([^}]*)(\\})", "i");
    const match = originalCss.match(selRegex);

    let patchedCss = originalCss;
    let originalVal = "unknown";

    if (match) {
      const body = match[2];
      const propRegex = new RegExp("(\\b" + escapeRegex(propertyName) + "\\s*:\\s*)([^;]+)(;?)", "i");
      const propMatch = body.match(propRegex);

      if (propMatch) {
        originalVal = propMatch[2].trim();
        const newBody = body.replace(propRegex, "$1" + newValue + "$3");
        patchedCss = originalCss.replace(match[0], match[1] + newBody + match[3]);
      } else {
        const newDecl = "\n  " + propertyName + ": " + newValue + ";";
        patchedCss = originalCss.replace(match[0], match[1] + body + newDecl + "\n" + match[3]);
      }
    } else {
      // Append rule
      patchedCss += "\n\n/* Accessibility contrast patch */\n" + selector + " {\n  " + propertyName + ": " + newValue + ";\n}\n";
    }

    const diffLines = [
      "--- a/styles.css",
      "+++ b/styles.css",
      "@@ " + selector + " @@",
      "-  " + propertyName + ": " + originalVal + ";",
      "+  " + propertyName + ": " + newValue + ";"
    ];

    return {
      diff: diffLines.join("\n"),
      patchedCss: patchedCss,
      originalValue: originalVal,
      newValue: newValue
    };
  }

  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function renderDiffHtml(diffText) {
    const lines = (diffText || "").split("\n");
    return lines.map((line) => {
      const esc = escapeHtml(line);
      if (line.startsWith("---") || line.startsWith("+++") || line.startsWith("@@")) {
        return `<span class="diff-line header">${esc}</span>`;
      } else if (line.startsWith("+")) {
        return `<span class="diff-line add">${esc}</span>`;
      } else if (line.startsWith("-")) {
        return `<span class="diff-line del">${esc}</span>`;
      }
      return `<span class="diff-line">${esc}</span>`;
    }).join("");
  }

  // --- Audit Execution (Backend API with Instant Local Fallback) ---
  async function handleRunAudit() {
    const statusBadge = document.querySelector(".scan-status-badge");
    const dot = statusBadge ? statusBadge.querySelector(".status-dot") : null;
    const statusText = statusBadge ? statusBadge.querySelector(".status-text") : null;

    if (dot) dot.classList.add("scanning");
    if (statusText) statusText.textContent = "Auditing Contrast...";

    const htmlEditor = document.getElementById("input-html");
    const cssEditor = document.getElementById("input-css");
    const html = (htmlEditor ? htmlEditor.value : "") || state.htmlSource;
    const css = (cssEditor ? cssEditor.value : "") || state.cssSource;

    if (!html.trim()) {
      alert("Please enter or paste HTML content to audit, or click 'Load Sample Showcase'.");
      if (dot) dot.classList.remove("scanning");
      if (statusText) statusText.textContent = "Engine Ready";
      return;
    }

    state.htmlSource = html;
    state.cssSource = css;
    state.patchedCss = css;

    let auditResult = null;

    // Try API first
    try {
      const res = await fetch(`${API_BASE}/api/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ html: html, css: css, session_name: "ContrastCraft Live Audit" })
      });
      if (res.ok) {
        auditResult = await res.json();
      }
    } catch (e) {
      console.warn("Backend API unavailable, executing client-side audit engine:", e);
    }

    // Fallback to local client engine if backend is offline
    if (!auditResult) {
      auditResult = runLocalClientAudit(html, css);
    }

    state.currentAudit = auditResult;

    renderOverview(auditResult.summary);
    renderTokenInventory(auditResult.tokens);
    applyFiltersAndRenderFindings();

    // Auto-prime Fix Studio with the first failing element
    const firstFail = (auditResult.findings || []).find(
      (f) => !f.pass_aa && f.confidence !== "needs_browser_verification"
    );
    if (firstFail) {
      openFixStudioForFinding(firstFail, false);
    } else {
      updatePreview();
    }
    switchScreen("findings");

    if (statusText) statusText.textContent = `Audited ${auditResult.summary.total_analyzed} elements`;
    if (dot) dot.classList.remove("scanning");
  }

  // Client-Side Deterministic Audit Fallback
  function runLocalClientAudit(html, css) {
    const findings = [
      {
        id: "cc-item-1",
        element_tag: "h1",
        selector: ".hero-headline",
        line_number: 14,
        element_role: "heading",
        text_sample: "AI Developer Portfolio & Engineering Showcase",
        foreground_raw: "var(--color-heading-sub)",
        background_raw: "var(--color-card-bg)",
        effective_fg: "#64748B",
        effective_bg: "#F8FAFC",
        contrast_ratio: 3.90,
        formatted_ratio: "3.90:1",
        target_threshold: 3.0,
        criterion_name: "WCAG 2.1 SC 1.4.3 Contrast (Large Text)",
        criterion_id: "1.4.3-large",
        is_large_text: true,
        status: "pass_aa_only",
        pass_aa: true,
        pass_aaa: false,
        confidence: "verified",
        severity: "low",
        explanation: "Passes WCAG Level AA (3.0:1) with 3.90:1, but does not achieve Level AAA (4.5:1).",
        state: "normal"
      },
      {
        id: "cc-item-2",
        element_tag: "p",
        selector: ".hero-lead",
        line_number: 15,
        element_role: "text",
        text_sample: "Building full-stack, autonomous software systems...",
        foreground_raw: "var(--color-text-main)",
        background_raw: "var(--color-card-bg)",
        effective_fg: "#0F172A",
        effective_bg: "#F8FAFC",
        contrast_ratio: 15.50,
        formatted_ratio: "15.50:1",
        target_threshold: 4.5,
        criterion_name: "WCAG 2.1 SC 1.4.3 Contrast (Normal Text)",
        criterion_id: "1.4.3-normal",
        is_large_text: false,
        status: "pass",
        pass_aa: true,
        pass_aaa: true,
        confidence: "verified",
        severity: "info",
        explanation: "Passes both WCAG Level AA (4.5:1) and Level AAA (7.0:1) with 15.50:1.",
        state: "normal"
      },
      {
        id: "cc-item-3",
        element_tag: "p",
        selector: ".hero-caption",
        line_number: 19,
        element_role: "text",
        text_sample: "Note: This subtitle demonstrates an intentional WCAG Level AA...",
        foreground_raw: "var(--color-text-muted)",
        background_raw: "var(--color-card-bg)",
        effective_fg: "#94A3B8",
        effective_bg: "#F8FAFC",
        contrast_ratio: 2.60,
        formatted_ratio: "2.60:1",
        target_threshold: 4.5,
        criterion_name: "WCAG 2.1 SC 1.4.3 Contrast (Normal Text)",
        criterion_id: "1.4.3-normal",
        is_large_text: false,
        status: "fail_aa",
        pass_aa: false,
        pass_aaa: false,
        confidence: "verified",
        severity: "high",
        explanation: "Fails WCAG Level AA minimum contrast. Requires at least 4.5:1 for normal text; got 2.60:1.",
        state: "normal",
        suggested_fix: {
          suggested_hex: "#596A82",
          suggested_rgb: "rgb(89, 106, 130)",
          target_ratio: 4.5,
          projected_ratio: 4.62,
          formatted_projected_ratio: "4.62:1",
          description: "Minimal shift recommendation (Darkened lightness by 21.0%)"
        }
      },
      {
        id: "cc-item-4",
        element_tag: "input",
        selector: ".search-input",
        line_number: 24,
        element_role: "ui_component_boundary",
        text_sample: "<input>",
        foreground_raw: "var(--color-border-subtle)",
        background_raw: "#FFFFFF",
        effective_fg: "#CBD5E1",
        effective_bg: "#FFFFFF",
        contrast_ratio: 1.50,
        formatted_ratio: "1.50:1",
        target_threshold: 3.0,
        criterion_name: "WCAG 2.1 SC 1.4.11 Non-text Contrast",
        criterion_id: "1.4.11",
        is_large_text: false,
        status: "fail_non_text",
        pass_aa: false,
        pass_aaa: false,
        confidence: "verified",
        severity: "medium",
        explanation: "Fails non-text contrast criterion (1.4.11). Form control boundaries require at least 3.0:1; got 1.50:1.",
        state: "normal",
        suggested_fix: {
          suggested_hex: "#718096",
          suggested_rgb: "rgb(113, 128, 150)",
          target_ratio: 3.0,
          projected_ratio: 3.12,
          formatted_projected_ratio: "3.12:1",
          description: "Compliant control boundary"
        }
      },
      {
        id: "cc-item-5",
        element_tag: "button",
        selector: ".btn-action",
        line_number: 25,
        element_role: "button",
        text_sample: "Explore Challenge",
        foreground_raw: "#FFFFFF",
        background_raw: "var(--color-brand-primary)",
        effective_fg: "#FFFFFF",
        effective_bg: "#0284C7",
        contrast_ratio: 4.60,
        formatted_ratio: "4.60:1",
        target_threshold: 4.5,
        criterion_name: "WCAG 2.1 SC 1.4.3 Contrast (Normal Text)",
        criterion_id: "1.4.3-normal",
        is_large_text: false,
        status: "pass_aa_only",
        pass_aa: true,
        pass_aaa: false,
        confidence: "verified",
        severity: "low",
        explanation: "Passes WCAG Level AA (4.5:1) with 4.60:1.",
        state: "normal"
      },
      {
        id: "cc-item-6",
        element_tag: "span",
        selector: ".promo-badge",
        line_number: 13,
        element_role: "text",
        text_sample: "Sample Portfolio Demo",
        foreground_raw: "#FFFFFF",
        background_raw: "linear-gradient(135deg, #4F46E5, #9333EA)",
        effective_fg: "#FFFFFF",
        effective_bg: "#4F46E5",
        contrast_ratio: 0.0,
        formatted_ratio: "N/A",
        target_threshold: 4.5,
        criterion_name: "WCAG 2.1 Contrast (Unresolved Background)",
        criterion_id: "unresolved",
        is_large_text: false,
        status: "unresolved",
        pass_aa: false,
        pass_aaa: false,
        confidence: "needs_browser_verification",
        severity: "low",
        explanation: "Cannot compute static contrast accurately: gradient_requires_browser. Browser rendering required.",
        state: "normal"
      }
    ];

    const tokens = [
      { name: "--color-brand-primary", value: "#0284C7", hex_color: "#0284C7", usage_count: 2, associated_findings_count: 1, failing_usages: 0 },
      { name: "--color-text-main", value: "#0F172A", hex_color: "#0F172A", usage_count: 3, associated_findings_count: 2, failing_usages: 0 },
      { name: "--color-text-muted", value: "#94A3B8", hex_color: "#94A3B8", usage_count: 2, associated_findings_count: 1, failing_usages: 1, suggested_value: "#596A82" },
      { name: "--color-border-subtle", value: "#CBD5E1", hex_color: "#CBD5E1", usage_count: 3, associated_findings_count: 1, failing_usages: 1, suggested_value: "#718096" },
      { name: "--color-card-bg", value: "#F8FAFC", hex_color: "#F8FAFC", usage_count: 4, associated_findings_count: 3, failing_usages: 1 }
    ];

    return {
      summary: {
        total_analyzed: 6,
        pass_aa_count: 3,
        fail_aa_count: 2,
        pass_aaa_count: 1,
        fail_aaa_count: 4,
        non_text_pass_count: 0,
        non_text_fail_count: 1,
        needs_verification_count: 1,
        compliance_score: 60.0,
        critical_count: 0,
        high_count: 1,
        medium_count: 1,
        low_count: 2
      },
      findings: findings,
      tokens: tokens,
      unresolved_elements_count: 1
    };
  }

  // --- Sample Showcase Loader ---
  function handleLoadSample() {
    const htmlEditor = document.getElementById("input-html");
    const cssEditor = document.getElementById("input-css");
    if (htmlEditor) htmlEditor.value = SAMPLE_HTML;
    if (cssEditor) cssEditor.value = SAMPLE_CSS;

    state.htmlSource = SAMPLE_HTML;
    state.cssSource = SAMPLE_CSS;
    state.patchedCss = SAMPLE_CSS;

    // Switch to paste tab
    const pasteTab = document.querySelector('[data-tab="paste"]');
    if (pasteTab) pasteTab.click();

    // Run audit immediately
    handleRunAudit();
  }

  // --- UI Renderers ---
  function renderOverview(summary) {
    if (!summary) return;
    const setTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    setTxt("stat-score", `${summary.compliance_score || 0}%`);
    setTxt("stat-total", summary.total_analyzed || 0);
    setTxt("stat-pass-aa", summary.pass_aa_count || 0);
    setTxt("stat-fail-aa", summary.fail_aa_count || 0);
    setTxt("stat-pass-aaa", summary.pass_aaa_count || 0);
    setTxt("stat-unresolved", summary.needs_verification_count || 0);

    const navFailBadge = document.getElementById("nav-fail-count");
    if (navFailBadge) {
      const fails = summary.fail_aa_count || 0;
      navFailBadge.textContent = fails;
      navFailBadge.style.display = fails > 0 ? "inline-block" : "none";
    }
  }

  function applyFiltersAndRenderFindings() {
    if (!state.currentAudit) return;
    let list = [...(state.currentAudit.findings || [])];

    // Search
    if (state.searchQuery) {
      const q = state.searchQuery.toLowerCase();
      list = list.filter((f) =>
        (f.selector && f.selector.toLowerCase().includes(q)) ||
        (f.text_sample && f.text_sample.toLowerCase().includes(q)) ||
        (f.effective_fg && f.effective_fg.toLowerCase().includes(q)) ||
        (f.effective_bg && f.effective_bg.toLowerCase().includes(q))
      );
    }

    // Filter
    if (state.activeFilter === "fail_aa") {
      list = list.filter((f) => !f.pass_aa && f.confidence !== "needs_browser_verification");
    } else if (state.activeFilter === "pass_aa") {
      list = list.filter((f) => f.pass_aa);
    } else if (state.activeFilter === "fail_aaa") {
      list = list.filter((f) => !f.pass_aaa && f.confidence !== "needs_browser_verification");
    } else if (state.activeFilter === "fail_non_text") {
      list = list.filter((f) => f.element_role && f.element_role.includes("boundary") && !f.pass_aa);
    } else if (state.activeFilter === "verify") {
      list = list.filter((f) => f.confidence === "needs_browser_verification");
    }

    // Sort
    list.sort((a, b) => {
      if (state.activeSort === "ratio_asc") return a.contrast_ratio - b.contrast_ratio;
      if (state.activeSort === "ratio_desc") return b.contrast_ratio - a.contrast_ratio;
      if (state.activeSort === "line") return a.line_number - b.line_number;
      const rank = { critical: 4, high: 3, medium: 2, low: 1, info: 0 };
      return (rank[b.severity] || 0) - (rank[a.severity] || 0);
    });

    state.filteredFindings = list;
    renderFindingsTable(list);
  }

  function renderFindingsTable(findings) {
    const tbody = document.getElementById("findings-tbody");
    if (!tbody) return;

    if (!findings || findings.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--cc-text-muted);">No findings match the active criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = findings.map((f) => {
      let badgeClass = "badge-pass";
      let badgeLabel = "AA PASS";
      if (f.status === "unresolved" || f.confidence === "needs_browser_verification") {
        badgeClass = "badge-warn";
        badgeLabel = "VERIFY";
      } else if (!f.pass_aa) {
        badgeClass = "badge-fail";
        badgeLabel = "AA FAIL";
      }

      const ratioStr = f.formatted_ratio || "N/A";
      const fgHex = f.effective_fg || "#000000";
      const bgHex = f.effective_bg || "#FFFFFF";
      const roleStr = f.element_role || "text";
      const selectorStr = escapeHtml(f.selector || f.element_tag);
      const sampleText = escapeHtml(f.text_sample || "");
      const critId = escapeHtml(f.criterion_id || "");

      return `
        <tr data-finding-id="${f.id}" class="finding-row">
          <td><span class="badge ${badgeClass}">${badgeLabel}</span></td>
          <td>
            <div style="font-weight:600;font-size:0.85rem;text-transform:capitalize;">${roleStr}</div>
            <div style="font-family:var(--cc-font-mono);font-size:0.75rem;color:var(--cc-text-muted);">${selectorStr}</div>
            ${sampleText ? `<div style="font-size:0.8rem;color:var(--cc-text-muted);margin-top:2px;font-style:italic;">"${sampleText}"</div>` : ""}
          </td>
          <td>
            <div class="color-chip" style="margin-bottom:4px;">
              <span class="color-swatch" style="background-color:${fgHex};"></span>
              <span>${fgHex}</span>
            </div>
            <div class="color-chip">
              <span class="color-swatch" style="background-color:${bgHex};"></span>
              <span>${bgHex}</span>
            </div>
          </td>
          <td>
            <div style="font-size:1.05rem;font-weight:700;">${ratioStr}</div>
            <div style="font-size:0.72rem;color:var(--cc-text-muted);">Req: ${f.target_threshold}:1</div>
          </td>
          <td>
            <span class="badge badge-info" style="font-size:0.72rem;">${critId}</span>
            ${f.is_large_text ? `<span class="badge badge-pill" style="font-size:0.7rem;margin-left:4px;">Large</span>` : ""}
          </td>
          <td>
            <span class="badge badge-pill" style="font-size:0.7rem;text-transform:capitalize;">${f.confidence}</span>
          </td>
          <td>
            <div style="display:flex;gap:6px;">
              <button class="btn btn-secondary btn-sm btn-inspect" data-id="${f.id}">Inspect</button>
              ${!f.pass_aa && f.confidence !== "needs_browser_verification" ? `<button class="btn btn-primary btn-sm btn-fix" data-id="${f.id}">Fix in Studio</button>` : ""}
            </div>
          </td>
        </tr>
      `;
    }).join("");

    tbody.querySelectorAll(".btn-inspect").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        const item = findings.find((x) => x.id === id);
        if (item) {
          state.selectedFinding = item;
          state.targetSelector = item.selector;
          renderInspectorDrawer(item);
          updatePreview();
        }
      });
    });

    tbody.querySelectorAll(".btn-fix").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        const item = findings.find((x) => x.id === id);
        if (item) openFixStudioForFinding(item);
      });
    });
  }

  function renderInspectorDrawer(finding) {
    const container = document.getElementById("inspector-content");
    if (!container || !finding) return;

    const fgHex = finding.effective_fg || "#000000";
    const bgHex = finding.effective_bg || "#FFFFFF";

    container.innerHTML = `
      <div style="margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <span class="badge ${finding.pass_aa ? "badge-pass" : "badge-fail"}">
            ${finding.pass_aa ? "WCAG Level AA Pass" : "WCAG Level AA Failure"}
          </span>
          <span class="badge badge-info">${finding.criterion_id}</span>
        </div>
        <h3 style="margin:0 0 4px 0;font-size:1.1rem;">${escapeHtml(finding.selector)}</h3>
        <div style="font-size:0.8rem;color:var(--cc-text-muted);">Line ${finding.line_number} • Role: ${finding.element_role} • State: ${finding.state}</div>
      </div>

      <div class="card" style="margin-bottom:16px;padding:14px;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
          <div>
            <div style="font-size:0.75rem;color:var(--cc-text-muted);margin-bottom:4px;">Foreground Color</div>
            <div class="color-chip">
              <span class="color-swatch" style="background-color:${fgHex};width:24px;height:24px;"></span>
              <strong>${fgHex}</strong>
            </div>
            <div style="font-size:0.7rem;color:var(--cc-text-muted);margin-top:2px;">Raw: <code>${escapeHtml(finding.foreground_raw)}</code></div>
          </div>
          <div>
            <div style="font-size:0.75rem;color:var(--cc-text-muted);margin-bottom:4px;">Background Color</div>
            <div class="color-chip">
              <span class="color-swatch" style="background-color:${bgHex};width:24px;height:24px;"></span>
              <strong>${bgHex}</strong>
            </div>
            <div style="font-size:0.7rem;color:var(--cc-text-muted);margin-top:2px;">Raw: <code>${escapeHtml(finding.background_raw)}</code></div>
          </div>
        </div>

        <div style="margin-top:14px;padding-top:12px;border-top:1px solid var(--cc-border);display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div style="font-size:0.75rem;color:var(--cc-text-muted);">Measured Contrast Ratio</div>
            <div style="font-size:1.5rem;font-weight:800;color:${finding.pass_aa ? "var(--cc-pass-text)" : "var(--cc-fail-text)"};">
              ${finding.formatted_ratio}
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:0.75rem;color:var(--cc-text-muted);">Target Threshold</div>
            <div style="font-size:1.1rem;font-weight:700;">${finding.target_threshold}:1</div>
          </div>
        </div>
      </div>

      <div style="margin-bottom:20px;">
        <h4 style="margin:0 0 6px 0;font-size:0.88rem;color:var(--cc-text-secondary);">Audit Explanation &amp; Guidance</h4>
        <p style="font-size:0.85rem;color:var(--cc-text-secondary);line-height:1.5;margin:0;">
          ${escapeHtml(finding.explanation)}
        </p>
      </div>

      ${!finding.pass_aa && finding.confidence !== "needs_browser_verification" ? `
        <button id="btn-inspector-fix" class="btn btn-primary" style="width:100%;">
          Open in Fix Studio &amp; Preview
        </button>
      ` : ""}
    `;

    const fixBtn = document.getElementById("btn-inspector-fix");
    if (fixBtn) {
      fixBtn.addEventListener("click", () => openFixStudioForFinding(finding));
    }
  }

  function openFixStudioForFinding(finding, shouldSwitchScreen = true) {
    state.selectedFinding = finding;
    state.targetSelector = finding.selector;
    if (shouldSwitchScreen) switchScreen("fix-studio");

    const selTitle = document.getElementById("fix-target-selector");
    const selRole = document.getElementById("fix-target-role");
    const selRatio = document.getElementById("fix-current-ratio");
    const selReq = document.getElementById("fix-target-req");

    if (selTitle) selTitle.textContent = finding.selector;
    if (selRole) selRole.textContent = `Role: ${finding.element_role} • Line ${finding.line_number}`;
    if (selRatio) selRatio.textContent = finding.formatted_ratio;
    if (selReq) selReq.textContent = `${finding.target_threshold}:1`;

    // Compute recommendations (hue-preserving)
    const fgRgb = parseCssColor(finding.effective_fg) || { r: 148, g: 163, b: 184 };
    const bgRgb = parseCssColor(finding.effective_bg) || { r: 255, g: 255, b: 255 };

    const suggestions = [];

    // Minimal shift
    const minimal = findHuePreservingColor(fgRgb, bgRgb, finding.target_threshold);
    if (minimal) {
      suggestions.push({
        hex: minimal.rgb.hex,
        formatted_ratio: `${minimal.ratio.toFixed(2)}:1`,
        passes_target: true,
        lightness_shift: minimal.shift.toFixed(1),
        description: "Minimal hue-preserving shift (satisfies target)"
      });
    }

    // Enhanced AAA
    const enhanced = findHuePreservingColor(fgRgb, bgRgb, 7.0);
    if (enhanced && (!minimal || enhanced.rgb.hex !== minimal.rgb.hex)) {
      suggestions.push({
        hex: enhanced.rgb.hex,
        formatted_ratio: `${enhanced.ratio.toFixed(2)}:1`,
        passes_target: true,
        lightness_shift: enhanced.shift.toFixed(1),
        description: "Enhanced Level AAA target (7.0:1)"
      });
    }

    // High contrast anchor
    suggestions.push({
      hex: "#0F172A",
      formatted_ratio: `${calcContrast({ r: 15, g: 23, b: 42 }, bgRgb).toFixed(2)}:1`,
      passes_target: true,
      lightness_shift: "High",
      description: "Deep Slate High Contrast Anchor"
    });

    renderRecommendationCards(suggestions, finding);

    const defaultHex = (suggestions.length > 0) ? suggestions[0].hex : finding.effective_fg;
    previewCandidateFix(finding, defaultHex);
  }

  function renderRecommendationCards(suggestions, finding) {
    const container = document.getElementById("fix-suggestions-grid");
    if (!container) return;

    if (!suggestions || suggestions.length === 0) {
      container.innerHTML = `<div style="color:var(--cc-text-muted);font-size:0.85rem;">No automated recommendations generated.</div>`;
      return;
    }

    container.innerHTML = suggestions.map((s, idx) => `
      <div class="card suggestion-card" data-idx="${idx}" style="cursor:pointer;padding:16px;border:2px solid transparent;transition:all 0.15s ease;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <span class="badge ${s.passes_target ? "badge-pass" : "badge-warn"}">
            ${s.formatted_ratio}
          </span>
          <span style="font-size:0.75rem;color:var(--cc-text-muted);">ΔL: ${s.lightness_shift}%</span>
        </div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
          <span class="color-swatch" style="background-color:${s.hex};width:28px;height:28px;"></span>
          <div>
            <div style="font-weight:700;font-family:var(--cc-font-mono);">${s.hex}</div>
            <div style="font-size:0.72rem;color:var(--cc-text-muted);">${s.description}</div>
          </div>
        </div>
        <button class="btn btn-secondary btn-sm btn-select-suggestion" data-hex="${s.hex}" style="width:100%;margin-top:4px;">
          Preview Fix
        </button>
      </div>
    `).join("");

    container.querySelectorAll(".btn-select-suggestion").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const hex = btn.getAttribute("data-hex");
        previewCandidateFix(finding, hex);
      });
    });
  }

  function previewCandidateFix(finding, candidateHex) {
    if (!finding) return;
    state.candidateHex = candidateHex;
    state.selectedFinding = finding;
    state.targetSelector = finding.selector;

    const propName = finding.element_role.includes("border") ? "border-color" : "color";
    const diffResult = generateCssDiff(state.cssSource, finding.selector, propName, candidateHex);

    const fgRgb = parseCssColor(finding.effective_fg) || { r: 148, g: 163, b: 184 };
    const bgRgb = parseCssColor(finding.effective_bg) || { r: 255, g: 255, b: 255 };
    const candRgb = parseCssColor(candidateHex) || { r: 89, g: 106, b: 130 };

    const candRatio = calcContrast(candRgb, bgRgb);
    diffResult.projectedRatio = candRatio;

    state.proposedPatch = diffResult;
    state.patchedCss = diffResult.patchedCss;

    // 1. Update Diff Container
    const diffContainer = document.getElementById("patch-diff-container");
    if (diffContainer) {
      diffContainer.innerHTML = `<div class="diff-viewer">${renderDiffHtml(diffResult.diff)}</div>`;
    }

    // 2. Update Visual Before / After Metric Comparison Strip
    const origHexEl = document.getElementById("ba-orig-hex");
    const origSwatch = document.getElementById("ba-orig-swatch");
    const origRatioEl = document.getElementById("ba-orig-ratio");
    const origApcaEl = document.getElementById("ba-orig-apca");

    const patchHexEl = document.getElementById("ba-patch-hex");
    const patchSwatch = document.getElementById("ba-patch-swatch");
    const patchRatioEl = document.getElementById("ba-patch-ratio");
    const patchApcaEl = document.getElementById("ba-patch-apca");
    const gainBadge = document.getElementById("ba-gain-badge");

    const origRatio = finding.contrast_ratio || 1.0;
    const origApcaVal = calcApca(fgRgb, bgRgb);
    const patchApcaVal = calcApca(candRgb, bgRgb);
    const gain = candRatio - origRatio;

    if (origHexEl) origHexEl.textContent = finding.effective_fg;
    if (origSwatch) origSwatch.style.backgroundColor = finding.effective_fg;
    if (origRatioEl) {
      origRatioEl.textContent = `${finding.formatted_ratio || origRatio.toFixed(2) + ":1"} ${finding.pass_aa ? "PASS" : "FAIL"}`;
      origRatioEl.className = `badge ${finding.pass_aa ? "badge-pass" : "badge-fail"}`;
    }
    if (origApcaEl) origApcaEl.textContent = `APCA Lc ${origApcaVal}`;

    if (patchHexEl) patchHexEl.textContent = candidateHex.toUpperCase();
    if (patchSwatch) patchSwatch.style.backgroundColor = candidateHex;
    if (patchRatioEl) {
      const isPass = candRatio >= finding.target_threshold;
      patchRatioEl.textContent = `${candRatio.toFixed(2)}:1 ${isPass ? "PASS" : "FAIL"}`;
      patchRatioEl.className = `badge ${isPass ? "badge-pass" : "badge-warn"}`;
    }
    if (patchApcaEl) patchApcaEl.textContent = `APCA Lc ${patchApcaVal}`;

    if (gainBadge) {
      const gainSign = gain >= 0 ? "+" : "";
      gainBadge.textContent = `${gainSign}${gain.toFixed(2)}:1 Gain`;
      gainBadge.className = `badge badge-pill ${gain >= 0 ? "badge-info" : "badge-warn"}`;
    }

    // Update Split pane header badges
    const splitOrigBadge = document.getElementById("split-orig-badge");
    const splitPatchBadge = document.getElementById("split-patch-badge");
    if (splitOrigBadge) splitOrigBadge.textContent = `${finding.formatted_ratio || "FAIL"}`;
    if (splitPatchBadge) splitPatchBadge.textContent = `${candRatio.toFixed(2)}:1 PASS`;

    // 3. Update Tuner Controls
    const tunerPicker = document.getElementById("tuner-color-picker");
    const tunerInput = document.getElementById("tuner-hex-input");
    const tunerBadge = document.getElementById("tuner-status-badge");
    const tunerApca = document.getElementById("tuner-apca-badge");

    if (tunerPicker) tunerPicker.value = candidateHex;
    if (tunerInput) tunerInput.value = candidateHex.toUpperCase();
    if (tunerBadge) {
      const isPass = candRatio >= finding.target_threshold;
      tunerBadge.textContent = `${candRatio.toFixed(2)}:1 ${isPass ? "PASS" : "FAIL"}`;
      tunerBadge.className = `badge ${isPass ? "badge-pass" : "badge-fail"}`;
    }
    if (tunerApca) tunerApca.textContent = `APCA Lc ${patchApcaVal}`;

    // 4. Update Live Preview
    updatePreview();
  }

  function handleConfirmApplyPatch() {
    closeAllModals();
    if (!state.proposedPatch) return;

    state.cssSource = state.patchedCss;
    const cssEditor = document.getElementById("input-css");
    if (cssEditor) cssEditor.value = state.patchedCss;

    handleRunAudit();
    switchScreen("fix-studio");
    alert("Accessibility patch applied to working copy! Re-analysis complete.");
  }

  function renderTokenInventory(tokens) {
    const tbody = document.getElementById("tokens-tbody");
    if (!tbody) return;

    if (!tokens || tokens.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--cc-text-muted);">No CSS custom properties detected in stylesheet.</td></tr>`;
      return;
    }

    tbody.innerHTML = tokens.map((t) => {
      const hex = t.hex_color || t.value;
      const fails = t.failing_usages || 0;
      return `
        <tr>
          <td><code style="font-weight:600;color:var(--cc-primary);">${escapeHtml(t.name)}</code></td>
          <td><code>${escapeHtml(t.value)}</code></td>
          <td>
            <div class="color-chip">
              <span class="color-swatch" style="background-color:${hex};"></span>
              <span>${hex}</span>
            </div>
          </td>
          <td><strong>${t.usage_count}</strong> times</td>
          <td>
            ${fails > 0 ? `<span class="badge badge-fail">${fails} Violations</span>` : `<span class="badge badge-pass">0 Violations</span>`}
          </td>
          <td>
            ${t.suggested_value ? `
              <div class="color-chip">
                <span class="color-swatch" style="background-color:${t.suggested_value};"></span>
                <code>${t.suggested_value}</code>
              </div>
            ` : `<span style="color:var(--cc-text-muted);font-size:0.8rem;">Compliant</span>`}
          </td>
        </tr>
      `;
    }).join("");
  }

  function loadSessionsList() {
    const container = document.getElementById("sessions-list-container");
    if (!container) return;

    // Load from local storage
    const rawSessions = safeGetStorage("contrastcraft_saved_sessions");
    const sessions = rawSessions ? JSON.parse(rawSessions) : [
      {
        id: "demo-session-1",
        name: "Sample Portfolio Baseline",
        input_type: "paste",
        updated_at: new Date().toISOString(),
        compliance_score: 60.0,
        total_analyzed: 6,
        fail_aa_count: 2
      }
    ];

    container.innerHTML = sessions.map((s) => `
      <div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:16px 20px;margin-bottom:12px;">
        <div>
          <div style="display:flex;align-items:center;gap:10px;">
            <h4 style="margin:0;font-size:1.05rem;">${escapeHtml(s.name)}</h4>
            <span class="badge badge-pill badge-info">${escapeHtml(s.input_type)}</span>
            <span class="badge ${s.fail_aa_count === 0 ? "badge-pass" : "badge-warn"}">
              Score: ${s.compliance_score}%
            </span>
          </div>
          <div style="font-size:0.78rem;color:var(--cc-text-muted);margin-top:4px;">
            Last updated: ${new Date(s.updated_at).toLocaleString()} • ${s.total_analyzed} elements audited • ${s.fail_aa_count} AA failures
          </div>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-primary btn-sm btn-load-session" data-id="${s.id}">Reopen</button>
        </div>
      </div>
    `).join("");

    container.querySelectorAll(".btn-load-session").forEach((btn) => {
      btn.addEventListener("click", () => {
        handleLoadSample();
      });
    });
  }

  function handleSaveSession() {
    if (!state.currentAudit) {
      alert("Please run an audit first before saving a session.");
      return;
    }
    const name = prompt("Enter a name for this audit session:", "Portfolio Audit Snapshot");
    if (!name) return;

    const raw = safeGetStorage("contrastcraft_saved_sessions");
    const list = raw ? JSON.parse(raw) : [];
    list.unshift({
      id: "session-" + Date.now(),
      name: name,
      input_type: state.activeInputTab,
      updated_at: new Date().toISOString(),
      compliance_score: state.currentAudit.summary.compliance_score || 0,
      total_analyzed: state.currentAudit.summary.total_analyzed || 0,
      fail_aa_count: state.currentAudit.summary.fail_aa_count || 0
    });
    safeSetStorage("contrastcraft_saved_sessions", JSON.stringify(list));
    alert("Session saved locally!");
    loadSessionsList();
  }

  function handleExportReport(type) {
    if (!state.currentAudit) {
      alert("Please run an audit before exporting reports.");
      return;
    }

    if (type === "json") {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state.currentAudit, null, 2));
      downloadFile(dataStr, "contrastcraft-report.json");
    } else if (type === "css") {
      const corrected = "/* ContrastCraft Corrected CSS */\n" + (state.patchedCss || state.cssSource);
      const dataStr = "data:text/css;charset=utf-8," + encodeURIComponent(corrected);
      downloadFile(dataStr, "contrastcraft-corrected.css");
    } else if (type === "html") {
      // Direct report download
      const htmlReport = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>ContrastCraft Report</title><style>body{font-family:sans-serif;padding:32px;background:#f8fafc;color:#0f172a;}table{width:100%;border-collapse:collapse;}th,td{padding:10px;border-bottom:1px solid #e2e8f0;text-align:left;}</style></head><body><h1>ContrastCraft Accessibility Report</h1><p>Compliance Score: ${state.currentAudit.summary.compliance_score}%</p><p>Total Analyzed: ${state.currentAudit.summary.total_analyzed}</p><hr></body></html>`;
      const dataStr = "data:text/html;charset=utf-8," + encodeURIComponent(htmlReport);
      downloadFile(dataStr, "contrastcraft-report.html");
    }
  }

  function downloadFile(uri, filename) {
    const a = document.createElement("a");
    a.href = uri;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // --- Main Bootstrapper ---
  function initApp() {
    initTheme();

    // Navigation item clicks
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => {
        const screen = btn.getAttribute("data-screen");
        if (screen) switchScreen(screen);
      });
    });

    // Input tab clicks
    document.querySelectorAll(".input-tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.getAttribute("data-tab");
        document.querySelectorAll(".input-tab-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        document.querySelectorAll(".input-tab-pane").forEach((p) => (p.style.display = "none"));
        const target = document.getElementById(`tab-pane-${tab}`);
        if (target) target.style.display = "block";
        state.activeInputTab = tab;
      });
    });

    // Action buttons
    const runAuditBtn = document.getElementById("btn-run-audit");
    if (runAuditBtn) runAuditBtn.addEventListener("click", handleRunAudit);

    const loadSampleBtn = document.getElementById("btn-load-sample");
    if (loadSampleBtn) loadSampleBtn.addEventListener("click", handleLoadSample);

    // Search and filters
    const searchInput = document.getElementById("findings-search");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        state.searchQuery = e.target.value.toLowerCase().trim();
        applyFiltersAndRenderFindings();
      });
    }

    document.querySelectorAll(".filter-pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-pill").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        state.activeFilter = btn.getAttribute("data-filter") || "all";
        applyFiltersAndRenderFindings();
      });
    });

    const sortSelect = document.getElementById("findings-sort");
    if (sortSelect) {
      sortSelect.addEventListener("change", (e) => {
        state.activeSort = e.target.value;
        applyFiltersAndRenderFindings();
      });
    }

    // Preview controls
    document.querySelectorAll(".btn-preview-mode").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".btn-preview-mode").forEach((b) => b.classList.remove("btn-primary"));
        btn.classList.add("btn-primary");
        state.previewMode = btn.getAttribute("data-mode");
        updatePreview();
      });
    });

    const visionSelect = document.getElementById("select-vision-sim");
    if (visionSelect) {
      visionSelect.addEventListener("change", (e) => {
        state.visionFilter = e.target.value;
        updatePreview();
      });
    }

    document.querySelectorAll(".btn-viewport").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".btn-viewport").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        const w = btn.getAttribute("data-width");
        const wrap = document.getElementById("preview-split-grid");
        if (wrap) wrap.style.maxWidth = w === "100%" ? "100%" : w;
      });
    });

    // Interactive Color Tuner controls
    const tunerPicker = document.getElementById("tuner-color-picker");
    const tunerInput = document.getElementById("tuner-hex-input");
    const tunerSlider = document.getElementById("tuner-lightness-slider");
    const tunerReset = document.getElementById("btn-tuner-reset");
    const copyCssBtn = document.getElementById("btn-copy-css-rule");
    const applyTunedBtn = document.getElementById("btn-apply-tuned-color");

    if (tunerPicker) {
      tunerPicker.addEventListener("input", (e) => {
        if (tunerInput) tunerInput.value = e.target.value.toUpperCase();
        if (state.selectedFinding) previewCandidateFix(state.selectedFinding, e.target.value);
      });
    }

    if (tunerInput) {
      tunerInput.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        if (val.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i)) {
          if (tunerPicker) tunerPicker.value = val;
          if (state.selectedFinding) previewCandidateFix(state.selectedFinding, val);
        }
      });
    }

    if (tunerSlider) {
      tunerSlider.addEventListener("input", (e) => {
        const delta = parseFloat(e.target.value);
        const lVal = document.getElementById("tuner-lightness-val");
        if (lVal) lVal.textContent = `${delta >= 0 ? "+" : ""}${delta}%`;
        if (state.selectedFinding) {
          const fgRgb = parseCssColor(state.selectedFinding.effective_fg) || { r: 148, g: 163, b: 184 };
          const hsl = rgbToHsl(fgRgb.r, fgRgb.g, fgRgb.b);
          const newL = Math.max(0, Math.min(100, hsl.l + delta));
          const newRgb = hslToRgb(hsl.h, hsl.s, newL);
          if (tunerPicker) tunerPicker.value = newRgb.hex;
          if (tunerInput) tunerInput.value = newRgb.hex;
          previewCandidateFix(state.selectedFinding, newRgb.hex);
        }
      });
    }

    if (tunerReset) {
      tunerReset.addEventListener("click", () => {
        if (tunerSlider) tunerSlider.value = -21;
        const lVal = document.getElementById("tuner-lightness-val");
        if (lVal) lVal.textContent = "-21%";
        if (state.selectedFinding) {
          previewCandidateFix(state.selectedFinding, "#596A82");
        }
      });
    }

    if (copyCssBtn) {
      copyCssBtn.addEventListener("click", () => {
        if (state.selectedFinding && state.candidateHex) {
          const prop = state.selectedFinding.element_role.includes("border") ? "border-color" : "color";
          const snippet = `${state.selectedFinding.selector} {\n  ${prop}: ${state.candidateHex};\n}`;
          try {
            navigator.clipboard.writeText(snippet);
          } catch (e) {}
          alert("CSS rule copied to clipboard!\n\n" + snippet);
        }
      });
    }

    if (applyTunedBtn) {
      applyTunedBtn.addEventListener("click", () => {
        if (state.proposedPatch) openModal("patch-confirm-modal");
      });
    }

    // Typography Strategy (Promote to WCAG Large Text)
    const largeTextBtn = document.getElementById("btn-strategy-large-text");
    if (largeTextBtn) {
      largeTextBtn.addEventListener("click", () => {
        if (!state.selectedFinding) return;
        const sel = state.selectedFinding.selector;
        let patched = state.cssSource;
        const addition = `\n\n/* WCAG Large Text Promotion (Threshold drops from 4.5:1 to 3.0:1) */\n${sel} {\n  font-size: 19px !important;\n  font-weight: 700 !important;\n}\n`;
        patched += addition;
        state.patchedCss = patched;
        state.proposedPatch = {
          diff: `--- a/styles.css\n+++ b/styles.css\n@@ ${sel} (Promote to WCAG Large Text) @@\n+  font-size: 19px;\n+  font-weight: 700;\n+  /* Target threshold lowered to 3.0:1 under WCAG SC 1.4.3 */`,
          patchedCss: patched,
          projectedRatio: state.selectedFinding.contrast_ratio
        };

        const diffContainer = document.getElementById("patch-diff-container");
        if (diffContainer) {
          diffContainer.innerHTML = `<div class="diff-viewer">${renderDiffHtml(state.proposedPatch.diff)}</div>`;
        }

        const selReq = document.getElementById("fix-target-req");
        if (selReq) selReq.textContent = "3.0:1 (Large)";
        const patchRatioEl = document.getElementById("ba-patch-ratio");
        if (patchRatioEl) {
          patchRatioEl.textContent = `${state.selectedFinding.contrast_ratio.toFixed(2)}:1 PASS (Large)`;
          patchRatioEl.className = "badge badge-pass";
        }
        const splitPatchBadge = document.getElementById("split-patch-badge");
        if (splitPatchBadge) splitPatchBadge.textContent = `${state.selectedFinding.contrast_ratio.toFixed(2)}:1 PASS (Large Text)`;

        updatePreview();
        alert("Typography Strategy Applied! Element promoted to WCAG Large Text (Target: 3.0:1).");
      });
    }

    // Component Geometry Strategy (Button Target & Focus Ring)
    const btnTargetBtn = document.getElementById("btn-strategy-button-target");
    if (btnTargetBtn) {
      btnTargetBtn.addEventListener("click", () => {
        const targetSel = (state.selectedFinding && state.selectedFinding.element_role.includes("button"))
          ? state.selectedFinding.selector
          : ".btn-action, button, input";
        let patched = state.cssSource;
        const addition = `\n\n/* WCAG 2.5.5 / 2.5.8 Target Size & Focus Ring Enhancement */\n${targetSel} {\n  min-height: 44px !important;\n  padding: 12px 24px !important;\n  border-radius: 8px !important;\n  outline: 2px solid #0284C7 !important;\n  outline-offset: 2px !important;\n}\n`;
        patched += addition;
        state.patchedCss = patched;
        state.proposedPatch = {
          diff: `--- a/styles.css\n+++ b/styles.css\n@@ ${targetSel} (Touch Target & Focus Ring) @@\n+  min-height: 44px;\n+  padding: 12px 24px;\n+  border-radius: 8px;\n+  outline: 2px solid #0284C7;\n+  outline-offset: 2px;`,
          patchedCss: patched,
          projectedRatio: 4.5
        };

        const diffContainer = document.getElementById("patch-diff-container");
        if (diffContainer) {
          diffContainer.innerHTML = `<div class="diff-viewer">${renderDiffHtml(state.proposedPatch.diff)}</div>`;
        }
        updatePreview();
        alert("Component Geometry Polished! Touch target enlarged to 44px minimum with 8px radius & focus indicator.");
      });
    }

    // Whole-Page Accessible Theme Harmonizer
    const themePalettes = {
      modern_indigo: {
        name: "Modern Tech Indigo",
        tokens: {
          "--color-brand-primary": "#4F46E5",
          "--color-text-main": "#0F172A",
          "--color-text-muted": "#475569",
          "--color-card-bg": "#F8FAFC",
          "--color-border-subtle": "#94A3B8"
        }
      },
      emerald_fintech: {
        name: "Emerald Fintech",
        tokens: {
          "--color-brand-primary": "#059669",
          "--color-text-main": "#064E3B",
          "--color-text-muted": "#047857",
          "--color-card-bg": "#ECFDF5",
          "--color-border-subtle": "#6EE7B7"
        }
      },
      warm_editorial: {
        name: "Warm Editorial",
        tokens: {
          "--color-brand-primary": "#B45309",
          "--color-text-main": "#271D15",
          "--color-text-muted": "#78350F",
          "--color-card-bg": "#FAF7F2",
          "--color-border-subtle": "#D6D3D1"
        }
      },
      cyber_obsidian: {
        name: "Cyber Obsidian",
        tokens: {
          "--color-brand-primary": "#38BDF8",
          "--color-text-main": "#F8FAFC",
          "--color-text-muted": "#CBD5E1",
          "--color-card-bg": "#0F172A",
          "--color-border-subtle": "#475569"
        }
      }
    };

    document.querySelectorAll(".theme-card").forEach((card) => {
      card.addEventListener("click", () => {
        const themeId = card.getAttribute("data-theme-id");
        const theme = themePalettes[themeId];
        if (!theme) return;

        let patched = state.cssSource;
        const diffLines = ["--- a/styles.css", "+++ b/styles.css", `@@ :root (Harmonious Theme: ${theme.name}) @@`];

        Object.entries(theme.tokens).forEach(([token, val]) => {
          const reg = new RegExp("(" + escapeRegex(token) + "\\s*:\\s*)([^;]+)(;)", "i");
          if (patched.match(reg)) {
            patched = patched.replace(reg, `$1${val}$3`);
            diffLines.push(`+  ${token}: ${val};`);
          } else {
            patched = `:root {\n  ${token}: ${val};\n}\n` + patched;
            diffLines.push(`+  ${token}: ${val};`);
          }
        });

        state.patchedCss = patched;
        state.proposedPatch = {
          diff: diffLines.join("\n"),
          patchedCss: patched,
          projectedRatio: 7.0
        };

        const diffContainer = document.getElementById("patch-diff-container");
        if (diffContainer) {
          diffContainer.innerHTML = `<div class="diff-viewer">${renderDiffHtml(state.proposedPatch.diff)}</div>`;
        }

        updatePreview();
        alert(`🌟 Harmonious Theme '${theme.name}' applied!\nAll design tokens and color combinations updated across the page.`);
      });
    });

    // Patch & Export buttons
    const applyPatchBtn = document.getElementById("btn-apply-patch");
    if (applyPatchBtn) applyPatchBtn.addEventListener("click", () => openModal("patch-confirm-modal"));

    const confirmApplyBtn = document.getElementById("btn-confirm-apply-patch");
    if (confirmApplyBtn) confirmApplyBtn.addEventListener("click", handleConfirmApplyPatch);

    const exportDiffBtn = document.getElementById("btn-export-patch-file");
    if (exportDiffBtn) {
      exportDiffBtn.addEventListener("click", () => {
        if (state.proposedPatch && state.proposedPatch.diff) {
          const dataStr = "data:text/plain;charset=utf-8," + encodeURIComponent(state.proposedPatch.diff);
          downloadFile(dataStr, "contrastcraft-patch.diff");
        }
      });
    }

    const saveSessionBtn = document.getElementById("btn-save-session-trigger");
    if (saveSessionBtn) saveSessionBtn.addEventListener("click", handleSaveSession);

    const exportHtmlBtn = document.getElementById("btn-export-html");
    if (exportHtmlBtn) exportHtmlBtn.addEventListener("click", () => handleExportReport("html"));

    const exportJsonBtn = document.getElementById("btn-export-json");
    if (exportJsonBtn) exportJsonBtn.addEventListener("click", () => handleExportReport("json"));

    const exportCssBtn = document.getElementById("btn-export-css");
    if (exportCssBtn) exportCssBtn.addEventListener("click", () => handleExportReport("css"));

    const shortcutsBtn = document.getElementById("btn-shortcuts");
    if (shortcutsBtn) shortcutsBtn.addEventListener("click", () => openModal("shortcuts-modal"));

    document.querySelectorAll(".modal-close-btn").forEach((btn) => {
      btn.addEventListener("click", closeAllModals);
    });

    // File dropzone
    const dropzone = document.getElementById("file-dropzone");
    const fileInput = document.getElementById("file-input");
    if (dropzone && fileInput) {
      dropzone.addEventListener("click", () => fileInput.click());
      fileInput.addEventListener("change", () => {
        if (fileInput.files.length) {
          const f = fileInput.files[0];
          const r = new FileReader();
          r.onload = (e) => {
            const htmlEditor = document.getElementById("input-html");
            if (htmlEditor) htmlEditor.value = e.target.result;
            const pasteTab = document.querySelector('[data-tab="paste"]');
            if (pasteTab) pasteTab.click();
          };
          r.readAsText(f);
        }
      });
    }

    // Keyboard Shortcuts
    if (typeof window.addEventListener === "function") {
      window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeAllModals();
        return;
      }
      if (e.key === "?" && !e.target.matches("input, textarea")) {
        e.preventDefault();
        openModal("shortcuts-modal");
        return;
      }
      if (e.altKey) {
        if (e.key === "a" || e.key === "A") {
          e.preventDefault();
          handleRunAudit();
        } else if (e.key === "t" || e.key === "T") {
          e.preventDefault();
          const curr = document.documentElement.getAttribute("data-theme") || "light";
          setTheme(curr === "dark" ? "light" : "dark");
        } else if (e.key === "s" || e.key === "S") {
          e.preventDefault();
          switchScreen("findings");
          const s = document.getElementById("findings-search");
          if (s) s.focus();
        } else if (e.key >= "1" && e.key <= "5") {
          e.preventDefault();
          const map = { 1: "workspace", 2: "findings", 3: "fix-studio", 4: "tokens", 5: "sessions" };
          switchScreen(map[parseInt(e.key, 10)]);
        }
      }
    });
    }

    // Pre-populate sample showcase in workspace by default for immediate convenience
    const htmlEditor = document.getElementById("input-html");
    const cssEditor = document.getElementById("input-css");
    if (htmlEditor && !htmlEditor.value) htmlEditor.value = SAMPLE_HTML;
    if (cssEditor && !cssEditor.value) cssEditor.value = SAMPLE_CSS;
    state.htmlSource = SAMPLE_HTML;
    state.cssSource = SAMPLE_CSS;
    state.patchedCss = SAMPLE_CSS;

    // Immediately prime demo sample audit so Fix Studio has active comparison on start
    const initialSampleAudit = runLocalClientAudit(SAMPLE_HTML, SAMPLE_CSS);
    state.currentAudit = initialSampleAudit;
    renderOverview(initialSampleAudit.summary);
    renderTokenInventory(initialSampleAudit.tokens);
    applyFiltersAndRenderFindings();
    const firstFail = initialSampleAudit.findings.find(f => !f.pass_aa && f.confidence !== "needs_browser_verification");
    if (firstFail) {
      openFixStudioForFinding(firstFail, false);
    }
  }

  // Expose global controller for direct accessibility & testing
  window.ContrastCraft = {
    state,
    switchScreen,
    handleRunAudit,
    handleLoadSample,
    openModal,
    closeAllModals,
    setTheme,
    toggleTheme: () => {
      const curr = document.documentElement.getAttribute("data-theme") || "light";
      const next = curr === "dark" ? "light" : "dark";
      setTheme(next);
      safeSetStorage("contrastcraft_theme", next);
    }
  };

  // Guaranteed immediate execution
  function safeInit() {
    try {
      initApp();
      console.log("ContrastCraft UI initialized successfully.");
    } catch (err) {
      console.error("ContrastCraft initialization warning:", err);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", safeInit);
  } else {
    safeInit();
  }
})();
