/**
 * ContrastCraft — API Client
 * Clean REST client handling requests, errors, and blob file downloads.
 */

const BASE_URL = window.location.origin;

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}/api${endpoint}`;
  const defaultHeaders = {
    "Accept": "application/json",
    "Content-Type": "application/json"
  };

  const config = {
    ...options,
    headers: { ...defaultHeaders, ...(options.headers || {}) }
  };

  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errorData.detail || `Request failed with status ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  checkHealth: () => request("/health"),
  getPresets: () => request("/presets"),

  runAudit: (html, css = "", sessionName = "Audit") =>
    request("/audit", {
      method: "POST",
      body: JSON.stringify({ html, css, session_name: sessionName })
    }),

  runFolderAudit: (folderPath, exclusions = [], maxFiles = 50) =>
    request("/audit-folder", {
      method: "POST",
      body: JSON.stringify({ folder_path: folderPath, exclusions, max_files: maxFiles })
    }),

  getRecommendations: (foreground, background, targetThreshold = 4.5) =>
    request("/recommend", {
      method: "POST",
      body: JSON.stringify({ foreground, background, target_threshold: targetThreshold })
    }),

  generatePatch: (css, selector, propertyName, newValue, fileName = "styles.css") =>
    request("/patch/generate", {
      method: "POST",
      body: JSON.stringify({
        css,
        selector,
        property_name: propertyName,
        new_value: newValue,
        file_name: fileName
      })
    }),

  applyPatch: (filePath, patchedContent, explicitApproval = false) =>
    request("/patch/apply", {
      method: "POST",
      body: JSON.stringify({
        file_path: filePath,
        patched_content: patchedContent,
        explicit_approval: explicitApproval
      })
    }),

  downloadJsonReport: async (auditData) => {
    const res = await fetch(`${BASE_URL}/api/reports/json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(auditData)
    });
    const blob = await res.blob();
    triggerDownload(blob, "contrastcraft-report.json");
  },

  downloadHtmlReport: async (auditData) => {
    const res = await fetch(`${BASE_URL}/api/reports/html`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(auditData)
    });
    const blob = await res.blob();
    triggerDownload(blob, "contrastcraft-report.html");
  },

  downloadCorrectedCss: async (auditData) => {
    const res = await fetch(`${BASE_URL}/api/export/css`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(auditData)
    });
    const blob = await res.blob();
    triggerDownload(blob, "contrastcraft-corrected.css");
  },

  listSessions: () => request("/sessions"),
  getSession: (id) => request(`/sessions/${id}`),
  saveSession: (sessionData) =>
    request("/sessions", {
      method: "POST",
      body: JSON.stringify(sessionData)
    }),
  renameSession: (id, newName) =>
    request(`/sessions/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ name: newName })
    }),
  deleteSession: (id) =>
    request(`/sessions/${id}`, {
      method: "DELETE"
    }),
  compareSessions: (idA, idB) => request(`/sessions/compare/${idA}/${idB}`)
};

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
