/* JobConnect — shared frontend JS */
(function () {
  "use strict";

  const csrfToken =
    document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
    document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";

  function postJSON(url, data) {
    const isForm = data instanceof FormData;
    return fetch(url, {
      method: "POST",
      headers: isForm ? {} : { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: isForm ? data : JSON.stringify(data || {}),
      credentials: "same-origin",
    }).then(async (r) => {
      let payload = {};
      try { payload = await r.json(); } catch (e) { /* ignore */ }
      if (!r.ok && payload && !payload.error) payload.error = `Request failed (${r.status})`;
      return { ok: r.ok, status: r.status, ...payload };
    });
  }
  window.jcPost = postJSON;

  /* ---------------- Toasts ---------------- */
  window.jcToast = function (message, type = "success") {
    let holder = document.getElementById("jc-toast-holder");
    if (!holder) {
      holder = document.createElement("div");
      holder.id = "jc-toast-holder";
      holder.style.cssText = "position:fixed;top:70px;right:16px;z-index:2000;display:flex;flex-direction:column;gap:8px;";
      document.body.appendChild(holder);
    }
    const bg = type === "error" ? "danger" : type === "info" ? "primary" : "success";
    const el = document.createElement("div");
    el.className = `alert alert-${bg} shadow`;
    el.style.cssText = "min-width:260px;margin:0;border-radius:12px;";
    el.textContent = message;
    holder.appendChild(el);
    setTimeout(() => el.remove(), 3500);
  };

  /* ---------------- Save / unsave job ---------------- */
  document.addEventListener("click", async function (e) {
    const btn = e.target.closest(".js-save-job");
    if (!btn) return;
    e.preventDefault();
    if (!window.JC_USER_AUTHENTICATED) {
      window.location.href = btn.dataset.loginUrl || "/accounts/login/";
      return;
    }
    const res = await postJSON(btn.dataset.url);
    if (res.success) {
      btn.innerHTML = res.saved
        ? '<i class="bi bi-bookmark-fill"></i> Saved'
        : '<i class="bi bi-bookmark"></i> Save Job';
      btn.classList.toggle("btn-light-brand", res.saved);
      window.jcToast(res.message, "success");
      document.dispatchEvent(new CustomEvent("job-save-toggled", { detail: { jobId: btn.dataset.jobId, saved: res.saved } }));
    } else {
      window.jcToast(res.error || "Could not save job.", "error");
    }
  });

  /* ---------------- Mark notification read ---------------- */
  document.addEventListener("click", async function (e) {
    const item = e.target.closest(".js-mark-read");
    if (!item) return;
    e.preventDefault();
    await postJSON(item.dataset.url);
    item.classList.remove("unread", "js-mark-read");
  });

  const markAllBtn = document.getElementById("js-mark-all-read");
  if (markAllBtn) {
    markAllBtn.addEventListener("click", async function () {
      const res = await postJSON(this.dataset.url);
      if (res.success) {
        document.querySelectorAll(".notif-item.unread").forEach((el) => el.classList.remove("unread", "js-mark-read"));
        window.jcToast(res.message || "All marked as read");
      }
    });
  }

  /* ---------------- Dashboard sidebar (mobile) ---------------- */
  const sidebarToggle = document.getElementById("js-sidebar-toggle");
  const sidebar = document.getElementById("jcSidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
      let backdrop = document.querySelector(".sidebar-backdrop");
      if (sidebar.classList.contains("open")) {
        if (!backdrop) {
          backdrop = document.createElement("div");
          backdrop.className = "sidebar-backdrop";
          document.body.appendChild(backdrop);
          backdrop.addEventListener("click", () => sidebar.classList.remove("open"));
        }
      } else if (backdrop) backdrop.remove();
    });
  }

  /* ---------------- OTP inputs auto-advance ---------------- */
  document.querySelectorAll(".otp-input").forEach((input, idx, arr) => {
    input.addEventListener("input", () => {
      input.value = input.value.replace(/\D/g, "").slice(0, 1);
      if (input.value && arr[idx + 1]) arr[idx + 1].focus();
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !input.value && arr[idx - 1]) arr[idx - 1].focus();
    });
    input.addEventListener("paste", (e) => {
      const text = (e.clipboardData.getData("text") || "").replace(/\D/g, "").slice(0, 6);
      if (text.length === 6) {
        e.preventDefault();
        arr.forEach((el, i) => (el.value = text[i] || ""));
        arr[5].focus();
      }
    });
  });

  /* ---------------- AJAX delete buttons (confirm) ---------------- */
  document.addEventListener("click", async function (e) {
    const btn = e.target.closest(".js-confirm-action");
    if (!btn) return;
    e.preventDefault();
    const msg = btn.dataset.confirm || "Are you sure?";
    if (!window.confirm(msg)) return;
    const res = await postJSON(btn.dataset.url);
    if (res.success) {
      window.jcToast(res.message || "Done");
      const row = btn.closest("tr");
      if (row) row.remove();
      else setTimeout(() => window.location.reload(), 600);
    } else {
      window.jcToast(res.error || "Action failed.", "error");
    }
  });

  window.JC_CSRF = csrfToken;
})();
