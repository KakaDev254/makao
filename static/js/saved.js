// =========================================================
// Makao — Saved properties page
// Reads saved slugs from localStorage, fetches real cards.
// =========================================================

(function () {
    "use strict";

    const SAVED_KEY = "makao_saved";
    const resultsBox = document.querySelector("[data-saved-results]");
    const countText = document.querySelector("[data-saved-count-text]");
    const countPlural = document.querySelector("[data-saved-count-plural]");

    if (!resultsBox) return;

    function getSaved() {
        try { return JSON.parse(localStorage.getItem(SAVED_KEY) || "[]"); }
        catch { return []; }
    }

    function setSaved(list) {
        localStorage.setItem(SAVED_KEY, JSON.stringify(list));
        const counter = document.querySelector("[data-saved-count]");
        if (counter) counter.textContent = list.length;
        updateMeta();
    }

    function updateMeta() {
        const n = getSaved().length;
        if (countText) countText.textContent = n;
        if (countPlural) countPlural.textContent = n === 1 ? "y" : "ies";
    }

    function emptyState() {
        return `
            <div class="empty-state">
                <div class="empty-icon">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M12 20s-7-4.6-7-10.2A4.3 4.3 0 0 1 12 6.6a4.3 4.3 0 0 1 7 3.2C19 15.4 12 20 12 20z"
                              stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                    </svg>
                </div>
                <p class="empty-title">Nothing saved yet.</p>
                <p class="empty-sub">Tap the heart on any listing and it will show up here.</p>
                <a href="/" class="btn btn-primary">Browse properties</a>
            </div>`;
    }

    function fetchSaved() {
        const saved = getSaved();
        updateMeta();

        if (!saved.length) {
            resultsBox.innerHTML = emptyState();
            return;
        }

        const qs = encodeURIComponent(saved.join(","));
        fetch(`/properties/by-slugs/?slugs=${qs}`, {
            headers: { "X-Requested-With": "fetch" },
        })
            .then(r => r.text())
            .then(html => {
                resultsBox.innerHTML = html;
                // Re-sync hearts (listings.js handles this via its own code,
                // but our page runs standalone — we call it here too).
                if (window.MakaoListings && window.MakaoListings.syncSaveButtons) {
                    window.MakaoListings.syncSaveButtons();
                } else {
                    // Fallback: mark hearts directly
                    document.querySelectorAll("[data-save-toggle]").forEach(function (btn) {
                        if (getSaved().includes(btn.dataset.slug)) {
                            btn.classList.add("is-saved");
                        }
                    });
                }
                bindCardClicks();
            })
            .catch(() => {
                resultsBox.innerHTML = `
                    <div class="empty-state">
                        <p class="empty-title">Could not load your saved properties.</p>
                        <p class="empty-sub">Check your connection and try again.</p>
                    </div>`;
            });
    }

    // ---------- Unsave from this page ----------
    document.addEventListener("click", function (e) {
        const saveBtn = e.target.closest("[data-save-toggle]");
        if (!saveBtn) return;
        e.stopPropagation();

        const slug = saveBtn.dataset.slug;
        const list = getSaved();
        const i = list.indexOf(slug);
        if (i === -1) list.push(slug); else list.splice(i, 1);
        setSaved(list);

        // On the saved page, unsaving should remove the card.
        if (!list.includes(slug)) {
            const card = saveBtn.closest(".pcard");
            if (card) {
                card.style.opacity = "0";
                setTimeout(() => {
                    card.remove();
                    if (!getSaved().length) {
                        resultsBox.innerHTML = emptyState();
                    }
                }, 180);
            }
        } else {
            saveBtn.classList.add("is-saved");
        }
    });

    // ---------- Modal opens on card click ----------
    function bindCardClicks() {
        document.querySelectorAll(".pcard").forEach(function (card) {
            card.addEventListener("click", function (e) {
                if (e.target.closest("[data-save-toggle]")) return;
                // Use the modal helper from listings.js if present
                const modal = document.getElementById("property-modal");
                if (modal) {
                    modal.dispatchEvent(new CustomEvent("makao:open", { detail: { slug: card.dataset.slug } }));
                }
            });
        });
    }

    // Expose minimal API for listings.js interop (optional)
    window.MakaoSaved = {
        refresh: fetchSaved,
        getSaved: getSaved,
        setSaved: setSaved,
    };

    fetchSaved();
})();