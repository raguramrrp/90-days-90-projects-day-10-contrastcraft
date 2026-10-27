/**
 * ContrastCraft — UI Renderers
 * Pure UI component renderers for tables, cards, inspector drawer, tokens, and sessions.
 */

export function renderOverview(summary) {
  const scoreEl = document.getElementById("stat-score");
  const totalEl = document.getElementById("stat-total");
  const passAaEl = document.getElementById("stat-pass-aa");
  const failAaEl = document.getElementById("stat-fail-aa");
  const passAaaEl = document.getElementById("stat-pass-aaa");
  const verifyEl = document.getElementById("stat-unresolved");

  if (scoreEl) scoreEl.textContent = `${summary.compliance_score || 0}%`;
  if (totalEl) totalEl.textContent = summary.total_analyzed || 0;
  if (passAaEl) passAaEl.textContent = summary.pass_aa_count || 0;
  if (failAaEl) failAaEl.textContent = summary.fail_aa_count || 0;
  if (passAaaEl) passAaaEl.textContent = summary.pass_aaa_count || 0;
  if (verifyEl) verifyEl.textContent = summary.needs_verification_count || 0;

  // Nav badge update
  const navFailBadge = document.getElementById("nav-fail-count");
  if (navFailBadge) {
    const fails = summary.fail_aa_count || 0;
    navFailBadge.textContent = fails;
    navFailBadge.style.display = fails > 0 ? "inline-block" : "none";
  }
}

export function renderFindingsTable(findings, onSelectFinding, onFixFinding) {
  const tbody = document.getElementById("findings-tbody");
  if (!tbody) return;

  if (!findings || findings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--cc-text-muted);">No findings match the active criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = findings.map((f) => {
    let badgeClass = "badge-pass";
    let badgeLabel = "AA PASS";
    if (f.status === "unresolved") {
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
            ${!f.pass_aa ? `<button class="btn btn-primary btn-sm btn-fix" data-id="${f.id}">Fix in Studio</button>` : ""}
          </div>
        </td>
      </tr>
    `;
  }).join("");

  // Attach event listeners
  tbody.querySelectorAll(".btn-inspect").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const item = findings.find((x) => x.id === id);
      if (item && onSelectFinding) onSelectFinding(item);
    });
  });

  tbody.querySelectorAll(".btn-fix").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const item = findings.find((x) => x.id === id);
      if (item && onFixFinding) onFixFinding(item);
    });
  });
}

export function renderInspectorDrawer(finding, onOpenFixStudio) {
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
          <div style="font-size:1.5rem;font-weight:800;color:${finding.pass_aa ? "var(--cc-pass-text)" : "var(--cc-fail-text)};">
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

    ${!finding.pass_aa ? `
      <button id="btn-inspector-fix" class="btn btn-primary" style="width:100%;">
        Open in Fix Studio &amp; Preview
      </button>
    ` : ""}
  `;

  const fixBtn = document.getElementById("btn-inspector-fix");
  if (fixBtn && onOpenFixStudio) {
    fixBtn.addEventListener("click", () => onOpenFixStudio(finding));
  }
}

export function renderRecommendationCards(recommendations, onSelectSuggestion) {
  const container = document.getElementById("fix-suggestions-grid");
  if (!container) return;

  const suggestions = recommendations.suggestions || [];
  if (suggestions.length === 0) {
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
      if (onSelectSuggestion) onSelectSuggestion(hex);
    });
  });
}

export function renderTokenInventory(tokens) {
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

export function renderSessionsList(sessions, onLoad, onRename, onDelete) {
  const container = document.getElementById("sessions-list-container");
  if (!container) return;

  if (!sessions || sessions.length === 0) {
    container.innerHTML = `<div style="text-align:center;padding:32px;color:var(--cc-text-muted);">No saved audit sessions found. Run an audit and save your session.</div>`;
    return;
  }

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
        <button class="btn btn-secondary btn-sm btn-rename-session" data-id="${s.id}" data-name="${escapeHtml(s.name)}">Rename</button>
        <button class="btn btn-danger btn-sm btn-delete-session" data-id="${s.id}">Delete</button>
      </div>
    </div>
  `).join("");

  container.querySelectorAll(".btn-load-session").forEach((btn) => {
    btn.addEventListener("click", () => onLoad(btn.getAttribute("data-id")));
  });

  container.querySelectorAll(".btn-rename-session").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const currName = btn.getAttribute("data-name");
      onRename(id, currName);
    });
  });

  container.querySelectorAll(".btn-delete-session").forEach((btn) => {
    btn.addEventListener("click", () => onDelete(btn.getAttribute("data-id")));
  });
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
