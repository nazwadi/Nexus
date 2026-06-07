/* spell_filters.js — spell list filter bar, sticky offset, back-to-top */

(function () {
    /* Inject back-to-top button CSS once */
    const styleEl = document.createElement("style");
    styleEl.textContent = `
        #back-to-top {
            position: fixed; bottom: 24px; right: 24px; z-index: 99999;
            display: none; width: 44px; height: 44px; border-radius: 50%;
            border: 1px solid #ffffff30; background: #0b0b10; color: #c8a84b;
            font-size: 18px; cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.6); transition: opacity 0.2s;
        }
        #back-to-top:hover { background: #1a1a2e; }
    `;
    document.head.appendChild(styleEl);
}());

const SPELL_FILTER_KEYS = {
    "expansion-mode":  "spells_expansion_mode",
    "expansion-value": "spells_expansion_value",
    "level-mode":      "spells_level_mode",
    "level-value":     "spells_level_value",
};

function saveSpellFilters() {
    Object.entries(SPELL_FILTER_KEYS).forEach(([id, key]) =>
        sessionStorage.setItem(key, $("#" + id).val())
    );
}

function loadSpellFilters() {
    Object.entries(SPELL_FILTER_KEYS).forEach(([id, key]) => {
        const $el = $("#" + id);
        const stored = sessionStorage.getItem(key);
        if (stored !== null) {
            $el.val(stored);
        } else {
            const def = $el.data("default");
            if (def !== undefined && String(def) !== "") $el.val(String(def));
        }
    });
}

function updateSpellFilterSummary() {
    const search    = $("#spell-filter").val().trim();
    const expVal    = $("#expansion-value").val();
    const expMode   = $("#expansion-mode").val();
    const levelVal  = $("#level-value").val();
    const levelMode = $("#level-mode").val();
    const parts = [];
    if (search) parts.push(`"${search}"`);
    if (expVal) {
        const expName = $("#expansion-value option:selected").text();
        parts.push(expMode === "lte" ? `Through ${expName}` : `Only ${expName}`);
    } else {
        parts.push("All Expansions");
    }
    if (levelVal) {
        const lvName = $("#level-value option:selected").text();
        const mod = levelMode === "gte" ? "and higher" : levelMode === "lte" ? "and lower" : "only";
        parts.push(`${lvName} ${mod}`);
    } else {
        parts.push("All Levels");
    }
    $("#spell-filter-summary").text("Showing: " + parts.join(" · "));
}

function applySpellFilters() {
    const textVal       = $("#spell-filter").val().toLowerCase();
    const expansionMode = $("#expansion-mode").val();
    const expansionVal  = $("#expansion-value").val();
    const levelMode     = $("#level-mode").val();
    const levelVal      = $("#level-value").val();
    $("[data-spell-row]").each(function () {
        const row = $(this);
        const textMatch = !textVal || row.text().toLowerCase().indexOf(textVal) > -1;
        let expansionMatch = true;
        if (expansionVal) {
            const rowExp = parseInt(row.attr("data-expansion"));
            const expNum = parseInt(expansionVal);
            expansionMatch = expansionMode === "lte" ? rowExp <= expNum : rowExp === expNum;
        }
        let levelMatch = true;
        if (levelVal) {
            const rowLevel = parseInt(row.attr("data-level"));
            const levelNum = parseInt(levelVal);
            if (levelMode === "gte")      levelMatch = rowLevel >= levelNum;
            else if (levelMode === "lte") levelMatch = rowLevel <= levelNum;
            else                          levelMatch = rowLevel === levelNum;
        }
        const show = textMatch && expansionMatch && levelMatch;
        row.toggle(show);
        row.toggleClass("filter-match", show);
    });
    $("[data-level-header]").each(function () {
        const level = $(this).attr("data-level-header");
        $(this).toggle($(`[data-spell-row][data-level="${level}"].filter-match`).length > 0);
    });
    updateSpellFilterSummary();
    saveSpellFilters();
}

function updateStickyOffset() {
    const bar = document.getElementById("spell-filter-bar");
    if (!bar) return;
    const h = bar.getBoundingClientRect().height;
    if (h === 0) return;
    const stickyTop = parseInt(getComputedStyle(bar).top) || 60;
    document.querySelectorAll(".eq-table-floating-header").forEach(el => {
        el.style.top = (stickyTop + h) + "px";
    });
}

$(document).ready(function () {
    if ($("#spell-filter-bar").length) {
        loadSpellFilters();
        updateStickyOffset();
        $(window).on("resize.spellfilter", updateStickyOffset);

        if (window.ResizeObserver) {
            new ResizeObserver(updateStickyOffset)
                .observe(document.getElementById("spell-filter-bar"));
        }

        $("#spell-filter").on("keyup", applySpellFilters);
        $("#expansion-mode, #expansion-value").on("change", applySpellFilters);
        $("#level-mode, #level-value").on("change", applySpellFilters);
        applySpellFilters();
    }

    /* Back to top */
    $("body").append('<button id="back-to-top" title="Back to top" aria-label="Back to top">&#9650;</button>');
    $(window).on("scroll.btt", function () {
        $("#back-to-top").toggle($(this).scrollTop() > 300);
    });
    $(document).on("click", "#back-to-top", function () {
        $("html, body").animate({ scrollTop: 0 }, 250);
    });
});
