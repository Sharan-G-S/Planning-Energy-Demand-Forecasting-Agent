// Energy Demand Forecasting Agent - Frontend JavaScript

const API_BASE = '';

// State
let currentForecastHours = 24;
let charts = {};
let updateInterval = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    console.log('Energy Demand Forecasting Agent initialized');
    initializeApp();
});

async function initializeApp() {
    // Load initial data
    await Promise.all([
        loadStats(),
        loadHistoricalData(),
        loadForecast(24),
        loadOptimization(),
        loadAnomalies()
    ]);

    // Set up event listeners
    setupEventListeners();

    // Auto-refresh every 30 seconds
    updateInterval = setInterval(() => {
        refreshDashboard();
    }, 30000);
}

function setupEventListeners() {
    // Forecast buttons
    document.querySelectorAll('.forecast-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const hours = parseInt(e.target.dataset.hours);
            selectForecastPeriod(hours);
        });
    });

    // Refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDashboard);
    }

    // Export button
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportData);
    }
}

async function selectForecastPeriod(hours) {
    currentForecastHours = hours;

    // Update button states
    document.querySelectorAll('.forecast-btn').forEach(btn => {
        btn.classList.remove('active');
        if (parseInt(btn.dataset.hours) === hours) {
            btn.classList.add('active');
        }
    });

    // Load new forecast
    await loadForecast(hours);
}

async function refreshDashboard() {
    console.log('Refreshing dashboard...');
    await Promise.all([
        loadStats(),
        loadHistoricalData(),
        loadForecast(currentForecastHours),
        loadOptimization(),
        loadAnomalies()
    ]);
}

// API Calls
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data = await response.json();

        if (data.success) {
            updateStatsDisplay(data);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadHistoricalData(days = 7) {
    try {
        const response = await fetch(`${API_BASE}/api/historical?days=${days}`);
        const data = await response.json();

        if (data.success) {
            updateHistoricalChart(data.data);
        }
    } catch (error) {
        console.error('Error loading historical data:', error);
    }
}

async function loadForecast(hours) {
    try {
        const response = await fetch(`${API_BASE}/api/predict?hours=${hours}`);
        const data = await response.json();

        if (data.success) {
            updateForecastChart(data.predictions);
            updateForecastSummary(data.summary);
        }
    } catch (error) {
        console.error('Error loading forecast:', error);
    }
}

async function loadOptimization() {
    try {
        const response = await fetch(`${API_BASE}/api/optimize?hours=24`);
        const data = await response.json();

        if (data.success) {
            updateRecommendations(data.recommendations);
            updateCostAnalysis(data.cost_analysis);
        }
    } catch (error) {
        console.error('Error loading optimization:', error);
    }
}

async function loadAnomalies() {
    try {
        const response = await fetch(`${API_BASE}/api/anomalies?days=7`);
        const data = await response.json();

        if (data.success) {
            updateAnomalyAlerts(data.alerts);
        }
    } catch (error) {
        console.error('Error loading anomalies:', error);
    }
}

// Update UI Functions
function updateStatsDisplay(data) {
    // Current demand
    const currentDemand = document.getElementById('currentDemand');
    if (currentDemand) {
        currentDemand.textContent = formatNumber(data.current.demand) + ' MW';
    }

    // Grid status
    const gridStatus = document.getElementById('gridStatus');
    if (gridStatus) {
        const status = data.grid_status.status;
        gridStatus.innerHTML = `
            <span class="status-badge ${status}">
                <span class="status-dot"></span>
                ${status.toUpperCase()}
            </span>
        `;
    }

    // Load factor
    const loadFactor = document.getElementById('loadFactor');
    if (loadFactor) {
        loadFactor.textContent = (data.grid_status.load_factor * 100).toFixed(1) + '%';
    }

    // Available capacity
    const availableCapacity = document.getElementById('availableCapacity');
    if (availableCapacity) {
        availableCapacity.textContent = formatNumber(data.grid_status.available_capacity) + ' MW';
    }

    // 24h average
    const avg24h = document.getElementById('avg24h');
    if (avg24h) {
        avg24h.textContent = formatNumber(data.last_24h.avg_demand) + ' MW';
    }

    // 24h peak
    const peak24h = document.getElementById('peak24h');
    if (peak24h) {
        peak24h.textContent = formatNumber(data.last_24h.max_demand) + ' MW';
    }
}

function updateHistoricalChart(data) {
    const ctx = document.getElementById('historicalChart');
    if (!ctx) return;

    const labels = data.map(d => new Date(d.timestamp).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit'
    }));
    const values = data.map(d => d.energy_demand);

    if (charts.historical) {
        charts.historical.destroy();
    }

    charts.historical = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Energy Demand (MW)',
                data: values,
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(30, 41, 59, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#6366f1',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        maxTicksLimit: 12
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function (value) {
                            return value.toLocaleString() + ' MW';
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

function updateForecastChart(predictions) {
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return;

    const labels = predictions.map(p => new Date(p.timestamp).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit'
    }));
    const values = predictions.map(p => p.predicted_demand);
    const lowerBounds = predictions.map(p => p.lower_bound);
    const upperBounds = predictions.map(p => p.upper_bound);

    if (charts.forecast) {
        charts.forecast.destroy();
    }

    charts.forecast = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Predicted Demand',
                    data: values,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: 'Upper Bound',
                    data: upperBounds,
                    borderColor: 'rgba(245, 158, 11, 0.5)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: '+1',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                    pointRadius: 0
                },
                {
                    label: 'Lower Bound',
                    data: lowerBounds,
                    borderColor: 'rgba(245, 158, 11, 0.5)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#cbd5e1',
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(30, 41, 59, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#06b6d4',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        maxTicksLimit: 12
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function (value) {
                            return value.toLocaleString() + ' MW';
                        }
                    }
                }
            }
        }
    });
}

