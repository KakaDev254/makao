// =========================================================
// Makao — Listings: filter pills, favorites, modal, skeletons
// =========================================================

(function () {
    "use strict";

    const SAVED_KEY = "makao_saved";
    const resultsBox = document.querySelector("[data-listings-results]");
    const pills = document.querySelectorAll("[data-filter-pills] .pill");
    const modal = document.getElementById("property-modal");

    // ---------- Favorites (localStorage) ----------
    function getSaved() {
        try { return JSON.parse(localStorage.getItem(SAVED_KEY) || "[]"); }
        catch { return []; }
    }
    function setSaved(list) {
        localStorage.setItem(SAVED_KEY, JSON.stringify(list));
        const counter = document.querySelector("[data-saved-count]");
        if (counter) counter.textContent = list.length;
    }
    function toggleSaved(slug) {
        const list = getSaved();
        const i = list.indexOf(slug);
        if (i === -1) list.push(slug); else list.splice(i, 1);
        setSaved(list);
        return list.includes(slug);
    }
    function isSaved(slug) { return getSaved().includes(slug); }

    function syncSaveButtons() {
        document.querySelectorAll("[data-save-toggle]").forEach(function (btn) {
            const slug = btn.dataset.slug;
            btn.classList.toggle("is-saved", isSaved(slug));
        });
        const counter = document.querySelector("[data-saved-count]");
        if (counter) counter.textContent = getSaved().length;
    }

    // ---------- Skeleton / error markup ----------
    function skeletonHTML() {
        const card = `
            <article class="pcard pcard--skeleton" aria-hidden="true">
                <div class="pcard-media skeleton-block"></div>
                <div class="pcard-body">
                    <div class="skeleton-line skeleton-line--title"></div>
                    <div class="skeleton-line skeleton-line--short"></div>
                    <div class="pcard-specs">
                        <span class="skeleton-chip"></span>
                        <span class="skeleton-chip"></span>
                        <span class="skeleton-chip"></span>
                    </div>
                    <div class="pcard-footer">
                        <div class="skeleton-line skeleton-line--price"></div>
                    </div>
                </div>
            </article>`;
        return `<div class="listings-grid" aria-busy="true">${card.repeat(8)}</div>`;
    }

    function errorHTML() {
        return `
            <div class="empty-state">
                <p class="empty-title">Could not load listings.</p>
                <p class="empty-sub">Check your connection and try again.</p>
                <button type="button" class="btn btn-primary" data-reset-filters>Retry</button>
            </div>`;
    }

    // ---------- Listings fetch ----------
    function fetchListings(params) {
        if (!resultsBox) return;

        // Show skeletons while we fetch
        resultsBox.innerHTML = skeletonHTML();

        const qs = new URLSearchParams(params).toString();
        fetch(`/properties/listings/?${qs}`, { headers: { "X-Requested-With": "fetch" } })
            .then(r => r.text())
            .then(html => {
                resultsBox.innerHTML = html;
                syncSaveButtons();
                bindCardClicks();
            })
            .catch(() => {
                resultsBox.innerHTML = errorHTML();
            });
    }

    function currentCategory() {
        const active = document.querySelector("[data-filter-pills] .pill.is-active");
        return active ? active.dataset.filter : "all";
    }

    // ---------- Filter pills ----------
    pills.forEach(function (pill) {
        pill.addEventListener("click", function () {
            pills.forEach(p => p.classList.remove("is-active"));
            pill.classList.add("is-active");

            const filter = pill.dataset.filter;

            if (filter === "saved") {
                const saved = getSaved();
                if (!saved.length) {
                    resultsBox.innerHTML = `
                        <div class="empty-state">
                            <p class="empty-title">No saved properties yet.</p>
                            <p class="empty-sub">Tap the heart on any listing to save it here.</p>
                        </div>`;
                    return;
                }
                fetchListings({ category: "all" });
                // After fetch, hide unsaved cards
                setTimeout(function () {
                    document.querySelectorAll(".pcard").forEach(function (card) {
                        if (!saved.includes(card.dataset.slug)) card.style.display = "none";
                    });
                }, 400);
                return;
            }

            fetchListings({ category: filter });
        });
    });

    // ---------- Delegated clicks ----------
    document.addEventListener("click", function (e) {
        // On the saved page, saved.js owns click handling — skip here
        if (document.body.dataset.page === "saved") return;

        const saveBtn = e.target.closest("[data-save-toggle]");
        if (saveBtn) {
            e.stopPropagation();
            toggleSaved(saveBtn.dataset.slug);
            syncSaveButtons();
            return;
        }

        const reset = e.target.closest("[data-reset-filters]");
        if (reset) {
            document.querySelectorAll("[data-filter-pills] .pill").forEach(p => p.classList.remove("is-active"));
            document.querySelector("[data-filter-pills] .pill[data-filter='all']").classList.add("is-active");
            const form = document.getElementById("hero-search");
            if (form) form.reset();
            fetchListings({ category: "all" });
            return;
        }

        // "View full listing" → manual navigation
        const viewFull = e.target.closest("[data-modal-view-full]");
        if (viewFull) {
            e.preventDefault();
            const url = viewFull.dataset.href;
            if (url && url !== "#") window.location.href = url;
            return;
        }

        const closeBtn = e.target.closest("[data-modal-close]");
        if (closeBtn) {
            closeModal();
            return;
        }
    });

    // ---------- Card click → open modal ----------
    function bindCardClicks() {
        document.querySelectorAll(".pcard").forEach(function (card) {
            card.addEventListener("click", function (e) {
                if (e.target.closest("[data-save-toggle]")) return;
                openModal(card.dataset.slug);
            });
        });
    }

    function openModal(slug) {
        if (!modal) return;
        modal.hidden = false;
        document.body.style.overflow = "hidden";

        // Reset visual state
        modal.querySelector("[data-modal-title]").textContent = "Loading…";
        modal.querySelector("[data-modal-description]").textContent = "";
        modal.querySelector("[data-modal-specs]").innerHTML = "";
        modal.querySelector("[data-modal-media]").innerHTML = "";

        // Reset the full-listing link until data arrives
        const fullLink = modal.querySelector("[data-modal-view-full]");
        if (fullLink) {
            fullLink.dataset.href = "";
            fullLink.href = "#";
        }

        fetch(`/properties/${slug}/json/`)
            .then(r => r.json())
            .then(data => {
                const mediaBox = modal.querySelector("[data-modal-media]");
                if (data.cover_image) {
                    mediaBox.innerHTML = `<img src="${data.cover_image}" alt="">`;
                } else {
                    mediaBox.innerHTML = `<div class="pcard-media-fallback"><span>${data.category}</span></div>`;
                }

                modal.querySelector("[data-modal-category]").textContent = data.category;
                modal.querySelector("[data-modal-title]").textContent = data.title;
                modal.querySelector("[data-modal-location]").textContent =
                    `${data.neighborhood}, ${data.county}`;
                modal.querySelector("[data-modal-price]").textContent = data.price_display;
                modal.querySelector("[data-modal-description]").textContent = data.description;
                modal.querySelector("[data-modal-agent]").textContent = data.agent_name;
                modal.querySelector("[data-modal-phone]").textContent = "+" + data.agent_phone;

                const specsBox = modal.querySelector("[data-modal-specs]");
                const rows = [];
                rows.push(["Type", data.property_type]);
                if (data.bedrooms)  rows.push(["Bedrooms", data.bedrooms]);
                if (data.bathrooms) rows.push(["Bathrooms", data.bathrooms]);
                if (data.guests)    rows.push(["Guests", data.guests]);
                if (data.plot_size) rows.push(["Plot size", data.plot_size]);
                if (data.area_sqft) rows.push(["Area", `${data.area_sqft} sqft`]);
                if (data.is_verified) rows.push(["Status", "Verified"]);

                specsBox.innerHTML = rows.map(([k, v]) => `
                    <li>
                        <span class="spec-label">${k}</span>
                        <span class="spec-value">${v}</span>
                    </li>`).join("");

                modal.querySelector("[data-modal-whatsapp]").href = data.whatsapp_url;
                modal.querySelector("[data-modal-call]").href = data.call_url;

                if (fullLink) {
                    fullLink.dataset.href = "/properties/" + data.slug + "/";
                }
            })
            .catch(() => {
                modal.querySelector("[data-modal-title]").textContent = "Could not load listing.";
            });
    }

    function closeModal() {
        if (!modal) return;
        modal.hidden = true;
        document.body.style.overflow = "";
    }

    // ESC closes modal
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && modal && !modal.hidden) closeModal();
    });

    // ---------- Initial bind ----------
    bindCardClicks();
    syncSaveButtons();

    // ---------- Expose API for other pages (e.g. /saved/) ----------
    window.MakaoListings = {
        syncSaveButtons: syncSaveButtons,
        openModal: openModal,
        closeModal: closeModal,
        bindCardClicks: bindCardClicks,
        getSaved: getSaved,
        setSaved: setSaved,
        toggleSaved: toggleSaved,
    };
})();