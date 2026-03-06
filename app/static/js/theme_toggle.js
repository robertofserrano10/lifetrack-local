document.addEventListener("DOMContentLoaded", () => {

const toggle = document.getElementById("theme-toggle");

const savedTheme = localStorage.getItem("theme");

if (savedTheme) {
document.documentElement.setAttribute("data-theme", savedTheme);
}

toggle.addEventListener("click", () => {

let current = document.documentElement.getAttribute("data-theme");

let next = current === "dark" ? "light" : "dark";

document.documentElement.setAttribute("data-theme", next);

localStorage.setItem("theme", next);

});

});