// =========================================================
// Makao — base interactions
// =========================================================

document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector("[data-menu-toggle]");
    const drawer = document.querySelector("[data-mobile-drawer]");

    if (toggle && drawer) {
        toggle.addEventListener("click", () => {
            const isOpen = toggle.getAttribute("aria-expanded") === "true";
            toggle.setAttribute("aria-expanded", String(!isOpen));
            drawer.hidden = isOpen;
            document.body.style.overflow = isOpen ? "" : "hidden";
        });
    }

    // Saved-count placeholder — real logic arrives in Section 6
    const counter = document.querySelector("[data-saved-count]");
    if (counter) {
        const saved = JSON.parse(localStorage.getItem("makao_saved") || "[]");
        counter.textContent = saved.length;
    }
});