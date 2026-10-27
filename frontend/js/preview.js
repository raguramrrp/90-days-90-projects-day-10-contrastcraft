/**
 * ContrastCraft — Isolated Sandboxed Live Preview Manager
 * Renders HTML/CSS within an isolated iframe and provides target highlighting.
 */

export class PreviewManager {
  constructor(iframeElementId) {
    this.iframe = document.getElementById(iframeElementId);
    this.htmlSource = "";
    this.originalCss = "";
    this.patchedCss = "";
    this.activeMode = "original"; // 'original' | 'patched'
    this.targetSelector = null;
  }

  setSources(html, originalCss = "", patchedCss = "") {
    this.htmlSource = html;
    this.originalCss = originalCss;
    this.patchedCss = patchedCss || originalCss;
  }

  setTargetSelector(selector) {
    this.targetSelector = selector;
    this.render();
  }

  setMode(mode) {
    this.activeMode = mode;
    this.render();
  }

  setViewportWidth(widthStr) {
    if (this.iframe) {
      this.iframe.style.width = widthStr;
    }
  }

  render() {
    if (!this.iframe) return;

    const cssToUse = this.activeMode === "patched" ? this.patchedCss : this.originalCss;

    // Highlight style injection for the target element
    let highlightCss = "";
    if (this.targetSelector) {
      highlightCss = `
        ${this.targetSelector} {
          outline: 3px solid #0284C7 !important;
          outline-offset: 4px !important;
          position: relative;
          box-shadow: 0 0 0 6px rgba(2, 132, 199, 0.25) !important;
          animation: cc-pulse-highlight 2s infinite !important;
        }
        @keyframes cc-pulse-highlight {
          0% { box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.4); }
          50% { box-shadow: 0 0 0 8px rgba(2, 132, 199, 0.1); }
          100% { box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.4); }
        }
      `;
    }

    const docContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    /* Injected user stylesheet */
    ${cssToUse}
    /* Injected element focus highlight */
    ${highlightCss}
  </style>
</head>
<body>
  ${this.htmlSource}
</body>
</html>`;

    this.iframe.srcdoc = docContent;
  }
}
