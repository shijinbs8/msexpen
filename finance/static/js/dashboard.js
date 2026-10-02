/**
 * Dashboard Chart.js Integration & Dynamic Filtering
 */

document.addEventListener('DOMContentLoaded', function () {
    const categoryCtx = document.getElementById('categoryChartCanvas');
    const incomeExpenseCtx = document.getElementById('incomeVsExpenseCanvas');
    const trendCtx = document.getElementById('spendingTrendCanvas');

    if (!categoryCtx || !incomeExpenseCtx) return;

    let categoryChart = null;
    let incomeExpenseChart = null;
    let trendChart = null;

    function fetchChartData(catPeriod = 'month', trendDays = 7) {
        fetch(`/api/dashboard-data/?cat_period=${catPeriod}&trend_days=${trendDays}`)
            .then(res => res.json())
            .then(data => {
                renderCategoryChart(data.category_chart);
                renderIncomeVsExpenseChart(data.income_vs_expense);
                if (trendCtx && data.spending_trend) {
                    renderTrendChart(data.spending_trend);
                }
            })
            .catch(err => console.error("Error fetching chart data:", err));
    }

    // --- 1. Category Doughnut Chart ---
    function renderCategoryChart(catData) {
        if (categoryChart) {
            categoryChart.destroy();
        }

        if (!catData.data || catData.data.length === 0) {
            // Empty state
            categoryCtx.getContext('2d').clearRect(0, 0, categoryCtx.width, categoryCtx.height);
            document.getElementById('categoryLegendContainer').innerHTML = '<div class="text-center text-muted p-4"><p class="mb-0">No expense data available for selected period.</p></div>';
            return;
        }

        categoryChart = new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: catData.labels,
                datasets: [{
                    data: catData.data,
                    backgroundColor: catData.colors,
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false // We render custom legend grid
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const val = context.raw || 0;
                                return ` ${context.label}: ${val.toLocaleString()} AED`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });

        // Update Legend Grid
        const legendContainer = document.getElementById('categoryLegendContainer');
        if (legendContainer && catData.items) {
            let html = '<div class="category-legend-grid">';
            catData.items.forEach(item => {
                html += `
                    <div class="cat-legend-item">
                        <span class="cat-color-dot" style="background-color: ${item.color}"></span>
                        <span>${item.icon} ${item.name}</span>
                        <strong class="ms-auto">${item.formatted_amount}</strong>
                    </div>
                `;
            });
            html += '</div>';
            legendContainer.innerHTML = html;
        }
    }

    // --- 2. Income vs Expense Bar Chart ---
    function renderIncomeVsExpenseChart(ieData) {
        if (incomeExpenseChart) {
            incomeExpenseChart.destroy();
        }

        incomeExpenseChart = new Chart(incomeExpenseCtx, {
            type: 'bar',
            data: {
                labels: ieData.labels,
                datasets: [
                    {
                        label: 'Income',
                        data: ieData.income,
                        backgroundColor: '#10b981',
                        borderRadius: 6,
                    },
                    {
                        label: 'Expenses',
                        data: ieData.expense,
                        backgroundColor: '#f43f5e',
                        borderRadius: 6,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: '#e2e8f0' }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { font: { family: 'Inter', weight: '600' } }
                    }
                }
            }
        });
    }

    // --- 3. Spending Trend Line Chart ---
    function renderTrendChart(trendData) {
        if (trendChart) {
            trendChart.destroy();
        }

        trendChart = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: trendData.labels,
                datasets: [{
                    label: 'Daily Expenses',
                    data: trendData.data,
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#4f46e5',
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // Initial load
    fetchChartData('month', 7);

    // Period Filter Listener
    const periodSelect = document.getElementById('categoryPeriodSelect');
    if (periodSelect) {
        periodSelect.addEventListener('change', function () {
            fetchChartData(this.value, 7);
        });
    }
});
