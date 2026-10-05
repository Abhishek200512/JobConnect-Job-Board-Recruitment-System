/* JobConnect — AJAX job search & filtering */
(function () {
  "use strict";

  const form = document.getElementById("jobFilterForm");
  const results = document.getElementById("jobResults");
  const countEl = document.getElementById("resultsCount");
  const searchBtn = document.getElementById("jsSearchBtn");
  if (!form || !results) return;

  const spinner = `
    <div class="text-center py-5 w-100" id="jc-loading">
      <div class="spinner-border text-primary"></div>
      <p class="mt-2 text-muted">Loading jobs…</p>
    </div>`;

  let debounceTimer = null;
  let activeController = null;

  function currentParams(page) {
    const fd = new FormData(form);
    const params = new URLSearchParams();
    for (const [k, v] of fd.entries()) if (v && v !== "all") params.set(k, v);
    if (page) params.set("page", page);
    return params;
  }

  function updateUrl(params) {
    const url = window.location.pathname + (params.toString() ? "?" + params.toString() : "");
    window.history.replaceState({}, "", url);
  }

  async function loadJobs(page) {
    const params = currentParams(page);
    if (activeController) activeController.abort();
    activeController = new AbortController();

    results.innerHTML = spinner;
    try {
      const res = await fetch(`/jobs/ajax/?${params.toString()}`, {
        signal: activeController.signal,
        credentials: "same-origin",
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "Failed to load");

      results.innerHTML = data.html;
      if (countEl) countEl.textContent = `${data.total} job${data.total === 1 ? "" : "s"} found`;
      updateUrl(params);
      bindPagination();
    } catch (err) {
      if (err.name === "AbortError") return;
      results.innerHTML = `<div class="empty-state w-100"><i class="bi bi-wifi-off"></i>
        <p>Something went wrong while loading jobs. Please try again.</p></div>`;
    }
  }

  function bindPagination() {
    results.querySelectorAll(".js-page-link").forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        loadJobs(a.dataset.page);
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    loadJobs(1);
  });

  // Debounced live filtering on selects & text inputs
  form.querySelectorAll("select, input[type=text]").forEach((el) => {
    el.addEventListener("change", () => loadJobs(1));
    el.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => loadJobs(1), 450);
    });
  });

  const resetBtn = document.getElementById("jsResetFilters");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      form.reset();
      loadJobs(1);
    });
  }

  bindPagination();
})();
