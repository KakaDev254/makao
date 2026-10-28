// =========================================================
// Makao — base interactions
// =========================================================

document.addEventListener("DOMContentLoaded", () => {
    // ---------- Mobile Drawer ----------
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

    // ---------- User Dropdown (Desktop) ----------
    const userToggle = document.querySelector("[data-user-menu-toggle]");
    const userDropdown = document.querySelector("[data-user-dropdown]");

    if (userToggle && userDropdown) {
        userToggle.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation(); // Prevent the click from instantly closing it
            
            // Toggle the visibility class
            userDropdown.classList.toggle("is-hidden");
            
            // Update accessibility attributes
            const isHidden = userDropdown.classList.contains("is-hidden");
            userToggle.setAttribute("aria-expanded", String(!isHidden));
        });

        // Close when clicking outside
        document.addEventListener("click", function (e) {
            if (!userDropdown.classList.contains("is-hidden")) {
                // If the click is NOT inside the dropdown or the toggle button
                if (!userDropdown.contains(e.target) && !userToggle.contains(e.target)) {
                    userDropdown.classList.add("is-hidden");
                    userToggle.setAttribute("aria-expanded", "false");
                }
            }
        });

        // Close on Escape key
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && !userDropdown.classList.contains("is-hidden")) {
                userDropdown.classList.add("is-hidden");
                userToggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    // ---------- Saved Properties Count ----------
    const counter = document.querySelector("[data-saved-count]");
    if (counter) {
        try {
            const saved = JSON.parse(localStorage.getItem("makao_saved") || "[]");
            counter.textContent = saved.length;
        } catch (e) {
            counter.textContent = "0";
        }
    }
});