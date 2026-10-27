/**
 * ContrastCraft — Keyboard Shortcuts & Accessibility Focus
 */

export function initShortcuts({ onAudit, onSwitchTab, onToggleTheme, onFocusSearch }) {
  window.addEventListener("keydown", (e) => {
    // If inside an input or textarea, only catch Escape
    const activeEl = document.activeElement;
    const isEditing = activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA");

    if (e.key === "Escape") {
      closeAllModals();
      return;
    }

    if (e.key === "?" && !isEditing && (e.shiftKey || e.key === "?")) {
      e.preventDefault();
      openShortcutsModal();
      return;
    }

    if (e.altKey) {
      if (e.key === "a" || e.key === "A") {
        e.preventDefault();
        if (onAudit) onAudit();
      } else if (e.key === "t" || e.key === "T") {
        e.preventDefault();
        if (onToggleTheme) onToggleTheme();
      } else if (e.key === "s" || e.key === "S") {
        e.preventDefault();
        if (onFocusSearch) onFocusSearch();
      } else if (e.key >= "1" && e.key <= "5") {
        e.preventDefault();
        const tabIndex = parseInt(e.key, 10);
        const tabMap = {
          1: "workspace",
          2: "findings",
          3: "fix-studio",
          4: "tokens",
          5: "sessions"
        };
        if (onSwitchTab && tabMap[tabIndex]) {
          onSwitchTab(tabMap[tabIndex]);
        }
      }
    }
  });

  const shortcutsBtn = document.getElementById("btn-shortcuts");
  if (shortcutsBtn) {
    shortcutsBtn.addEventListener("click", openShortcutsModal);
  }
}

export function openShortcutsModal() {
  const modal = document.getElementById("shortcuts-modal");
  if (modal) {
    modal.style.display = "flex";
    modal.setAttribute("aria-hidden", "false");
    const closeBtn = modal.querySelector(".modal-close-btn");
    if (closeBtn) closeBtn.focus();
  }
}

export function closeAllModals() {
  const modals = document.querySelectorAll(".modal-overlay");
  modals.forEach((m) => {
    m.style.display = "none";
    m.setAttribute("aria-hidden", "true");
  });
}
