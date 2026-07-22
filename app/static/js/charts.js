/* PROFILE SHIELD AI - Interactive Charting & Visual Analytics Suite */

// Render Trust Radar Chart
function renderTrustRadar(canvasId, radarData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !radarData) return;

    const labels = Object.keys(radarData);
    const values = Object.values(radarData);

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Trust Intelligence Profile Vector',
                data: values,
                backgroundColor: 'rgba(99, 102, 241, 0.25)',
                borderColor: '#6366f1',
                borderWidth: 2.5,
                pointBackgroundColor: '#a855f7',
                pointBorderColor: '#fff',
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.15)' },
                    grid: { color: 'rgba(255, 255, 255, 0.15)' },
                    pointLabels: {
                        color: '#94a3b8',
                        font: { size: 12, family: 'Inter', weight: '600' }
                    },
                    suggestedMin: 0,
                    suggestedMax: 100,
                    ticks: { display: false }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// Render Dual Profile Trust Radar Comparison Overlay
function renderCompareRadar(canvasId, radar1, name1, radar2, name2) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !radar1 || !radar2) return;

    const labels = Object.keys(radar1);

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: `@${name1}`,
                    data: Object.values(radar1),
                    backgroundColor: 'rgba(99, 102, 241, 0.25)',
                    borderColor: '#6366f1',
                    borderWidth: 2
                },
                {
                    label: `@${name2}`,
                    data: Object.values(radar2),
                    backgroundColor: 'rgba(236, 72, 153, 0.25)',
                    borderColor: '#ec4899',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.15)' },
                    grid: { color: 'rgba(255, 255, 255, 0.15)' },
                    pointLabels: { color: '#94a3b8', font: { size: 11 } },
                    suggestedMin: 0,
                    suggestedMax: 100,
                    ticks: { display: false }
                }
            },
            plugins: {
                legend: { labels: { color: '#f8fafc' } }
            }
        }
    });
}

// Render SHAP Feature Importance Bar Chart
function renderShapChart(canvasId, shapData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !shapData || !Array.isArray(shapData)) return;

    const topShap = shapData.slice(0, 8);
    const labels = topShap.map(item => item.display_name);
    const values = topShap.map(item => item.importance);
    const bgColors = topShap.map(item => item.importance > 0 ? '#ef4444' : '#22c55e');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'SHAP Risk Contribution',
                data: values,
                backgroundColor: bgColors,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#f8fafc', font: { size: 11 } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const val = context.raw;
                            return val > 0 ? `+${val} (Increases Anomaly Risk)` : `${val} (Increases Trust)`;
                        }
                    }
                }
            }
        }
    });
}

// Render Dashboard Doughnut Chart
function renderDashboardRiskDoughnut(canvasId, low, mod, high, crit) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low Risk', 'Moderate Risk', 'High Risk', 'Critical Risk'],
            datasets: [{
                data: [low || 0, mod || 0, high || 0, crit || 0],
                backgroundColor: ['#22c55e', '#eab308', '#f97316', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 15 } }
            }
        }
    });
}

// Render Trust Gauge helper
function renderTrustGauge(gaugeFillId, trustScore) {
    const fillEl = document.getElementById(gaugeFillId);
    if (!fillEl) return;
    const circumference = 408;
    const offset = circumference - (circumference * Math.min(100, Math.max(0, trustScore)) / 100);
    fillEl.style.strokeDashoffset = offset;
}

// Render Heatmap Helper
function renderHeatmap(heatmapContainerId, matrixData) {
    const container = document.getElementById(heatmapContainerId);
    if (!container || !matrixData) return;
    // Interactive heatmap hover triggers can be bound here
}
