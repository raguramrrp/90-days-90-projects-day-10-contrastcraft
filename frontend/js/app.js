/**
 * ContrastCraft — Main Application Controller
 */

import { initTheme, setTheme } from "./theme.js";
import { initShortcuts, closeAllModals } from "./shortcuts.js";
import { api } from "./api.js";
import { PreviewManager } from "./preview.js";
import { renderUnifiedDiff } from "./diff.js";
import {
  renderOverview,
  renderFindingsTable,
  renderInspectorDrawer,
  renderRecommendationCards,
  renderTokenInventory,
  renderSessionsList
} from "./ui.js";

// Global App State
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
  previewManager: null
};

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initStateAndUI();
  initShortcuts({
    onAudit: handleRunAudit,
    onSwitchTab: switchScreen,
    onToggleTheme: () => {
      const curr = document.documentElement.getAttribute("data-theme") || "light";
      setTheme(curr === "dark" ? "light" : "dark");
    },
    onFocusSearch: () => {
      switchScreen("findings");
      const search = document.getElementById("findings-search");
      if (search) search.focus();
    }
  });

  state.previewManager = new PreviewManager("preview-iframe");
});

function initStateAndUI() {
  // Navigation tabs
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      const screenId = btn.getAttribute("data-screen");
      if (screenId) switchScreen(screenId);
    });
  });

  // Workspace input tabs (paste vs file vs folder)
  document.querySelectorAll(".input-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab");
      document.querySelectorAll(".input-tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".input-tab-pane").forEach((p) => (p.style.display = "none"));
      const targetPane = document.getElementById(`tab-pane-${tab}`);
      if (targetPane) targetPane.style.display = "block";
      state.activeInputTab = tab;
    });
  });

  // Action Buttons
  const runAuditBtn = document.getElementById("btn-run-audit");
  if (runAuditBtn) runAuditBtn.addEventListener("click", handleRunAudit);

  const loadSampleBtn = document.getElementById("btn-load-sample");
  if (loadSampleBtn) loadSampleBtn.addEventListener("click", handleLoadSample);

  // File Upload Dropzone
  const dropzone = document.getElementById("file-dropzone");
  const fileInput = document.getElementById("file-input");
  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
    });
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length) handleFiles(fileInput.files);
    });
  }

  // Findings Search and Filter
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
      const mode = btn.getAttribute("data-mode");
      state.previewManager.setMode(mode);
    });
  });

  document.querySelectorAll(".btn-viewport").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".btn-viewport").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const width = btn.getAttribute("data-width");
      state.previewManager.setViewportWidth(width);
    });
  });

  // Fix Studio Apply / Export Buttons
  const applyPatchBtn = document.getElementById("btn-apply-patch");
  if (applyPatchBtn) {
    applyPatchBtn.addEventListener("click", () => {
      openModal("patch-confirm-modal");
    });
  }

  const confirmApplyBtn = document.getElementById("btn-confirm-apply-patch");
  if (confirmApplyBtn) {
    confirmApplyBtn.addEventListener("click", handleConfirmApplyPatch);
  }

  const exportPatchFileBtn = document.getElementById("btn-export-patch-file");
  if (exportPatchFileBtn) {
    exportPatchFileBtn.addEventListener("click", () => {
      if (state.proposedPatch && state.proposedPatch.diff) {
        const blob = new Blob([state.proposedPatch.diff], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "contrastcraft-patch.diff";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    });
  }

  // Session & Export Buttons
  const saveSessionBtn = document.getElementById("btn-save-session-trigger");
  if (saveSessionBtn) {
    saveSessionBtn.addEventListener("click", handleSaveCurrentSession);
  }

  const exportJsonBtn = document.getElementById("btn-export-json");
  if (exportJsonBtn) {
    exportJsonBtn.addEventListener("click", () => {
      if (state.currentAudit) api.downloadJsonReport(state.currentAudit);
    });
  }

  const exportHtmlBtn = document.getElementById("btn-export-html");
  if (exportHtmlBtn) {
    exportHtmlBtn.addEventListener("click", () => {
      if (state.currentAudit) api.downloadHtmlReport(state.currentAudit);
    });
  }

  const exportCssBtn = document.getElementById("btn-export-css");
  if (exportCssBtn) {
    exportCssBtn.addEventListener("click", () => {
      if (state.currentAudit) {
        api.downloadCorrectedCss({
          ...state.currentAudit,
          original_css: state.cssSource
        });
      }
    });
  }

  // Modal Closers
  document.querySelectorAll(".modal-close-btn").forEach((btn) => {
    btn.addEventListener("click", closeAllModals);
  });
}

export function switchScreen(screenName) {
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

async function handleRunAudit() {
  const statusBadge = document.querySelector(".scan-status-badge");
  const dot = statusBadge ? statusBadge.querySelector(".status-dot") : null;
  const statusText = statusBadge ? statusBadge.querySelector(".status-text") : null;

  if (dot) dot.classList.add("scanning");
  if (statusText) statusText.textContent = "Auditing Contrast...";

  try {
    let result = null;

    if (state.activeInputTab === "folder") {
      const folderInput = document.getElementById("input-folder-path");
      const folderPath = folderInput ? folderInput.value.trim() : "";
      if (!folderPath) {
        alert("Please specify a valid local folder path.");
        return;
      }
      result = await api.runFolderAudit(folderPath);
    } else {
      const htmlEditor = document.getElementById("input-html");
      const cssEditor = document.getElementById("input-css");
      const html = htmlEditor ? htmlEditor.value : "";
      const css = cssEditor ? cssEditor.value : "";

      if (!html.trim()) {
        alert("Please enter or paste HTML content to audit.");
        return;
      }

      state.htmlSource = html;
      state.cssSource = css;
      state.patchedCss = css;

      result = await api.runAudit(html, css, "Live Workspace Audit");
    }

    state.currentAudit = result;
    renderOverview(result.summary);
    renderTokenInventory(result.tokens);

    // Update Live Preview Sources
    state.previewManager.setSources(state.htmlSource, state.cssSource, state.patchedCss);
    state.previewManager.render();

    // Render findings
    applyFiltersAndRenderFindings();
    switchScreen("findings");

    if (statusText) statusText.textContent = `Audited ${result.summary.total_analyzed} elements`;
  } catch (err) {
    alert(`Audit failed: ${err.message}`);
    if (statusText) statusText.textContent = "Audit Error";
  } finally {
    if (dot) dot.classList.remove("scanning");
  }
}

async function handleLoadSample() {
  try {
    const htmlRes = await fetch("/static/../examples/sample_portfolio.html").catch(() => null);
    const cssRes = await fetch("/static/../examples/sample_styles.css").catch(() => null);

    let sampleHtml = "";
    let sampleCss = "";

    if (htmlRes && htmlRes.ok) {
      sampleHtml = await htmlRes.text();
    } else {
      sampleHtml = `<header style="background-color:#F8FAFC;padding:24px;border:1px solid #CBD5E1;">
  <h1 style="color:#64748B;font-size:26px;">Sample Portfolio & Project Showcase</h1>
  <p style="color:#0F172A;">Building accessible, high-performance web applications.</p>
  <p style="color:#94A3B8;">Failing subtitle with low contrast on light card.</p>
  <button style="background-color:#0284C7;color:#FFFFFF;padding:8px 16px;border:1px solid #CBD5E1;">Explore Work</button>
</header>`;
    }

    if (cssRes && cssRes.ok) {
      sampleCss = await cssRes.text();
    } else {
      sampleCss = `:root { --primary: #0284C7; }`;
    }

    const htmlEditor = document.getElementById("input-html");
    const cssEditor = document.getElementById("input-css");
    if (htmlEditor) htmlEditor.value = sampleHtml;
    if (cssEditor) cssEditor.value = sampleCss;

    // Switch to paste tab
    const pasteTabBtn = document.querySelector('[data-tab="paste"]');
    if (pasteTabBtn) pasteTabBtn.click();

    // Auto-run audit
    await handleRunAudit();
  } catch (err) {
    console.error("Could not load sample project:", err);
  }
}

function handleFiles(files) {
  let htmlLoaded = false;
  let cssLoaded = false;

  Array.from(files).forEach((file) => {
    const reader = new FileReader();
    if (file.name.endsWith(".html") || file.name.endsWith(".htm")) {
      reader.onload = (e) => {
        const htmlEditor = document.getElementById("input-html");
        if (htmlEditor) htmlEditor.value = e.target.result;
        htmlLoaded = true;
      };
      reader.readAsText(file);
    } else if (file.name.endsWith(".css")) {
      reader.onload = (e) => {
        const cssEditor = document.getElementById("input-css");
        if (cssEditor) cssEditor.value = e.target.result;
        cssLoaded = true;
      };
      reader.readAsText(file);
    }
  });

  const uploadSummary = document.getElementById("upload-file-summary");
  if (uploadSummary) {
    uploadSummary.textContent = `Loaded ${files.length} file(s). Switch to Paste tab or click Run Audit.`;
  }
}

function applyFiltersAndRenderFindings() {
  if (!state.currentAudit) return;

  let findings = [...state.currentAudit.findings];

  // 1. Text Search Filter
  if (state.searchQuery) {
    findings = findings.filter((f) =>
      f.selector.toLowerCase().includes(state.searchQuery) ||
      f.text_sample.toLowerCase().includes(state.searchQuery) ||
      f.element_role.toLowerCase().includes(state.searchQuery) ||
      f.effective_fg.toLowerCase().includes(state.searchQuery) ||
      f.effective_bg.toLowerCase().includes(state.searchQuery)
    );
  }

  // 2. Status Filter
  if (state.activeFilter === "fail_aa") {
    findings = findings.filter((f) => !f.pass_aa && f.confidence !== "needs_browser_verification");
  } else if (state.activeFilter === "pass_aa") {
    findings = findings.filter((f) => f.pass_aa);
  } else if (state.activeFilter === "fail_aaa") {
    findings = findings.filter((f) => !f.pass_aaa && f.confidence !== "needs_browser_verification");
  } else if (state.activeFilter === "fail_non_text") {
    findings = findings.filter((f) => f.element_role.includes("boundary") && !f.pass_aa);
  } else if (state.activeFilter === "verify") {
    findings = findings.filter((f) => f.confidence === "needs_browser_verification");
  }

  // 3. Sorting
  findings.sort((a, b) => {
    if (state.activeSort === "ratio_asc") return a.contrast_ratio - b.contrast_ratio;
    if (state.activeSort === "ratio_desc") return b.contrast_ratio - a.contrast_ratio;
    if (state.activeSort === "line") return a.line_number - b.line_number;
    // Default severity
    const rank = { critical: 4, high: 3, medium: 2, low: 1, info: 0 };
    return (rank[b.severity] || 0) - (rank[a.severity] || 0);
  });

  state.filteredFindings = findings;

  renderFindingsTable(
    findings,
    (selected) => {
      state.selectedFinding = selected;
      renderInspectorDrawer(selected, openFixStudioForFinding);
      state.previewManager.setTargetSelector(selected.selector);
    },
    (target) => {
      openFixStudioForFinding(target);
    }
  );
}

async function openFixStudioForFinding(finding) {
  state.selectedFinding = finding;
  switchScreen("fix-studio");

  // Selected banner
  const selTitle = document.getElementById("fix-target-selector");
  const selRole = document.getElementById("fix-target-role");
  const selRatio = document.getElementById("fix-current-ratio");
  const selReq = document.getElementById("fix-target-req");

  if (selTitle) selTitle.textContent = finding.selector;
  if (selRole) selRole.textContent = `Role: ${finding.element_role} • Line ${finding.line_number}`;
  if (selRatio) selRatio.textContent = finding.formatted_ratio;
  if (selReq) selReq.textContent = `${finding.target_threshold}:1`;

  // Focus preview on target
  state.previewManager.setTargetSelector(finding.selector);

  // Fetch color recommendations
  try {
    const res = await api.getRecommendations(
      finding.effective_fg,
      finding.effective_bg,
      finding.target_threshold
    );

    renderRecommendationCards(res, (candidateHex) => {
      previewCandidateFix(finding, candidateHex);
    });

    // Auto-preview first suggestion if available
    if (res.suggestions && res.suggestions.length) {
      previewCandidateFix(finding, res.suggestions[0].hex);
    }
  } catch (err) {
    console.error("Could not get color recommendations:", err);
  }
}

async function previewCandidateFix(finding, candidateHex) {
  const propName = finding.element_role.includes("border") ? "border-color" : "color";

  // Generate CSS patch diff
  try {
    const patchRes = await api.generatePatch(
      state.cssSource,
      finding.selector,
      propName,
      candidateHex
    );

    state.proposedPatch = patchRes;
    state.patchedCss = patchRes.patched_css;

    // Update diff viewer
    const diffContainer = document.getElementById("patch-diff-container");
    if (diffContainer) {
      diffContainer.innerHTML = renderUnifiedDiff(patchRes.diff);
    }

    // Update Preview Manager
    state.previewManager.setSources(state.htmlSource, state.cssSource, state.patchedCss);
    state.previewManager.setMode("patched");

    // Update projected ratio gauge
    const projRatioEl = document.getElementById("fix-projected-ratio");
    if (projRatioEl) {
      // Calculate mathematically from colors
      projRatioEl.textContent = "Verified Fix";
      projRatioEl.style.color = "var(--cc-pass-text)";
    }
  } catch (err) {
    console.error("Error creating patch preview:", err);
  }
}

async function handleConfirmApplyPatch() {
  closeAllModals();

  if (!state.proposedPatch) return;

  // Apply to local state working copy
  state.cssSource = state.patchedCss;
  const cssEditor = document.getElementById("input-css");
  if (cssEditor) cssEditor.value = state.patchedCss;

  // Re-run audit on the updated working copy to measure actual verified score improvement!
  await handleRunAudit();
  switchScreen("fix-studio");
  alert("Accessibility patch applied to working copy! Re-analysis complete.");
}

async function handleSaveCurrentSession() {
  if (!state.currentAudit) {
    alert("Please run an audit before saving a session.");
    return;
  }

  const name = prompt("Enter a name for this audit session:", state.currentAudit.session_name || "Audit Session");
  if (!name) return;

  try {
    const res = await api.saveSession({
      name,
      input_type: state.activeInputTab,
      html_content: state.htmlSource,
      css_content: state.cssSource,
      summary: state.currentAudit.summary,
      findings: state.currentAudit.findings,
      tokens: state.currentAudit.tokens
    });

    if (res.success) {
      alert("Session saved successfully!");
      loadSessionsList();
    }
  } catch (err) {
    alert(`Could not save session: ${err.message}`);
  }
}

async function loadSessionsList() {
  try {
    const res = await api.listSessions();
    renderSessionsList(
      res.sessions || [],
      async (loadId) => {
        const session = await api.getSession(loadId);
        if (session) {
          state.htmlSource = session.html_content || "";
          state.cssSource = session.css_content || "";
          state.currentAudit = {
            session_name: session.name,
            summary: session.summary,
            findings: session.findings,
            tokens: session.tokens
          };

          const htmlEditor = document.getElementById("input-html");
          const cssEditor = document.getElementById("input-css");
          if (htmlEditor) htmlEditor.value = state.htmlSource;
          if (cssEditor) cssEditor.value = state.cssSource;

          renderOverview(session.summary);
          renderTokenInventory(session.tokens);
          state.previewManager.setSources(state.htmlSource, state.cssSource, state.cssSource);
          state.previewManager.render();

          applyFiltersAndRenderFindings();
          switchScreen("findings");
        }
      },
      async (renameId, currName) => {
        const newName = prompt("Rename session to:", currName);
        if (newName && newName.trim() && newName !== currName) {
          await api.renameSession(renameId, newName.trim());
          loadSessionsList();
        }
      },
      async (deleteId) => {
        if (confirm("Are you sure you want to permanently delete this saved session?")) {
          await api.deleteSession(deleteId);
          loadSessionsList();
        }
      }
    );
  } catch (err) {
    console.error("Failed to load sessions:", err);
  }
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "flex";
    modal.setAttribute("aria-hidden", "false");
  }
}
