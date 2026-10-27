/**
 * ContrastCraft — Theme Switcher
 * Persists user preference and respects system preferences with WCAG-compliant colors.
 */

const THEME_KEY = "contrastcraft_theme";

export function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === "dark" || saved === "light") {
    setTheme(saved);
  } else {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setTheme(prefersDark ? "dark" : "light");
  }

  // Listen for system changes if not explicitly overridden
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
    if (!localStorage.getItem(THEME_KEY)) {
      setTheme(e.matches ? "dark" : "light");
    }
  });

  const toggleBtn = document.getElementById("btn-theme-toggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "light";
      const next = current === "dark" ? "light" : "dark";
      setTheme(next);
      localStorage.setItem(THEME_KEY, next);
    });
  }
}

export function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const toggleBtn = document.getElementById("btn-theme-toggle");
  if (toggleBtn) {
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
  window.dispatchEvent(new CustomEvent("contrastcraft:themechange", { detail: { theme } }));
}
