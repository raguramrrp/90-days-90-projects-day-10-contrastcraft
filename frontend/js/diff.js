/**
 * ContrastCraft — Diff Formatter
 * Converts unified diff text into styled HTML elements with safe escaping.
 */

export function renderUnifiedDiff(diffText) {
  if (!diffText || !diffText.trim()) {
    return `<div class="diff-line header">No diff changes detected.</div>`;
  }

  const lines = diffText.split("\n");
  const htmlLines = lines.map((line) => {
    const escaped = escapeHtml(line);
    if (line.startsWith("+++") || line.startsWith("---") || line.startsWith("@@")) {
      return `<span class="diff-line header">${escaped}</span>`;
    } else if (line.startsWith("+")) {
      return `<span class="diff-line add">${escaped}</span>`;
    } else if (line.startsWith("-")) {
      return `<span class="diff-line del">${escaped}</span>`;
    }
    return `<span class="diff-line">${escaped}</span>`;
  });

  return `<div class="diff-viewer">${htmlLines.join("")}</div>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
