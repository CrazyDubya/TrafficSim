/**
 * Traffic Simulation Charts Controller
 * Handles real-time charting of simulation data using Chart.js
 */

class ChartsController {
    constructor() {
        this.speedChart = null;
        this.flowChart = null;
        
        this.maxDataPoints = 100; // Keep last 100 data points
        this.updateInterval = 1000; // Update charts every 1 second
        this.lastUpdateTime = 0;
        
        this.data = {
            time: [],
            averageSpeed: [],
            totalFlow: [],
            density: [],
            vehicleCount: []
        };
        
        this.init();
    }
    
    init() {
        this.initializeCharts();
    }
    
    initializeCharts() {
        // Speed vs Time Chart
        const speedCtx = document.getElementById('speed-chart').getContext('2d');
        this.speedChart = new Chart(speedCtx, {
            type: 'line',
            data: {
                labels: this.data.time,
                datasets: [{
                    label: 'Average Speed (m/s)',
                    data: this.data.averageSpeed,
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time (s)'
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Speed (m/s)'
                        },
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
        
        // Flow vs Time Chart
        const flowCtx = document.getElementById('flow-chart').getContext('2d');
        this.flowChart = new Chart(flowCtx, {
            type: 'line',
            data: {
                labels: this.data.time,
                datasets: [
                    {
                        label: 'Traffic Flow (veh/h)',
                        data: this.data.totalFlow,
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Vehicle Count',
                        data: this.data.vehicleCount,
                        borderColor: '#FF9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time (s)'
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Flow (veh/h)'
                        },
                        beginAtZero: true
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Vehicle Count'
                        },
                        beginAtZero: true,
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
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
    
    updateCharts(simulationData) {
        const currentTime = Date.now();
        
        // Throttle updates to avoid overwhelming the charts
        if (currentTime - this.lastUpdateTime < this.updateInterval) {
            return;
        }
        
        this.lastUpdateTime = currentTime;
        
        if (!simulationData.stats) {
            return;
        }
        
        const stats = simulationData.stats;
        const timeLabel = stats.current_time.toFixed(1);
        
        // Add new data point
        this.data.time.push(timeLabel);
        this.data.averageSpeed.push(stats.average_speed);
        this.data.totalFlow.push(stats.total_flow);
        this.data.density.push(stats.average_density);
        this.data.vehicleCount.push(stats.active_vehicles);
        
        // Limit data points to avoid memory issues
        if (this.data.time.length > this.maxDataPoints) {
            this.data.time.shift();
            this.data.averageSpeed.shift();
            this.data.totalFlow.shift();
            this.data.density.shift();
            this.data.vehicleCount.shift();
        }
        
        // Update chart data
        this.speedChart.data.labels = [...this.data.time];
        this.speedChart.data.datasets[0].data = [...this.data.averageSpeed];
        
        this.flowChart.data.labels = [...this.data.time];
        this.flowChart.data.datasets[0].data = [...this.data.totalFlow];
        this.flowChart.data.datasets[1].data = [...this.data.vehicleCount];
        
        // Update charts
        this.speedChart.update('none'); // Use 'none' for better performance
        this.flowChart.update('none');
    }
    
    clearCharts() {
        // Clear all data
        this.data.time = [];
        this.data.averageSpeed = [];
        this.data.totalFlow = [];
        this.data.density = [];
        this.data.vehicleCount = [];
        
        // Update chart data
        this.speedChart.data.labels = [];
        this.speedChart.data.datasets[0].data = [];
        
        this.flowChart.data.labels = [];
        this.flowChart.data.datasets[0].data = [];
        this.flowChart.data.datasets[1].data = [];
        
        // Update charts
        this.speedChart.update();
        this.flowChart.update();
    }
    
    addDensityChart() {
        // Add a third chart for density if needed
        const chartContainer = document.querySelector('.charts-container');
        
        if (document.getElementById('density-chart')) {
            return; // Chart already exists
        }
        
        // Create new chart panel
        const chartPanel = document.createElement('div');
        chartPanel.className = 'chart-panel';
        chartPanel.innerHTML = `
            <h4>Density vs Time</h4>
            <canvas id="density-chart" width="400" height="200"></canvas>
        `;
        
        chartContainer.appendChild(chartPanel);
        
        // Initialize density chart
        const densityCtx = document.getElementById('density-chart').getContext('2d');
        this.densityChart = new Chart(densityCtx, {
            type: 'line',
            data: {
                labels: this.data.time,
                datasets: [{
                    label: 'Average Density (veh/km)',
                    data: this.data.density,
                    borderColor: '#9C27B0',
                    backgroundColor: 'rgba(156, 39, 176, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time (s)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Density (veh/km)'
                        },
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
        
        // Update grid layout for 3 charts
        chartContainer.style.gridTemplateColumns = 'repeat(3, 1fr)';
    }
    
    exportChartData() {
        // Export chart data as CSV
        const csvData = [
            ['Time (s)', 'Average Speed (m/s)', 'Traffic Flow (veh/h)', 'Density (veh/km)', 'Vehicle Count']
        ];
        
        for (let i = 0; i < this.data.time.length; i++) {
            csvData.push([
                this.data.time[i],
                this.data.averageSpeed[i],
                this.data.totalFlow[i],
                this.data.density[i],
                this.data.vehicleCount[i]
            ]);
        }
        
        const csvContent = csvData.map(row => row.join(',')).join('\n');
        
        // Create download link
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'traffic_simulation_data.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
    
    getStatistics() {
        // Calculate basic statistics from current data
        if (this.data.averageSpeed.length === 0) {
            return null;
        }
        
        const avgSpeed = this.data.averageSpeed.reduce((a, b) => a + b, 0) / this.data.averageSpeed.length;
        const maxSpeed = Math.max(...this.data.averageSpeed);
        const minSpeed = Math.min(...this.data.averageSpeed);
        
        const avgFlow = this.data.totalFlow.reduce((a, b) => a + b, 0) / this.data.totalFlow.length;
        const maxFlow = Math.max(...this.data.totalFlow);
        
        const avgDensity = this.data.density.reduce((a, b) => a + b, 0) / this.data.density.length;
        const maxDensity = Math.max(...this.data.density);
        
        return {
            speed: {
                average: avgSpeed.toFixed(2),
                maximum: maxSpeed.toFixed(2),
                minimum: minSpeed.toFixed(2)
            },
            flow: {
                average: avgFlow.toFixed(0),
                maximum: maxFlow.toFixed(0)
            },
            density: {
                average: avgDensity.toFixed(2),
                maximum: maxDensity.toFixed(2)
            }
        };
    }
    
    showStatistics() {
        const stats = this.getStatistics();
        if (!stats) {
            alert('No data available for statistics');
            return;
        }
        
        const message = `
Traffic Statistics:

Speed:
- Average: ${stats.speed.average} m/s
- Maximum: ${stats.speed.maximum} m/s
- Minimum: ${stats.speed.minimum} m/s

Flow:
- Average: ${stats.flow.average} veh/h
- Maximum: ${stats.flow.maximum} veh/h

Density:
- Average: ${stats.density.average} veh/km
- Maximum: ${stats.density.maximum} veh/km
        `;
        
        alert(message);
    }
}

// Initialize the charts controller when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chartsController = new ChartsController();
    
    // Add export button functionality if it exists
    const exportBtn = document.getElementById('export-data-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            window.chartsController.exportChartData();
        });
    }
    
    // Add statistics button functionality if it exists
    const statsBtn = document.getElementById('show-stats-btn');
    if (statsBtn) {
        statsBtn.addEventListener('click', () => {
            window.chartsController.showStatistics();
        });
    }
});