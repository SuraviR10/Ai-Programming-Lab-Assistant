/* ═══════════════════════════════════════════════════════════════
   AI Programming Lab — Charts (charts.js)
   Chart.js configurations with Real-time Data Update Engine
   ═══════════════════════════════════════════════════════════════ */

const Charts = (() => {
  const chartInstances = new Map();

  const defaultFontFamily = "'Inter', sans-serif";
  const gridColor = 'rgba(30, 41, 59, 0.5)';
  const tickColor = '#64748b';

  function setDefaults() {
    if (typeof Chart === 'undefined') return;

    Chart.defaults.font.family = defaultFontFamily;
    Chart.defaults.font.size = 12;
    Chart.defaults.color = tickColor;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 16;
    Chart.defaults.plugins.tooltip.backgroundColor = '#0d152e';
    Chart.defaults.plugins.tooltip.borderColor = '#1e293b';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.titleFont = { weight: '700' };
  }

  function getCanvas(canvasId) {
    if (typeof canvasId === 'string') {
      return document.getElementById(canvasId);
    }
    return canvasId;
  }

  function destroyExisting(canvasId) {
    if (chartInstances.has(canvasId)) {
      try {
        chartInstances.get(canvasId).destroy();
      } catch (e) {}
      chartInstances.delete(canvasId);
    }
  }

  // ── Progress Timeline Chart ─────────────────────────────────
  function createProgressTimeline(canvasId, data) {
    const ctx = getCanvas(canvasId);
    if (!ctx) return null;
    destroyExisting(canvasId);

    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map(d => d.week),
        datasets: [
          {
            label: 'Avg Score',
            data: data.map(d => d.avgScore),
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#6366f1',
            pointBorderColor: '#0f172a',
            pointBorderWidth: 2,
            pointRadius: 5,
            pointHoverRadius: 7,
          },
          {
            label: 'Success Rate',
            data: data.map(d => d.successRate / 10),
            borderColor: '#4ade80',
            backgroundColor: 'rgba(74, 222, 128, 0.05)',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#4ade80',
            pointBorderColor: '#0f172a',
            pointBorderWidth: 2,
            pointRadius: 5,
            pointHoverRadius: 7,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        scales: {
          y: {
            beginAtZero: true,
            max: 10,
            grid: { color: gridColor },
            ticks: { stepSize: 2 },
          },
          x: {
            grid: { color: gridColor },
          },
        },
        plugins: {
          legend: { position: 'top' },
        },
      },
    });

    chartInstances.set(canvasId, chart);
    return chart;
  }

  // ── Success Rate Doughnut ───────────────────────────────────
  function createSuccessRate(canvasId, rate) {
    const ctx = getCanvas(canvasId);
    if (!ctx) return null;
    destroyExisting(canvasId);

    const chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Success', 'Remaining'],
        datasets: [{
          data: [rate, 100 - rate],
          backgroundColor: ['#6366f1', '#1e293b'],
          borderWidth: 0,
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '78%',
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false },
        },
      },
    });

    chartInstances.set(canvasId, chart);
    return chart;
  }

  // ── Problems Per Week Bar Chart ─────────────────────────────
  function createWeeklyProblems(canvasId, data) {
    const ctx = getCanvas(canvasId);
    if (!ctx) return null;
    destroyExisting(canvasId);

    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(d => d.week),
        datasets: [{
          label: 'Problems Solved',
          data: data.map(d => d.problems),
          backgroundColor: 'rgba(99, 102, 241, 0.6)',
          borderColor: '#6366f1',
          borderWidth: 1,
          borderRadius: 6,
          barPercentage: 0.6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: gridColor },
            ticks: { stepSize: 1 },
          },
          x: {
            grid: { display: false },
          },
        },
        plugins: {
          legend: { display: false },
        },
      },
    });

    chartInstances.set(canvasId, chart);
    return chart;
  }

  // ── Error Trend Line ────────────────────────────────────────
  function createErrorTrend(canvasId, data) {
    const ctx = getCanvas(canvasId);
    if (!ctx) return null;
    destroyExisting(canvasId);

    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map(d => d.week),
        datasets: [{
          label: 'Errors',
          data: data.map(d => d.errors),
          borderColor: '#f87171',
          backgroundColor: 'rgba(248, 113, 113, 0.1)',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#f87171',
          pointBorderColor: '#0f172a',
          pointBorderWidth: 2,
          pointRadius: 5,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: gridColor },
          },
          x: {
            grid: { display: false },
          },
        },
        plugins: {
          legend: { display: false },
        },
      },
    });

    chartInstances.set(canvasId, chart);
    return chart;
  }

  // ── Faculty: Real-Time Error Distribution ───────────────────
  function createErrorDistribution(canvasId, data) {
    const ctx = getCanvas(canvasId);
    if (!ctx) return null;

    if (chartInstances.has(canvasId)) {
      const existing = chartInstances.get(canvasId);
      existing.data.labels = data.map(d => d.type);
      existing.data.datasets[0].data = data.map(d => d.count);
      existing.update('none'); // Update without full redraw glitch
      return existing;
    }

    const colors = [
      '#6366f1', '#00f2fe', '#a855f7', '#00f5d4',
      '#fbbf24', '#f87171', '#38bdf8', '#e879f9'
    ];

    const chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: data.map(d => d.type),
        datasets: [{
          data: data.map(d => d.count),
          backgroundColor: colors.slice(0, data.length),
          borderColor: '#080d1e',
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '58%',
        plugins: {
          legend: {
            position: 'right',
            labels: {
              boxWidth: 10,
              padding: 12,
              font: { size: 11 },
              color: '#94a3b8'
            },
          },
        },
      },
    });

    chartInstances.set(canvasId, chart);
    return chart;
  }

  // ── Faculty: Real-Time Class Performance Bar ────────────────
  function createClassPerformance(canvasId, students) {
    const ctx = getCanvas(canvasId);
    if (!ctx) return null;

    if (chartInstances.has(canvasId)) {
      const existing = chartInstances.get(canvasId);
      existing.data.labels = students.map(s => s.name ? s.name.split(' ')[0] : s.id);
      existing.data.datasets[0].data = students.map(s => s.score);
      existing.data.datasets[0].backgroundColor = students.map(s =>
        s.attention ? 'rgba(248, 113, 113, 0.7)' : 'rgba(0, 242, 254, 0.65)'
      );
      existing.data.datasets[0].borderColor = students.map(s =>
        s.attention ? '#f87171' : '#00f2fe'
      );
      existing.update('none');
      return existing;
    }

    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: students.map(s => s.name ? s.name.split(' ')[0] : s.id),
        datasets: [{
          label: 'Score (out of 10)',
          data: students.map(s => s.score),
          backgroundColor: students.map(s =>
            s.attention ? 'rgba(248, 113, 113, 0.7)' : 'rgba(0, 242, 254, 0.65)'
          ),
          borderColor: students.map(s =>
            s.attention ? '#f87171' : '#00f2fe'
          ),
          borderWidth: 1,
          borderRadius: 4,
          barPercentage: 0.7,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 10,
            grid: { color: gridColor },
            ticks: {
              stepSize: 2,
              color: '#94a3b8'
            }
          },
          x: {
            grid: { display: false },
            ticks: {
              font: { size: 10 },
              color: '#94a3b8'
            },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `Avg Score: ${context.parsed.y} / 10.0`
            }
          }
        },
      },
    });

    chartInstances.set(canvasId, chart);
    return chart;
  }

  function init() {
    setDefaults();
  }

  return {
    init,
    createProgressTimeline,
    createSuccessRate,
    createWeeklyProblems,
    createErrorTrend,
    createErrorDistribution,
    createClassPerformance,
    destroyExisting
  };
})();
