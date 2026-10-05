/* JobConnect — Chart.js dashboard charts */
(function () {
  "use strict";

  const palette = ["#4f46e5", "#0d9488", "#f59e0b", "#e11d48", "#7c3aed", "#059669", "#0ea5e9", "#d97706"];

  function parseJSON(id) {
    const el = document.getElementById(id);
    return el ? JSON.parse(el.textContent) : null;
  }

  const lineCtx = document.getElementById("activityChart");
  const lineData = window.__jcLine || parseJSON("activityChartData");
  if (lineCtx && lineData) {
    new Chart(lineCtx, {
      type: "line",
      data: {
        labels: lineData.labels,
        datasets: [
          {
            label: lineData.series1Label || "Series 1",
            data: lineData.series1,
            borderColor: "#4f46e5",
            backgroundColor: "rgba(79,70,229,.1)",
            fill: true, tension: .35,
          },
          {
            label: lineData.series2Label || "Series 2",
            data: lineData.series2,
            borderColor: "#0d9488",
            backgroundColor: "rgba(13,148,136,.1)",
            fill: true, tension: .35,
          },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  }

  const barCtx = document.getElementById("barChart");
  const barData = window.__jcBar || parseJSON("barChartData");
  if (barCtx && barData) {
    new Chart(barCtx, {
      type: "bar",
      data: {
        labels: barData.labels,
        datasets: [{ label: barData.label || "Count", data: barData.values, backgroundColor: "#4f46e5", borderRadius: 8 }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  }

  const lineCtx2 = document.getElementById("monthlyChart");
  const monthlyData = window.__jcMonthly || parseJSON("monthlyChartData");
  if (lineCtx2 && monthlyData) {
    new Chart(lineCtx2, {
      type: "line",
      data: {
        labels: monthlyData.labels,
        datasets: [
          { label: monthlyData.series1Label || "Series 1", data: monthlyData.series1, borderColor: "#4f46e5", tension: .35 },
          { label: monthlyData.series2Label || "Series 2", data: monthlyData.series2, borderColor: "#0d9488", tension: .35 },
          { label: monthlyData.series3Label || "Series 3", data: monthlyData.series3, borderColor: "#f59e0b", tension: .35 },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  }

  const doughnutCtx = document.getElementById("statusChart");
  const statusData = window.__jcStatus || parseJSON("statusChartData");
  if (doughnutCtx && statusData) {
    new Chart(doughnutCtx, {
      type: "doughnut",
      data: {
        labels: statusData.labels,
        datasets: [{ data: statusData.values, backgroundColor: palette, borderWidth: 0 }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        cutout: "62%",
        plugins: { legend: { position: "bottom" } },
      },
    });
  }
})();
