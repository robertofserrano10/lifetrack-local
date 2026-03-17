document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("theme-toggle");
  const icon = toggle?.querySelector("i");

  const setIcon = (theme) => {
    if (!icon) return;
    icon.classList.remove("fa-moon", "fa-sun");
    icon.classList.add(theme === "dark" ? "fa-sun" : "fa-moon");
  };

  const savedTheme = localStorage.getItem("theme");
  const fallback = "light";
  const theme = savedTheme || fallback;
  document.documentElement.setAttribute("data-theme", theme);
  setIcon(theme);

  toggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    setIcon(next);
  });
});