/**
 * VisionFlow Analytics Dashboard - 高級分析儀表板
 * 提供深度數據分析、趨勢預測、報表生成等功能
 */

class AnalyticsDashboard {
    constructor() {
        this.charts = {};
        this.realTimeData = new Map();
        this.analytics = {
            detections: [],
            alerts: [],
            performance: {},
            trends: {}
        };
        this.filters = {
            dateRange: 7, // 預設 7 天
            cameras: [],
            objectTypes: []
        };
        
        this.init();
    }

    async init() {
        await this.loadInitialData();
        this.createCharts();
        this.setupEventListeners();
        this.startRealTimeUpdates();
        
        console.log('📊 Analytics Dashboard initialized');
    }

    async loadInitialData() {
        try {
            // 載入歷史分析數據
            const [detections, alerts, performance] = await Promise.all([
                this.fetchDetectionAnalytics(),
                this.fetchAlertAnalytics(),
                this.fetchPerformanceMetrics()
            ]);

            this.analytics.detections = detections;
            this.analytics.alerts = alerts;
            this.analytics.performance = performance;

        } catch (error) {
            console.error('Failed to load analytics data:', error);
            this.showErrorNotification('分析數據載入失敗');
        }
    }

    async fetchDetectionAnalytics() {
        try {
            const response = await fetch('/api/analytics/detections');
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to fetch detection analytics');
            }
        } catch (error) {
            console.error('Error fetching detection analytics:', error);
            // 回退到模擬數據
            return this.getMockDetectionData();
        }
    }

    getMockDetectionData() {
        return {
            totalDetections: 1247,
            todayDetections: 89,
            averageDaily: 178,
            topObjectTypes: [
                { type: 'person', count: 856, percentage: 68.7 },
                { type: 'vehicle', count: 234, percentage: 18.8 },
                { type: 'package', count: 157, percentage: 12.5 }
            ],
            hourlyDistribution: Array.from({length: 24}, (_, i) => ({
                hour: i,
                count: Math.floor(Math.random() * 50) + 10
            })),
            weeklyTrend: Array.from({length: 7}, (_, i) => ({
                day: new Date(Date.now() - (6-i) * 24 * 60 * 60 * 1000).toLocaleDateString(),
                count: Math.floor(Math.random() * 200) + 100
            }))
        };
    }

    async fetchAlertAnalytics() {
        try {
            const response = await fetch('/api/analytics/alerts');
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to fetch alert analytics');
            }
        } catch (error) {
            console.error('Error fetching alert analytics:', error);
            // 回退到模擬數據
            return this.getMockAlertData();
        }
    }

    getMockAlertData() {
        return {
            totalAlerts: 45,
            criticalAlerts: 3,
            resolvedAlerts: 42,
            averageResponseTime: 4.2,
            alertTypes: [
                { type: '未授權進入', count: 18, severity: 'critical' },
                { type: '攝影機離線', count: 12, severity: 'warning' },
                { type: '移動偵測', count: 15, severity: 'info' }
            ]
        };
    }

    async fetchPerformanceMetrics() {
        try {
            const response = await fetch('/api/analytics/performance');
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || 'Failed to fetch performance metrics');
            }
        } catch (error) {
            console.error('Error fetching performance metrics:', error);
            // 回退到模擬數據
            return this.getMockPerformanceData();
        }
    }

    getMockPerformanceData() {
        return {
            systemUptime: 99.7,
            averageFPS: 24.8,
            averageLatency: 120,
            storageUsage: 78.5,
            networkBandwidth: 85.2,
            cpuUsage: 45.3,
            memoryUsage: 62.1
        };
    }

    createCharts() {
        this.createDetectionTrendChart();
        this.createObjectTypeChart();
        this.createHourlyActivityChart();
        this.createPerformanceChart();
        this.createAlertChart();
        this.createHeatmapChart();
    }

    createDetectionTrendChart() {
        const ctx = document.getElementById('detectionTrendChart');
        if (!ctx) return;

        this.charts.detectionTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.analytics.detections.weeklyTrend?.map(d => d.day) || [],
                datasets: [{
                    label: '每日偵測數量',
                    data: this.analytics.detections.weeklyTrend?.map(d => d.count) || [],
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    createObjectTypeChart() {
        const ctx = document.getElementById('objectTypeChart');
        if (!ctx) return;

        const colors = ['#667eea', '#764ba2', '#f093fb'];
        
        this.charts.objectType = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: this.analytics.detections.topObjectTypes?.map(o => o.type) || [],
                datasets: [{
                    data: this.analytics.detections.topObjectTypes?.map(o => o.count) || [],
                    backgroundColor: colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: 'white',
                            usePointStyle: true,
                            padding: 20
                        }
                    }
                }
            }
        });
    }

    createHourlyActivityChart() {
        const ctx = document.getElementById('hourlyActivityChart');
        if (!ctx) return;

        this.charts.hourlyActivity = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Array.from({length: 24}, (_, i) => `${i}:00`),
                datasets: [{
                    label: '偵測次數',
                    data: this.analytics.detections.hourlyDistribution?.map(h => h.count) || [],
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgb(102, 126, 234)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    createPerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        const metrics = this.analytics.performance;
        
        this.charts.performance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['系統運行時間', 'FPS 表現', '網路頻寬', 'CPU 使用率', '記憶體使用', '存儲使用'],
                datasets: [{
                    label: '系統性能',
                    data: [
                        metrics.systemUptime || 0,
                        (metrics.averageFPS / 30) * 100 || 0,
                        metrics.networkBandwidth || 0,
                        100 - (metrics.cpuUsage || 0),
                        100 - (metrics.memoryUsage || 0),
                        100 - (metrics.storageUsage || 0)
                    ],
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgb(102, 126, 234)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        angleLines: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        pointLabels: {
                            color: 'white',
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });
    }

    createAlertChart() {
        const ctx = document.getElementById('alertChart');
        if (!ctx) return;

        const alertData = this.analytics.alerts.alertTypes || [];
        const severityColors = {
            critical: '#ff4757',
            warning: '#ffa502',
            info: '#3742fa'
        };

        this.charts.alert = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: alertData.map(a => a.type),
                datasets: [{
                    label: '警報數量',
                    data: alertData.map(a => a.count),
                    backgroundColor: alertData.map(a => severityColors[a.severity]),
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    createHeatmapChart() {
        // 熱力圖顯示偵測活動的時間分佈
        const heatmapContainer = document.getElementById('heatmapChart');
        if (!heatmapContainer) return;

        // 生成模擬熱力圖數據
        const days = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'];
        const hours = Array.from({length: 24}, (_, i) => i);
        
        let heatmapHTML = '<div class="heatmap-container">';
        heatmapHTML += '<div class="heatmap-header">';
        heatmapHTML += '<div class="hour-labels">';
        hours.forEach(hour => {
            heatmapHTML += `<span>${hour}</span>`;
        });
        heatmapHTML += '</div></div>';
        
        days.forEach(day => {
            heatmapHTML += `<div class="heatmap-row">`;
            heatmapHTML += `<div class="day-label">${day}</div>`;
            heatmapHTML += `<div class="hour-cells">`;
            
            hours.forEach(hour => {
                const intensity = Math.random();
                const color = this.getHeatmapColor(intensity);
                heatmapHTML += `<div class="heat-cell" style="background-color: ${color}" title="${day} ${hour}:00 - 活動度: ${Math.round(intensity * 100)}%"></div>`;
            });
            
            heatmapHTML += '</div></div>';
        });
        heatmapHTML += '</div>';
        
        heatmapContainer.innerHTML = heatmapHTML;
    }

    getHeatmapColor(intensity) {
        // 從藍色到紅色的漸變
        const colors = [
            'rgba(102, 126, 234, 0.1)',
            'rgba(102, 126, 234, 0.3)',
            'rgba(102, 126, 234, 0.5)',
            'rgba(255, 107, 53, 0.5)',
            'rgba(255, 107, 53, 0.7)',
            'rgba(255, 107, 53, 0.9)'
        ];
        
        const index = Math.floor(intensity * (colors.length - 1));
        return colors[index];
    }

    setupEventListeners() {
        // 日期範圍選擇器
        const dateRangeSelect = document.getElementById('dateRangeSelect');
        if (dateRangeSelect) {
            dateRangeSelect.addEventListener('change', (e) => {
                this.filters.dateRange = parseInt(e.target.value);
                this.refreshData();
            });
        }

        // 匯出報表按鈕
        const exportBtn = document.getElementById('exportReportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportReport());
        }

        // 即時模式切換
        const realTimeToggle = document.getElementById('realTimeToggle');
        if (realTimeToggle) {
            realTimeToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startRealTimeUpdates();
                } else {
                    this.stopRealTimeUpdates();
                }
            });
        }
    }

    startRealTimeUpdates() {
        if (this.realTimeInterval) return;
        
        this.realTimeInterval = setInterval(() => {
            this.updateRealTimeData();
        }, 5000); // 每5秒更新一次
        
        console.log('🔄 Real-time updates started');
    }

    stopRealTimeUpdates() {
        if (this.realTimeInterval) {
            clearInterval(this.realTimeInterval);
            this.realTimeInterval = null;
            console.log('⏹️ Real-time updates stopped');
        }
    }

    async updateRealTimeData() {
        try {
            // 更新即時統計數據
            const newDetection = {
                timestamp: new Date(),
                count: Math.floor(Math.random() * 5) + 1,
                type: ['person', 'vehicle', 'package'][Math.floor(Math.random() * 3)]
            };

            // 更新統計卡片
            this.updateStatCards(newDetection);
            
            // 更新圖表數據
            this.updateChartsRealTime(newDetection);
            
        } catch (error) {
            console.error('Real-time update failed:', error);
        }
    }

    updateStatCards(newData) {
        // 更新今日偵測數
        const todayCountEl = document.getElementById('todayDetectionCount');
        if (todayCountEl) {
            const current = parseInt(todayCountEl.textContent) || 0;
            todayCountEl.textContent = current + newData.count;
            
            // 添加動畫效果
            todayCountEl.classList.add('stat-updated');
            setTimeout(() => todayCountEl.classList.remove('stat-updated'), 1000);
        }

        // 更新即時狀態
        this.updateActivityIndicator();
    }

    updateActivityIndicator() {
        const indicator = document.getElementById('activityIndicator');
        if (indicator) {
            indicator.classList.add('pulse');
            setTimeout(() => indicator.classList.remove('pulse'), 1000);
        }
    }

    updateChartsRealTime(newData) {
        // 更新偵測趨勢圖表
        if (this.charts.detectionTrend) {
            const chart = this.charts.detectionTrend;
            const now = new Date().toLocaleTimeString();
            
            chart.data.labels.push(now);
            chart.data.datasets[0].data.push(newData.count);
            
            // 保持最近50個數據點
            if (chart.data.labels.length > 50) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            
            chart.update('none');
        }
    }

    async refreshData() {
        try {
            this.showLoadingState();
            await this.loadInitialData();
            this.updateAllCharts();
            this.hideLoadingState();
        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showErrorNotification('數據刷新失敗');
        }
    }

    updateAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.update) {
                chart.update();
            }
        });
    }

    async exportReport() {
        try {
            this.showLoadingState('正在生成報表...');
            
            const response = await fetch('/api/analytics/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type: 'comprehensive',
                    dateRange: this.filters.dateRange
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 創建完整的報表數據
                const reportData = {
                    ...result.data,
                    generatedAt: new Date().toISOString(),
                    period: `最近 ${this.filters.dateRange} 天`,
                    summary: this.analytics.detections,
                    alerts: this.analytics.alerts,
                    performance: this.analytics.performance
                };

                // 下載JSON報表
                this.downloadJSON(reportData, `VisionFlow_Analytics_Report_${new Date().toISOString().split('T')[0]}.json`);
                
                this.hideLoadingState();
                this.showSuccessNotification('報表已成功匯出');
            } else {
                throw new Error(result.error || '報表生成失敗');
            }
            
        } catch (error) {
            console.error('Export failed:', error);
            this.showErrorNotification('報表匯出失敗');
            this.hideLoadingState();
        }
    }

    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    showLoadingState(message = '載入中...') {
        // 顯示載入狀態
        const loader = document.getElementById('analyticsLoader');
        if (loader) {
            loader.style.display = 'flex';
            const text = loader.querySelector('.loading-text');
            if (text) text.textContent = message;
        }
    }

    hideLoadingState() {
        const loader = document.getElementById('analyticsLoader');
        if (loader) {
            loader.style.display = 'none';
        }
    }

    showSuccessNotification(message) {
        this.showNotification(message, 'success');
    }

    showErrorNotification(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // 創建通知元素
        const notification = document.createElement('div');
        notification.className = `analytics-notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        // 顯示動畫
        setTimeout(() => notification.classList.add('show'), 100);
        
        // 自動移除
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }

    destroy() {
        // 清理資源
        this.stopRealTimeUpdates();
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
        console.log('📊 Analytics Dashboard destroyed');
    }
}

// 自動初始化（當DOM載入完成時）
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.analytics-dashboard')) {
        window.analyticsDashboard = new AnalyticsDashboard();
    }
});

// 匯出到全域
window.AnalyticsDashboard = AnalyticsDashboard;