function updateForecastSummary(summary) {
    const avgForecast = document.getElementById('avgForecast');
    if (avgForecast) {
        avgForecast.textContent = formatNumber(summary.avg_demand) + ' MW';
    }

    const peakForecast = document.getElementById('peakForecast');
    if (peakForecast) {
        peakForecast.textContent = formatNumber(summary.max_demand) + ' MW';
    }

    const confidence = document.getElementById('confidence');
    if (confidence) {
        confidence.textContent = summary.avg_confidence.toFixed(1) + '%';
    }
}

function updateRecommendations(recommendations) {
    const container = document.getElementById('recommendationsList');
    if (!container) return;

    if (recommendations.length === 0) {
        container.innerHTML = '<p class="text-center" style="color: var(--text-muted);">No recommendations at this time</p>';
        return;
    }

    container.innerHTML = recommendations.map(rec => `
        <div class="recommendation-item ${rec.priority}">
            <div class="recommendation-header">
                <span class="recommendation-title">${rec.title}</span>
                <span class="recommendation-priority" style="background: ${getPriorityColor(rec.priority)}">${rec.priority}</span>
            </div>
            <p class="recommendation-description">${rec.description}</p>
            <p class="recommendation-action">💡 ${rec.action}</p>
            ${rec.estimated_impact ? `<p class="recommendation-action">📊 Impact: ${rec.estimated_impact}</p>` : ''}
        </div>
    `).join('');
}

function updateCostAnalysis(analysis) {
    const savings = document.getElementById('potentialSavings');
    if (savings) {
        savings.textContent = '$' + formatNumber(analysis.potential_savings);
    }
}

function updateAnomalyAlerts(alerts) {
    const container = document.getElementById('anomalyAlerts');
    if (!container) return;

    if (alerts.length === 0) {
        container.innerHTML = '<p class="text-center" style="color: var(--text-muted);">No anomalies detected</p>';
        return;
    }

    container.innerHTML = alerts.slice(0, 5).map(alert => `
        <div class="alert-item ${alert.severity}">
            <div class="alert-header">
                <span class="alert-type">${alert.type.replace('_', ' ')}</span>
                <span class="alert-time">${formatTimestamp(alert.timestamp)}</span>
            </div>
            <p class="alert-message">${alert.message}</p>
            <p class="recommendation-action">💡 ${alert.recommendation}</p>
        </div>
    `).join('');
}

// Utility Functions
function formatNumber(num) {
    return Math.round(num).toLocaleString();
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getPriorityColor(priority) {
    const colors = {
        'high': 'rgba(239, 68, 68, 0.2)',
        'medium': 'rgba(245, 158, 11, 0.2)',
        'low': 'rgba(16, 185, 129, 0.2)'
    };
    return colors[priority] || colors.medium;
}

function exportData() {
    // Export current forecast data as CSV
    console.log('Exporting data...');
    alert('Export functionality - Data would be downloaded as CSV');
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }

    // Destroy charts
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
});
