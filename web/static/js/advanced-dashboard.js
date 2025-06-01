/**
 * VisionFlow Real-time Monitoring Dashboard
 * Advanced WebSocket-based dashboard with modern UI/UX
 */

class VisionFlowAdvancedDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.isConnected = false;
        this.retryCount = 0;
        this.maxRetries = 5;
        this.updateInterval = null;
        this.notifications = [];
        
        this.init();
    }

    async init() {
        this.showLoadingScreen();
        await this.initializeSocket();
        this.initializeCharts();
        this.initializeUI();
        this.setupEventListeners();
        this.startPeriodicUpdates();
        this.hideLoadingScreen();
    }

    showLoadingScreen() {
        const loadingHTML = `
            <div id="loading-screen" class="loading-screen">
                <div class="loading-content">
                    <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;"></div>
                    <h4 class="mt-3">正在初始化 VisionFlow 系統</h4>
                    <p class="text-muted">正在連接監控服務...</p>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('afterbegin', loadingHTML);
    }

    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.style.opacity = '0';
            setTimeout(() => loadingScreen.remove(), 500);
        }
    }

    async initializeSocket() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true,
                reconnection: true,
                reconnectionAttempts: this.maxRetries,
                reconnectionDelay: 1000,
                timeout: 5000
            });

            this.socket.on('connect', () => {
                console.log('✅ VisionFlow 連接成功');
                this.isConnected = true;
                this.retryCount = 0;
                this.showNotification('系統連接成功', 'success');
                this.socket.emit('join_room', { room: 'dashboard' });
            });

            this.socket.on('disconnect', () => {
                console.log('❌ VisionFlow 連接斷開');
                this.isConnected = false;
                this.showNotification('連接已斷開，正在重新連接...', 'warning');
            });

            this.socket.on('reconnect', () => {
                console.log('🔄 VisionFlow 重新連接成功');
                this.showNotification('重新連接成功', 'success');
            });

            // 實時數據監聽
            this.socket.on('detection_update', (data) => {
                this.handleDetectionUpdate(data);
            });

            this.socket.on('alert_update', (data) => {
                this.handleAlertUpdate(data);
            });

            this.socket.on('system_status', (data) => {
                this.handleSystemStatusUpdate(data);
            });

            this.socket.on('camera_status', (data) => {
                this.handleCameraStatusUpdate(data);
            });

        } catch (error) {
            console.error('Socket 初始化失败:', error);
            this.showNotification('連接初始化失敗', 'error');
        }
    }

    initializeCharts() {
        // 初始化檢測趨勢圖表
        this.initDetectionTrendChart();
        
        // 初始化檢測類型分布圖
        this.initDetectionTypeChart();
        
        // 初始化系統效能圖表
        this.initSystemPerformanceChart();
        
        // 初始化攝影機狀態圖表
        this.initCameraStatusChart();
    }

    initDetectionTrendChart() {
        const ctx = document.getElementById('detectionTrendChart')?.getContext('2d');
        if (!ctx) return;

        this.charts.detectionTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '檢測數量',
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: '警報數量',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: '檢測與警報趨勢 (過去24小時)'
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
                },
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    initDetectionTypeChart() {
        const ctx = document.getElementById('detectionTypeChart')?.getContext('2d');
        if (!ctx) return;

        this.charts.detectionType = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['人員', '車輛', '動物', '包裹', '其他'],
                datasets: [{
                    data: [45, 25, 15, 10, 5],
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    title: {
                        display: true,
                        text: '檢測類型分布'
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1000
                }
            }
        });
    }

    initSystemPerformanceChart() {
        const ctx = document.getElementById('systemPerformanceChart')?.getContext('2d');
        if (!ctx) return;

        this.charts.systemPerformance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['CPU使用率', '記憶體使用率', '磁碟使用率', '網路IO', '處理佇列', 'FPS平均'],
                datasets: [{
                    label: '系統效能',
                    data: [65, 70, 45, 80, 20, 95],
                    borderColor: 'rgb(255, 206, 86)',
                    backgroundColor: 'rgba(255, 206, 86, 0.2)',
                    pointBackgroundColor: 'rgb(255, 206, 86)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(255, 206, 86)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '系統效能監控'
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
                        }
                    }
                }
            }
        });
    }

    initCameraStatusChart() {
        const ctx = document.getElementById('cameraStatusChart')?.getContext('2d');
        if (!ctx) return;

        this.charts.cameraStatus = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: '今日檢測數量',
                    data: [],
                    backgroundColor: function(context) {
                        const value = context.parsed.y;
                        if (value > 80) return '#28a745';
                        if (value > 50) return '#ffc107';
                        return '#dc3545';
                    },
                    borderRadius: 5,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '攝影機檢測統計'
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

    initializeUI() {
        // 初始化標籤頁切換
        this.initTabSwitching();
        
        // 初始化通知系統
        this.initNotificationSystem();
        
        // 初始化攝影機網格
        this.initCameraGrid();
        
        // 初始化設定面板
        this.initSettingsPanel();
    }

    initTabSwitching() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;
                
                // 移除所有活動狀態
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // 添加當前標籤的活動狀態
                button.classList.add('active');
                document.getElementById(targetTab).classList.add('active');
                
                // 如果切換到圖表標籤，重新調整圖表大小
                if (targetTab === 'dashboard') {
                    setTimeout(() => {
                        Object.values(this.charts).forEach(chart => {
                            if (chart && chart.resize) {
                                chart.resize();
                            }
                        });
                    }, 100);
                }
            });
        });
    }

    initNotificationSystem() {
        // 創建通知容器
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
    }

    initCameraGrid() {
        const cameraGrid = document.getElementById('camera-grid');
        if (cameraGrid) {
            this.loadCameraData();
        }
    }

    initSettingsPanel() {
        // 初始化設定面板的各種控制項
        this.initThemeToggle();
        this.initNotificationSettings();
        this.initSystemSettings();
    }

    initThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('change', (e) => {
                const theme = e.target.checked ? 'dark' : 'light';
                this.setTheme(theme);
            });
        }
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('visionflow-theme', theme);
    }

    setupEventListeners() {
        // 窗口大小變化時重新調整圖表
        window.addEventListener('resize', () => {
            setTimeout(() => {
                Object.values(this.charts).forEach(chart => {
                    if (chart && chart.resize) {
                        chart.resize();
                    }
                });
            }, 100);
        });

        // 頁面可見性變化處理
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
    }

    startPeriodicUpdates() {
        this.updateInterval = setInterval(() => {
            if (this.isConnected) {
                this.fetchLatestData();
            }
        }, 5000); // 每5秒更新一次
    }

    pauseUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    resumeUpdates() {
        if (!this.updateInterval) {
            this.startPeriodicUpdates();
        }
    }

    async fetchLatestData() {
        try {
            const [analytics, alerts, cameras, performance] = await Promise.all([
                fetch('/api/analytics/summary').then(r => r.json()),
                fetch('/api/alerts/active').then(r => r.json()),
                fetch('/api/cameras/status').then(r => r.json()),
                fetch('/api/system/performance').then(r => r.json())
            ]);

            this.updateDashboardStats(analytics);
            this.updateAlertsDisplay(alerts);
            this.updateCamerasDisplay(cameras);
            this.updateSystemPerformance(performance);

        } catch (error) {
            console.error('獲取數據失敗:', error);
            this.showNotification('數據更新失敗', 'error');
        }
    }

    updateDashboardStats(data) {
        // 更新統計卡片
        this.updateStatCard('total-detections', data.total_detections);
        this.updateStatCard('active-cameras', data.active_cameras);
        this.updateStatCard('alerts-today', data.alerts_today);
        this.updateStatCard('system-uptime', data.system_uptime);
    }

    updateStatCard(id, value) {
        const element = document.getElementById(id);
        if (element) {
            const oldValue = element.textContent;
            if (oldValue !== value.toString()) {
                element.style.transform = 'scale(1.1)';
                element.textContent = value;
                setTimeout(() => {
                    element.style.transform = 'scale(1)';
                }, 200);
            }
        }
    }

    handleDetectionUpdate(data) {
        // 處理實時檢測更新
        this.updateDetectionTrendChart(data);
        this.showNotification(`新檢測: ${data.type} 在 ${data.camera_id}`, 'info');
    }

    handleAlertUpdate(data) {
        // 處理警報更新
        this.showNotification(`⚠️ ${data.type}: ${data.description}`, 'warning');
        this.updateAlertsCount();
    }

    handleSystemStatusUpdate(data) {
        // 處理系統狀態更新
        this.updateSystemPerformanceChart(data);
    }

    handleCameraStatusUpdate(data) {
        // 處理攝影機狀態更新
        this.updateCameraGrid(data);
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        container.appendChild(notification);

        // 添加關閉事件
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.removeNotification(notification);
        });

        // 自動移除
        setTimeout(() => {
            this.removeNotification(notification);
        }, 5000);

        // 添加動畫
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
    }

    removeNotification(notification) {
        notification.classList.add('hide');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    async loadCameraData() {
        try {
            const response = await fetch('/api/cameras/status');
            const data = await response.json();
            this.updateCameraGrid(data.cameras);
        } catch (error) {
            console.error('載入攝影機數據失敗:', error);
            this.showNotification('攝影機數據載入失敗', 'error');
        }
    }

    updateCameraGrid(cameras) {
        const grid = document.getElementById('camera-grid');
        if (!grid || !cameras) return;

        grid.innerHTML = cameras.map(camera => `
            <div class="camera-card ${camera.status}" data-camera-id="${camera.id}">
                <div class="camera-header">
                    <h6>${camera.name}</h6>
                    <span class="status-indicator ${camera.status}"></span>
                </div>
                <div class="camera-preview">
                    <img src="${camera.stream_url}" alt="${camera.name}" 
                         onerror="this.src='/static/images/camera-placeholder.png'">
                </div>
                <div class="camera-info">
                    <small>位置: ${camera.location}</small>
                    <small>今日檢測: ${camera.detection_count_today}</small>
                </div>
            </div>
        `).join('');
    }

    destroy() {
        // 清理資源
        if (this.socket) {
            this.socket.disconnect();
        }
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
    }
}

// 初始化儀表板
document.addEventListener('DOMContentLoaded', () => {
    window.visionFlowDashboard = new VisionFlowAdvancedDashboard();
});

// 清理資源
window.addEventListener('beforeunload', () => {
    if (window.visionFlowDashboard) {
        window.visionFlowDashboard.destroy();
    }
});
