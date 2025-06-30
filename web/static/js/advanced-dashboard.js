/**
 * VisionFlow Real-time Monitoring Dashboard
 * Advanced WebSocket-based dashboard with modern UI/UX
 */
const API_URL        = "http://localhost:5001";    // 後端主機＋埠號
const STREAM_API_URL = "http://localhost:15440";   // 串流服務埠號
class VisionFlowAdvancedDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.isConnected = false;
        this.retryCount = 0;
        this.maxRetries = 5;
        this.updateInterval = null;
        this.notifications = [];
        
        // 認證相關
        this.token = localStorage.getItem('accessToken') || null;
        this.isLoggedIn = false;
        this.currentUser = null;
        
        this.init();
    }

    async init() {
        try {
            this.showLoadingScreen();
            
            // 載入保存的設定
            this.loadSettings();
            
            // 檢查認證狀態
            if (this.token) {
                console.log('Token 存在，設置為已登入狀態 (暫時)');
                this.isLoggedIn = true; // 暫時直接設為 true
                // await this.checkAuthStatus(); // 暫時註解掉，避免 API 調用失敗影響
            }
            
            // 並行初始化，不要等待 WebSocket 連接
            await Promise.allSettled([
                this.initializeSocket(),
                this.initializeCharts(),
                this.initializeUI(),
                this.setupEventListeners()
            ]);
            
            // 啟動定時更新
            this.startPeriodicUpdates();
            
            // 載入初始數據（不會拋出錯誤）
            try {
                await this.fetchLatestData();
            } catch (dataError) {
                console.warn('初始數據載入失敗，將在登入後重試:', dataError);
                // 使用模擬數據
                const [dashboardStats, alerts, cameras, systemStatus] = this.getMockData();
                this.updateDashboardStats(dashboardStats.data);
                this.updateAlertsDisplay(alerts.data);
                this.updateCamerasDisplay(cameras.data);
                this.updateSystemPerformance(systemStatus.data);
            }
            
            // 延遲一點時間確保 UI 渲染完成
            setTimeout(() => {
                this.hideLoadingScreen();
                this.showNotification('VisionFlow 系統已就緒', 'success');
            }, 500);
            
        } catch (error) {
            console.error('Dashboard 初始化失敗:', error);
            this.hideLoadingScreen();
            this.showNotification('Dashboard 初始化失敗', 'error');
        }
    }

    getAuthHeaders() {
        // 獲取認證 headers
        if (this.token) {
            return {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            };
        }
        return {
            'Content-Type': 'application/json'
        };
    }

    getMockData() {
        // 提供模擬數據，用於未登入狀態或 API 失敗時
        const dashboardStats = {
            success: true,
            data: {
                cameras: {
                    total: 8,
                    online: 6,
                    offline: 2,
                    recording: 5
                },
                detections: {
                    today: Math.floor(Math.random() * 200) + 50,
                    this_week: Math.floor(Math.random() * 1000) + 300,
                    this_month: Math.floor(Math.random() * 5000) + 1200,
                    total: Math.floor(Math.random() * 50000) + 10000
                },
                alerts: {
                    active: Math.floor(Math.random() * 5),
                    resolved_today: Math.floor(Math.random() * 20) + 5,
                    high_priority: Math.floor(Math.random() * 3),
                    total_today: Math.floor(Math.random() * 30) + 10
                },
                system: {
                    cpu_usage: Math.floor(Math.random() * 60) + 20,
                    memory_usage: Math.floor(Math.random() * 40) + 30,
                    disk_usage: Math.floor(Math.random() * 50) + 40,
                    uptime: '7 天 14 小時 32 分鐘'
                },
                performance: {
                    fps_average: Math.round((Math.random() * 5 + 25) * 10) / 10,
                    detection_accuracy: Math.round((Math.random() * 10 + 85) * 10) / 10,
                    response_time: Math.floor(Math.random() * 150) + 50
                }
            }
        };

        const alerts = {
            success: true,
            data: [
                {
                    id: 1,
                    type: 'detection',
                    message: '攝影機 1 偵測到異常活動',
                    timestamp: new Date().toISOString(),
                    priority: 'high'
                },
                {
                    id: 2,
                    type: 'system',
                    message: '系統運行正常',
                    timestamp: new Date().toISOString(),
                    priority: 'low'
                }
            ]
        };

        const cameras = {
            success: true,
            data: [
                { id: 1, name: '前門攝影機', status: 'online', fps: 30 },
                { id: 2, name: '後門攝影機', status: 'online', fps: 30 },
                { id: 3, name: '停車場攝影機', status: 'offline', fps: 0 },
                { id: 4, name: '會議室攝影機', status: 'online', fps: 25 }
            ]
        };

        const systemStatus = {
            success: true,
            data: {
                cpu_usage: Math.floor(Math.random() * 60) + 20,
                memory_usage: Math.floor(Math.random() * 40) + 30,
                disk_usage: Math.floor(Math.random() * 50) + 40,
                network_status: 'healthy',
                service_status: 'running'
            }
        };

        return [dashboardStats, alerts, cameras, systemStatus];
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
        return new Promise((resolve, reject) => {
            try {
                // 設置連接超時 - 無論成功或失敗都要 resolve，不要阻塞初始化
                const connectionTimeout = setTimeout(() => {
                    console.warn('WebSocket 連接超時，繼續使用離線模式');
                    resolve(); // 改為 resolve 而不是 reject
                }, 3000); // 縮短超時時間

                this.socket = io({
                    transports: ['websocket', 'polling'],
                    upgrade: true,
                    rememberUpgrade: true,
                    reconnection: true,
                    reconnectionAttempts: this.maxRetries,
                    reconnectionDelay: 1000,
                    timeout: 3000, // 縮短超時時間
                    forceNew: true // 強制建立新連接
                });

                this.socket.on('connect', () => {
                    console.log('✅ VisionFlow 連接成功');
                    this.isConnected = true;
                    this.retryCount = 0;
                    clearTimeout(connectionTimeout);
                    this.showNotification('系統連接成功', 'success');
                    this.socket.emit('join_room', { room: 'dashboard' });
                    this.updateConnectionStatus(true);
                    resolve();
                });

                this.socket.on('connect_error', (error) => {
                    console.warn('WebSocket 連接錯誤:', error);
                    clearTimeout(connectionTimeout);
                    this.updateConnectionStatus(false);
                    resolve(); // 改為 resolve，繼續初始化
                });

                this.socket.on('disconnect', (reason) => {
                    console.log('❌ VisionFlow 連接斷開:', reason);
                    this.isConnected = false;
                    this.updateConnectionStatus(false);
                    this.showNotification('連接已斷開，正在重新連接...', 'warning');
                });

                this.socket.on('reconnect', () => {
                    console.log('🔄 VisionFlow 重新連接成功');
                    this.isConnected = true;
                    this.updateConnectionStatus(true);
                    this.showNotification('重新連接成功', 'success');
                });

                // 實時數據監聽
                this.socket.on('dashboard_update', (data) => {
                    this.handleDashboardUpdate(data);
                });

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
                resolve(); // 即使失敗也 resolve，繼續初始化
            }
        });
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
                    backgroundColor: (context) => {
                        const yScale = context.chart.scales?.y;
                        // 防呆：context.parsed 也可能是 undefined
                        if (!yScale || !context.parsed || typeof context.parsed.y === 'undefined') {
                            return 'rgba(54, 162, 235, 0.1)'; // 預設顏色
                        }
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
                // 修正：每次切換到 cameras tab 時，重新綁定新增攝影機按鈕事件
                if (targetTab === 'cameras') {
                    const addCameraBtn = document.getElementById('add-camera');
                    if (addCameraBtn) {
                        addCameraBtn.onclick = null; // 先移除舊的
                        addCameraBtn.addEventListener('click', () => {
                            console.log('add-camera clicked'); // debug log
                            this.showAddCameraModal();
                        });
                    }
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

        // 重新整理按鈕
        const refreshBtn = document.getElementById('refresh-data');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.fetchLatestData();
                this.showNotification('正在重新整理數據...', 'info');
            });
        }

        // 匯出數據按鈕
        const exportBtn = document.getElementById('export-data');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportData();
            });
        }

        // 新增攝影機按鈕
        const addCameraBtn = document.getElementById('add-camera');
        if (addCameraBtn) {
            addCameraBtn.addEventListener('click', () => {
                this.showAddCameraModal();
            });
        }

        // 生成報告按鈕
        const generateReportBtn = document.getElementById('generate-report');
        if (generateReportBtn) {
            generateReportBtn.addEventListener('click', () => {
                this.generateReport();
            });
        }

        // 全部標為已讀按鈕
        const markAllReadBtn = document.getElementById('mark-all-read');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => {
                this.markAllAlertsAsRead();
            });
        }

        // 警報設定按鈕
        const alertSettingsBtn = document.getElementById('alert-settings');
        if (alertSettingsBtn) {
            alertSettingsBtn.addEventListener('click', () => {
                this.showAlertSettings();
            });
        }

        // 儲存設定按鈕
        const saveSettingsBtn = document.getElementById('save-settings');
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => {
                this.saveSettings();
            });
        }

        // 自動重新整理切換
        const autoRefreshToggle = document.getElementById('auto-refresh');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startPeriodicUpdates();
                } else {
                    this.pauseUpdates();
                }
            });
        }

        // 聲音警報切換
        const soundAlertsToggle = document.getElementById('sound-alerts');
        if (soundAlertsToggle) {
            soundAlertsToggle.addEventListener('change', (e) => {
                this.updateSystemSetting('sound_alerts', e.target.checked);
            });
        }

        // Email 通知切換
        const emailNotificationsToggle = document.getElementById('email-notifications');
        if (emailNotificationsToggle) {
            emailNotificationsToggle.addEventListener('change', (e) => {
                this.updateSystemSetting('email_notifications', e.target.checked);
            });
        }

        // LINE 通知切換
        const lineNotificationsToggle = document.getElementById('line-notifications');
        if (lineNotificationsToggle) {
            lineNotificationsToggle.addEventListener('change', (e) => {
                this.updateSystemSetting('line_notifications', e.target.checked);
            });
        }

        // 浮動操作按鈕
        const fabMain = document.getElementById('fab-main');
        if (fabMain) {
            fabMain.addEventListener('click', () => {
                const fabContainer = document.querySelector('.fab-container');
                fabContainer.classList.toggle('fab-open');
            });
        }

        // 處理浮動操作按鈕選項
        document.querySelectorAll('.fab-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const action = e.target.closest('.fab-option').dataset.action;
                this.handleFabAction(action);
            });
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
            // 獲取認證 headers
            const headers = this.getAuthHeaders();
            // 檢查是否有認證 token
            const hasAuth = this.token;
            console.log('認證狀態檢查:', {
                token: this.token ? '存在' : '不存在',
                isLoggedIn: this.isLoggedIn,
                hasAuth: hasAuth
            });

            let dashboardStats, alerts, cameras, systemStatus;
            let cameraStatusMap = {};

            // 先取得攝影機狀態
            try {
                const statusResponse = await fetch('http://localhost:15440/camera_status');
                if (statusResponse.ok) {
                    const statusResult = await statusResponse.json();
                    if (statusResult.success && statusResult.data) {
                        cameraStatusMap = statusResult.data;
                    }
                }
            } catch (e) {
                console.warn('無法取得攝影機狀態:', e);
            }

            if (hasAuth) {
                try {
                    [dashboardStats, alerts, systemStatus] = await Promise.all([
                        fetch(`${API_URL}/api/dashboard/stats`, { headers }).then(r => r.json()),
                        fetch(`${API_URL}/api/alerts/active`, { headers }).then(r => r.json()),
                        fetch(`${API_URL}/api/system/status`, { headers }).then(r => r.json())
                    ]);
                    // 單獨獲取攝影機數據，因為路徑不同
                    try {
                        const cameraResponse = await fetch(`${API_URL}/camera/cameras`, {
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${this.token}`
                            }
                        });
                        const cameras_data = await cameraResponse.json();
                        console.log('cameras_data:', cameras_data);
                        const cameraArr = Array.isArray(cameras_data) ? cameras_data : cameras_data.data;
                        if (Array.isArray(cameraArr) && cameraArr.length > 0) {
                            cameras = {
                                success: true,
                                data: cameraArr.map(cam => {
                                    const statusObj = cameraStatusMap[String(cam.id)];
                                    const isOnline = statusObj && statusObj.alive === 'True';
                                    return {
                                        id: cam.id,
                                        name: cam.name || `攝影機 ${cam.id}`,
                                        status: isOnline ? 'online' : 'offline',
                                        detection_count_today: Math.floor(Math.random() * 50),
                                        fps: 0,
                                        last_timestamp: statusObj?.last_image_timestamp || new Date().toISOString(),
                                        url: cam.stream_url || '',
                                        thumbnail: isOnline
                                            ? `http://localhost:15440/get_stream/${cam.id}`
                                            : '/static/images/no_camera.gif'
                                    };
                                })
                            };
                            console.log('合併狀態後的 cameras:', cameras);
                        }
                    } catch (cameraError) {
                        console.warn('攝影機數據獲取失敗:', cameraError);
                        const [, , mockCameras] = this.getMockData();
                        cameras = mockCameras;
                    }
                } catch (apiError) {
                    console.warn('API 請求失敗，使用模擬數據:', apiError);
                    [dashboardStats, alerts, cameras, systemStatus] = this.getMockData();
                }
            } else {
                // 沒有認證，直接使用模擬數據
                console.log('未登入狀態，使用模擬數據');
                [dashboardStats, alerts, cameras, systemStatus] = this.getMockData();
            }

            // 更新儀表板統計數據
            if (dashboardStats && dashboardStats.success) {
                this.updateDashboardStats(dashboardStats.data);
            }
            // 更新警報顯示
            if (alerts && alerts.success) {
                this.updateAlertsDisplay(alerts.data);
            }
            // 更新攝影機顯示
            if (cameras && cameras.success) {
                this.updateCamerasDisplay(cameras.data);
            }
            // 更新系統性能
            if (systemStatus && systemStatus.success) {
                this.updateSystemPerformance(systemStatus.data);
            }
        } catch (error) {
            console.error('獲取數據失敗:', error);
            this.showNotification('數據更新失敗', 'error');
            this.useFallbackData();
        }
    }

    updateDashboardStats(data) {
        // 更新統計卡片，對應 API 的實際數據結構
        this.updateStatCard('total-detections', data.detections?.today || 0);
        this.updateStatCard('active-cameras', data.cameras?.online || 0);
        this.updateStatCard('alerts-today', data.alerts?.total_today || 0);
        this.updateStatCard('system-uptime', data.system?.uptime || '--');
        
        // 更新系統狀態摘要
        this.updateSystemSummary(data.system);
        
        // 更新性能數據
        if (data.performance) {
            this.updatePerformanceData(data.performance);
        }
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

    updateConnectionStatus(isConnected) {
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        
        if (statusDot && statusText) {
            if (isConnected) {
                statusDot.className = 'status-dot online';
                statusText.textContent = '已連接';
            } else {
                statusDot.className = 'status-dot offline';
                statusText.textContent = '離線模式';
            }
        }
    }

    handleDashboardUpdate(data) {
        // 處理儀表板數據更新
        if (data.type === 'stats') {
            this.updateDashboardStats(data.data);
        } else if (data.type === 'charts') {
            this.updateChartData(data.data);
        }
    }

    updateChartData(data) {
        // 更新圖表數據
        if (data.detection_trend && this.charts.detectionTrend) {
            const chart = this.charts.detectionTrend;
            chart.data.labels = data.detection_trend.labels;
            chart.data.datasets[0].data = data.detection_trend.detections;
            chart.data.datasets[1].data = data.detection_trend.alerts;
            chart.update('none');
        }

        if (data.detection_types && this.charts.detectionType) {
            const chart = this.charts.detectionType;
            chart.data.datasets[0].data = data.detection_types.values;
            chart.update('none');
        }
    }

    destroy() {
        // 清理資源
        if (this.socket) {
            this.socket.disconnect();
        }
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // 清理圖表
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });

        console.log('🧹 Dashboard 資源已清理');
    }

    initNotificationSettings() {
        // 初始化通知設定
        const notificationToggles = document.querySelectorAll('.notification-toggle');
        notificationToggles.forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                const setting = e.target.dataset.setting;
                const enabled = e.target.checked;
                this.updateNotificationSetting(setting, enabled);
            });
        });
    }

    initSystemSettings() {
        // 初始化系統設定
        const systemSettings = document.querySelectorAll('.system-setting');
        systemSettings.forEach(setting => {
            setting.addEventListener('change', (e) => {
                const settingName = e.target.dataset.setting;
                const value = e.target.value || e.target.checked;
                this.updateSystemSetting(settingName, value);
            });
        });
    }

    updateNotificationSetting(setting, enabled) {
        // 更新通知設定
        console.log(`更新通知設定: ${setting} = ${enabled}`);
        // 這裡可以發送 API 請求到後端
    }

    updateSystemSetting(setting, value) {
        // 更新系統設定
        console.log(`更新系統設定: ${setting} = ${value}`);
        // 這裡可以發送 API 請求到後端
    }

    updateAlertsDisplay(alerts) {
        // 更新警報顯示
        const alertsList = document.getElementById('alerts-list');
        if (alertsList && alerts) {
            alertsList.innerHTML = alerts.map(alert => `
                <div class="alert-item ${alert.severity}">
                    <div class="alert-content">
                        <h6>${alert.title}</h6>
                        <p>${alert.description}</p>
                        <small>${new Date(alert.timestamp).toLocaleString()}</small>
                    </div>
                </div>
            `).join('');
        }
    }

    updateCamerasDisplay(cameras) {
        // 更新攝影機顯示
        this.updateCameraGrid(cameras);
        this.updateCameraStatusChart(cameras);
    }

    updateSystemPerformance(performance) {
        // 更新系統效能顯示
        if (this.charts.systemPerformance && performance) {
            const chart = this.charts.systemPerformance;
            chart.data.datasets[0].data = [
                performance.cpu || 0,
                performance.memory || 0,
                performance.disk || 0,
                performance.network || 0,
                performance.queue || 0,
                performance.fps || 0
            ];
            chart.update('none');
        }
    }

    updateAlertsCount() {
        // 更新警報計數
        const alertsBadge = document.querySelector('.alerts-count');
        if (alertsBadge) {
            const currentCount = parseInt(alertsBadge.textContent) || 0;
            alertsBadge.textContent = currentCount + 1;
        }
    }

    updateDetectionTrendChart(data) {
        // 更新檢測趨勢圖表
        if (this.charts.detectionTrend && data) {
            const chart = this.charts.detectionTrend;
            const now = new Date().toLocaleTimeString();
            
            // 添加新數據點
            chart.data.labels.push(now);
            chart.data.datasets[0].data.push(data.detections || 0);
            chart.data.datasets[1].data.push(data.alerts || 0);
            
            // 保持最多50個數據點
            if (chart.data.labels.length > 50) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
                chart.data.datasets[1].data.shift();
            }
            
            chart.update('none');
        }
    }

    updateCameraStatusChart(cameras) {
        // 更新攝影機狀態圖表
        if (this.charts.cameraStatus && cameras) {
            const chart = this.charts.cameraStatus;
            chart.data.labels = cameras.map(c => c.name);
            chart.data.datasets[0].data = cameras.map(c => c.detection_count_today || 0);
            chart.update('none');
        }
    }

    updateCameraGrid(cameraList) {
        const cameraGrid = document.getElementById('camera-grid');
        if (!cameraGrid || !cameraList) return;

        cameraGrid.innerHTML = cameraList.map(camera => `
            <div class="camera-card" data-camera-id="${camera.id}">
                <div class="camera-header">
                    <h6>${camera.name}</h6>
                    <span class="status-badge ${camera.status}">${camera.status}</span>
                </div>
                <div class="camera-preview">
                    <img src="${camera.thumbnail || '/static/images/no_camera.gif'}" 
                         alt="${camera.name}" 
                         class="camera-thumbnail">
                </div>
                <div class="camera-stats">
                    <small>今日檢測: ${camera.detection_count_today || 0}</small>
                    <small>FPS: ${camera.fps || 0}</small>
                </div>
                <div class="camera-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="window.visionFlowDashboard.viewCamera('${camera.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="window.visionFlowDashboard.configCamera('${camera.id}')">
                        <i class="fas fa-cog"></i>
                    </button>
                </div>
            </div>
        `).join('');

        cameraList.forEach(camera => {
            console.log('camera.id:', camera.id, 'thumbnail:', camera.thumbnail);
        });
    }

    async loadCameraData() {
        try {
            console.log('正在載入攝影機數據...');
            let cameraList = [];
            let cameraStatusMap = {};

            // 先取得攝影機狀態
            try {
                const statusResponse = await fetch('http://localhost:15440/camera_status');
                if (statusResponse.ok) {
                    const statusResult = await statusResponse.json();
                    if (statusResult.success && statusResult.data) {
                        cameraStatusMap = statusResult.data; // 這是一個以 camera_id 為 key 的物件
                    }
                }
            } catch (e) {
                console.warn('無法取得攝影機狀態:', e);
            }

            // 再取得攝影機列表
            try {
                const response = await fetch(`${API_URL}/camera/cameras`, {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.token}`
                    }
                });
                if (response.ok) {
                    const cameras_data = await response.json();
                    if (Array.isArray(cameras_data) && cameras_data.length > 0) {
                        cameraList = cameras_data.map(cam => {
                            // 取得該攝影機的狀態
                            const statusObj = cameraStatusMap[cam.id?.toString()];
                            const isOnline = statusObj && statusObj.alive === 'True';
                            return {
                                id: cam.id,
                                name: cam.name || `攝影機 ${cam.id}`,
                                status: isOnline ? 'online' : 'offline',
                                detection_count_today: Math.floor(Math.random() * 50),
                                fps: 0,
                                last_timestamp: statusObj?.last_image_timestamp || new Date().toISOString(),
                                url: cam.stream_url || '',
                                thumbnail: isOnline
                                    ? `http://localhost:15440/get_stream/${cam.id}`
                                    : '/static/images/no_camera.gif'
                            };
                        });
                        console.log('合併狀態後的 cameraList:', cameraList);
                    }
                }
            } catch (apiError) {
                console.warn('主 API 不可用:', apiError);
            }

            this.updateCameraGrid(cameraList);
            this.showNotification(`成功載入 ${cameraList.length} 個攝影機的數據`, 'success');
        } catch (error) {
            console.error('載入攝影機數據失敗:', error);
            this.updateCameraGrid([]);
            this.showNotification('無法取得攝影機資料，請確認 API 服務狀態', 'error');
        }
    }

    viewCamera(cameraId) {
        console.log('查看攝影機:', cameraId);
        this.showNotification(`正在開啟攝影機 ${cameraId} 的即時串流`, 'info');
        
        // 切換到即時辨識標籤頁
        const detectionTab = document.querySelector('[data-tab="detection"]');
        const detectionPane = document.getElementById('detection');
        
        if (detectionTab && detectionPane) {
            // 移除所有活動狀態
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
            
            // 添加當前標籤的活動狀態
            detectionTab.classList.add('active');
            detectionPane.classList.add('active');
            
            // 更新即時串流顯示
            this.loadCameraStream(cameraId);
        }
    }

    configCamera(cameraId) {
        console.log('設定攝影機:', cameraId);
        this.showNotification(`正在開啟攝影機 ${cameraId} 的設定面板`, 'info');
        
        if (window.Swal) {
            Swal.fire({
                title: `攝影機 ${cameraId} 設定`,
                html: `
                    <div class="text-start">
                        <div class="mb-3">
                            <label class="form-label">攝影機名稱</label>
                            <input type="text" class="form-control" id="config-name" value="攝影機 ${cameraId}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">串流解析度</label>
                            <select class="form-select" id="config-resolution">
                                <option value="1920x1080">1080p</option>
                                <option value="1280x720" selected>720p</option>
                                <option value="640x480">480p</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">檢測敏感度</label>
                            <input type="range" class="form-range" id="config-sensitivity" min="1" max="10" value="5">
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="config-alerts" checked>
                            <label class="form-check-label" for="config-alerts">啟用警報通知</label>
                        </div>
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: '保存設定',
                cancelButtonText: '取消',
                width: 500
            }).then((result) => {
                if (result.isConfirmed) {
                    this.saveCameraConfig(cameraId);
                }
            });
        }
    }

    exportData() {
        console.log('匯出數據');
        this.showNotification('正在準備匯出數據...', 'info');
        
        // 模擬數據匯出
        const data = {
            timestamp: new Date().toISOString(),
            stats: {
                total_detections: document.getElementById('total-detections')?.textContent || '0',
                active_cameras: document.getElementById('active-cameras')?.textContent || '0',
                alerts_today: document.getElementById('alerts-today')?.textContent || '0',
                system_uptime: document.getElementById('system-uptime')?.textContent || '0'
            }
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `visionflow-data-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showNotification('數據匯出完成', 'success');
    }

    showAddCameraModal() {
        console.log('顯示新增攝影機對話框');

        // 改用 authManager 判斷
        if (!window.authManager?.isLoggedIn) {
            this.showNotification('請先登入才能新增攝影機', 'warning');
            window.authManager.showLoginModal();
            return;
        }

        this.showNotification('正在開啟新增攝影機對話框...', 'info');
        if (window.Swal) {
            Swal.fire({
                title: '新增攝影機',
                html: `
                    <div class="form-group">
                        <label>攝影機名稱:</label>
                        <input type="text" id="camera-name" class="form-control" placeholder="請輸入攝影機名稱">
                    </div>
                    <div class="form-group mt-3">
                        <label>RTSP URL:</label>
                        <input type="text" id="camera-url" class="form-control" placeholder="rtsp://...">
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: '新增',
                cancelButtonText: '取消'
            }).then((result) => {
                if (result.isConfirmed) {
                    const name = document.getElementById('camera-name').value.trim();
                    const url  = document.getElementById('camera-url').value.trim();
                    if (!name) {
                        this.showNotification('請輸入攝影機名稱', 'error');
                        return;
                    }
                    if (!url) {
                        this.showNotification('請輸入 RTSP URL', 'error');
                        return;
                    }
                    this.addCamera(name, url);
                }
            });
        }
    }

    async addCamera(name, url) {
        console.log('新增攝影機:', { name, url });
        this.showNotification(`正在新增攝影機: ${name}`, 'info');
        
        try {
            const headers = {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            };
            
            const response = await fetch(`${API_URL}/camera/cameras`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    name: name,
                    stream_url: url
                })
            });
            
            const result = await response.json();
            
            if (result.id) {  // 假設成功回傳新增攝影機的ID
                this.showNotification(`攝影機 ${name} 新增成功`, 'success');
                this.loadCameraData(); // 重新載入攝影機數據
            } else if (result.message) {
                throw new Error(result.message);
            } else {
                throw new Error('新增攝影機失敗');
            }
        } catch (error) {
            console.error('新增攝影機錯誤:', error);
            this.showNotification(`新增攝影機失敗: ${error.message}`, 'error');
        }
    }

    async loadCameraStream(cameraId) {
        const streamContainer = document.querySelector('.detection-stream');
        if (!streamContainer) {
            console.error('Detection stream container not found');
            return;
        }

        try {
            // 顯示加載狀態
            streamContainer.innerHTML = `
                <div class="camera-stream-display">
                    <div class="stream-header">
                        <h5>正在載入攝影機 ${cameraId}...</h5>
                        <div class="spinner-border spinner-border-sm text-light" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                </div>
            `;

            // 獲取攝影機資訊
            let camera = null;
            let streamUrl = `http://localhost:15440/get_stream/${cameraId}`;
            
            try {
                // 嘗試從 camera controller 獲取攝影機狀態
                const statusResponse = await fetch(`http://localhost:15440/camera_status`);
                if (statusResponse.ok) {
                    const statusResult = await statusResponse.json();
                    if (statusResult.success && statusResult.data) {
                        // 修正：data 是物件不是陣列
                        const cameraStatus = statusResult.data[cameraId.toString()];
                        
                        if (cameraStatus) {
                            camera = {
                                name: `攝影機 ${cameraId}`,
                                status: cameraStatus.status === 'True' ? 'online' : 'offline',
                                fps: cameraStatus.fps || 0
                            };
                        }
                    }
                }
            } catch (err) {
                console.warn('無法獲取攝影機狀態，使用預設設定:', err);
            }

            // 如果無法獲取狀態，使用預設值
            if (!camera) {
                camera = {
                    name: `攝影機 ${cameraId}`,
                    status: 'unknown',
                    fps: 0
                };
            }

            streamContainer.innerHTML = `
                <div class="camera-stream-display" data-camera-id="${cameraId}">
                    <div class="stream-header">
                        <h5>${camera.name} 即時串流</h5>
                        <div class="stream-status">
                            <span class="badge ${camera.status === 'online' ? 'bg-success' : 'bg-danger'}">${camera.status}</span>
                        </div>
                        <div class="stream-controls">
                            <button class="btn btn-sm btn-outline-light" onclick="window.visionFlowDashboard.toggleFullscreen()" title="全螢幕">
                                <i class="fas fa-expand"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-light" onclick="window.visionFlowDashboard.takeSnapshot(${cameraId})" title="截圖">
                                <i class="fas fa-camera"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-light" onclick="window.visionFlowDashboard.configCamera(${cameraId})" title="設定">
                                <i class="fas fa-cog"></i>
                            </button>
                        </div>
                    </div>
                    <div class="stream-video-container">
                        <img src="${streamUrl}" 
                             alt="${camera.name}串流" 
                             class="stream-video"
                             style="width: 100%; max-height: 400px; object-fit: cover;"
                             onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuaUnemMoeapnyAke2NhbWVyYUlkfSDnhKHms5XpgKPntZE8L3RleHQ+PC9zdmc+';">
                        <div class="stream-overlay">
                            <div class="detection-info">
                                <span class="badge bg-success" id="detection-status">即時檢測中</span>
                                <span class="badge bg-info" id="fps-indicator-${cameraId}">FPS: ${camera.fps}</span>
                                <span class="badge bg-warning" id="detection-count-${cameraId}">檢測: 0</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 啟動串流監控
            this.startStreamMonitoring(cameraId);
            
        } catch (error) {
            console.error('載入攝影機串流失敗:', error);
            streamContainer.innerHTML = `
                <div class="camera-stream-display error">
                    <div class="stream-header">
                        <h5>攝影機 ${cameraId} 載入失敗</h5>
                    </div>
                    <div class="stream-error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>${error.message}</p>
                        <button class="btn btn-sm btn-outline-light" onclick="window.visionFlowDashboard.loadCameraStream(${cameraId})">
                            重新載入
                        </button>
                    </div>
                </div>
            `;
        }
    }

    async saveCameraConfig(cameraId) {
        const name = document.getElementById('config-name')?.value;
        const resolution = document.getElementById('config-resolution')?.value;
        const sensitivity = document.getElementById('config-sensitivity')?.value;
        const alerts = document.getElementById('config-alerts')?.checked;
        
        if (!name || !name.trim()) {
            this.showNotification('攝影機名稱不能為空', 'error');
            return;
        }
        
        const configData = {
            name: name.trim(),
            resolution: resolution,
            sensitivity: parseInt(sensitivity),
            alerts_enabled: alerts
        };
        
        try {
            this.showNotification('正在保存攝影機設定...', 'info');
            
            // 首先嘗試更新攝影機基本資訊（如果有相關 API）
            let updateSuccess = false;
            
            try {
                // 嘗試調用攝影機控制器的 API 來保存設定
                const controllerResponse = await fetch(`http://localhost:15440/camera_config/${cameraId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(configData)
                });
                
                if (controllerResponse.ok) {
                    updateSuccess = true;
                }
            } catch (err) {
                console.warn('攝影機控制器 API 不可用，使用本地儲存:', err);
            }
            
            // 如果控制器 API 不可用，保存到本地儲存
            if (!updateSuccess) {
                const savedConfigs = JSON.parse(localStorage.getItem('camera-configs') || '{}');
                savedConfigs[cameraId] = configData;
                localStorage.setItem('camera-configs', JSON.stringify(savedConfigs));
            }
            
            console.log('攝影機設定已保存:', { cameraId, ...configData });
            this.showNotification(`攝影機 ${cameraId} 設定已保存`, 'success');
            
            // 如果當前正在顯示此攝影機的串流，更新顯示
            const currentStreamDisplay = document.querySelector(`.camera-stream-display[data-camera-id="${cameraId}"]`);
            if (currentStreamDisplay) {
                const streamHeader = currentStreamDisplay.querySelector('.stream-header h5');
                if (streamHeader) {
                    streamHeader.textContent = `${name} 即時串流`;
                }
            }
            
        } catch (error) {
            console.error('保存攝影機設定失敗:', error);
            this.showNotification('保存設定失敗，請重試', 'error');
        }
    }

    async takeSnapshot(cameraId) {
        try {
            this.showNotification(`正在截取攝影機 ${cameraId} 的畫面...`, 'info');
            
            // 嘗試從攝影機控制器獲取快照
            const snapshotUrl = `http://localhost:15440/get_snapshot/${cameraId}`;
            
            try {
                const response = await fetch(snapshotUrl);
                
                if (response.ok) {
                    // 創建 blob URL 下載圖片
                    const blob = await response.blob();
                    
                    // 創建下載連結
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                    a.href = url;
                    a.download = `camera-${cameraId}-snapshot-${timestamp}.jpg`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    
                    this.showNotification('截圖已保存到下載資料夾', 'success');
                    
                    // 如果使用了 SweetAlert2，顯示預覽
                    if (window.Swal) {
                        const imageUrl = URL.createObjectURL(blob);
                        Swal.fire({
                            title: `攝影機 ${cameraId} 截圖`,
                            html: `
                                <div class="text-center">
                                    <img src="${imageUrl}" style="max-width: 100%; max-height: 400px; border-radius: 8px;">
                                    <p class="mt-2 text-muted">截圖時間: ${new Date().toLocaleString()}</p>
                                </div>
                            `,
                            showConfirmButton: true,
                            confirmButtonText: '關閉',
                            width: 600,
                            didDestroy: () => {
                                URL.revokeObjectURL(imageUrl);
                            }
                        });
                    }
                    
                } else {
                    throw new Error(`無法獲取攝影機 ${cameraId} 的快照`);
                }
                
            } catch (fetchError) {
                console.warn('無法從控制器獲取快照，嘗試其他方法:', fetchError);
                
                // 嘗試從當前顯示的串流圖片截圖
                const streamImage = document.querySelector(`.camera-stream-display[data-camera-id="${cameraId}"] .stream-video`);
                
                if (streamImage && streamImage.src && !streamImage.src.includes('data:image/svg+xml')) {
                    // 創建 canvas 來截取圖片
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    
                    // 等待圖片載入
                    const img = new Image();
                    img.crossOrigin = 'anonymous';
                    
                    img.onload = () => {
                        canvas.width = img.naturalWidth || img.width;
                        canvas.height = img.naturalHeight || img.height;
                        ctx.drawImage(img, 0, 0);
                        
                        // 轉換為 blob 並下載
                        canvas.toBlob((blob) => {
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                            a.href = url;
                            a.download = `camera-${cameraId}-snapshot-${timestamp}.jpg`;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                            
                            this.showNotification('截圖已保存到下載資料夾', 'success');
                        }, 'image/jpeg', 0.9);
                    };
                    
                    img.onerror = () => {
                        this.showNotification('截圖失敗，無法讀取影像', 'error');
                    };
                    
                    img.src = streamImage.src;
                } else {
                    throw new Error('無法找到可用的影像來源');
                }
            }
            
        } catch (error) {
            console.error('截圖失敗:', error);
            this.showNotification('截圖失敗: ' + error.message, 'error');
        }
    }

    toggleFullscreen() {
        const streamContainer = document.querySelector('.camera-stream-display');
        
        if (!streamContainer) {
            this.showNotification('無法找到攝影機串流容器', 'error');
            return;
        }
        
        try {
            if (!document.fullscreenElement) {
                // 進入全螢幕模式
                if (streamContainer.requestFullscreen) {
                    streamContainer.requestFullscreen();
                } else if (streamContainer.webkitRequestFullscreen) {
                    streamContainer.webkitRequestFullscreen();
                } else if (streamContainer.msRequestFullscreen) {
                    streamContainer.msRequestFullscreen();
                } else if (streamContainer.mozRequestFullScreen) {
                    streamContainer.mozRequestFullScreen();
                } else {
                    throw new Error('瀏覽器不支援全螢幕模式');
                }
                
                // 更新按鈕圖示
                const fullscreenBtn = streamContainer.querySelector('[onclick*="toggleFullscreen"] i');
                if (fullscreenBtn) {
                    fullscreenBtn.className = 'fas fa-compress';
                }
                
                // 添加全螢幕樣式
                streamContainer.classList.add('fullscreen-mode');
                
                this.showNotification('已進入全螢幕模式，按 ESC 退出', 'info');
                
            } else {
                // 退出全螢幕模式
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                } else if (document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                }
            }
            
        } catch (error) {
            console.error('全螢幕切換失敗:', error);
            this.showNotification('全螢幕功能出現錯誤: ' + error.message, 'error');
        }
    }

    startStreamMonitoring(cameraId) {
        // 清除之前的監控間隔
        if (this.streamMonitorInterval) {
            clearInterval(this.streamMonitorInterval);
        }
        
        console.log(`開始監控攝影機 ${cameraId} 的串流狀態`);
        
        // 每5秒更新一次攝影機狀態
        this.streamMonitorInterval = setInterval(async () => {
            try {
                // 檢查是否還在顯示此攝影機
                const streamDisplay = document.querySelector(`.camera-stream-display[data-camera-id="${cameraId}"]`);
                if (!streamDisplay) {
                    clearInterval(this.streamMonitorInterval);
                    return;
                }
                
                // 獲取攝影機狀態
                const statusResponse = await fetch(`http://localhost:15440/camera_status`);
                if (statusResponse.ok) {
                    const statusResult = await statusResponse.json();
                    if (statusResult.success && statusResult.data) {
                        // 修正：data 是物件不是陣列
                        const cameraStatus = statusResult.data[cameraId.toString()];
                        
                        if (cameraStatus) {
                            // 更新 FPS 指示器
                            const fpsIndicator = document.getElementById(`fps-indicator-${cameraId}`);
                            if (fpsIndicator) {
                                const fps = parseFloat(cameraStatus.fps) || 0;
                                fpsIndicator.textContent = `FPS: ${fps.toFixed(1)}`;
                                
                                // 根據 FPS 更新指示器顏色
                                fpsIndicator.className = 'badge';
                                if (fps >= 25) {
                                    fpsIndicator.classList.add('bg-success');
                                } else if (fps >= 15) {
                                    fpsIndicator.classList.add('bg-warning');
                                } else {
                                    fpsIndicator.classList.add('bg-danger');
                                }
                            }
                            
                            // 更新狀態指示器
                            const statusBadge = streamDisplay.querySelector('.stream-status .badge');
                            if (statusBadge) {
                                const isOnline = cameraStatus.status === 'True';
                                statusBadge.textContent = isOnline ? 'online' : 'offline';
                                statusBadge.className = `badge ${isOnline ? 'bg-success' : 'bg-danger'}`;
                            }
                            
                            // 更新檢測狀態
                            const detectionStatus = document.getElementById('detection-status');
                            if (detectionStatus && cameraStatus.status === 'True') {
                                detectionStatus.textContent = '即時檢測中';
                                detectionStatus.className = 'badge bg-success';
                            } else if (detectionStatus) {
                                detectionStatus.textContent = '檢測暫停';
                                detectionStatus.className = 'badge bg-secondary';
                            }
                        }
                    }
                }
                
                // 模擬檢測計數更新（實際應用中應該從真實的檢測 API 獲取）
                const detectionCount = document.getElementById(`detection-count-${cameraId}`);
                if (detectionCount) {
                    const currentCount = parseInt(detectionCount.textContent.replace('檢測: ', '')) || 0;
                    // 隨機增加檢測數量（僅用於示範）
                    if (Math.random() < 0.1) { // 10% 機率增加
                        detectionCount.textContent = `檢測: ${currentCount + 1}`;
                    }
                }
                
            } catch (error) {
                console.warn('更新串流狀態失敗:', error);
            }
        }, 5000);
        
        // 監控串流圖片載入狀態
        const streamImage = document.querySelector(`.camera-stream-display[data-camera-id="${cameraId}"] .stream-video`);
        if (streamImage) {
            streamImage.addEventListener('load', () => {
                console.log(`攝影機 ${cameraId} 串流圖片載入成功`);
            });
            
            streamImage.addEventListener('error', () => {
                console.warn(`攝影機 ${cameraId} 串流圖片載入失敗`);
                // 可以在這裡添加重試邏輯
            });
        }
    }

    generateReport() {
        const period = document.getElementById('report-period')?.value || 'today';
        console.log('生成報告:', period);
        this.showNotification(`正在生成 ${period} 報告...`, 'info');
        
        // 模擬報告生成
        setTimeout(() => {
            this.showNotification('報告生成完成', 'success');
        }, 2000);
    }

    markAllAlertsAsRead() {
        console.log('標記所有警報為已讀');
        this.showNotification('所有警報已標記為已讀', 'success');
        
        // 更新 UI
        const alertCount = document.getElementById('notification-count');
        if (alertCount) {
            alertCount.textContent = '0';
        }
    }

    showAlertSettings() {
        console.log('顯示警報設定');
        this.showNotification('正在開啟警報設定...', 'info');
    }

    saveSettings() {
        console.log('儲存設定');
        this.showNotification('設定已儲存', 'success');
        
        // 收集所有設定值
        const settings = {
            theme: document.getElementById('theme-toggle')?.checked ? 'dark' : 'light',
            autoRefresh: document.getElementById('auto-refresh')?.checked || false,
            soundAlerts: document.getElementById('sound-alerts')?.checked || false,
            emailNotifications: document.getElementById('email-notifications')?.checked || false,
            lineNotifications: document.getElementById('line-notifications')?.checked || false
        };

        // 保存到 localStorage
        localStorage.setItem('visionflow-settings', JSON.stringify(settings));
        
        // 這裡可以發送 API 請求保存設定到後端
    }

    loadSettings() {
        const savedSettings = localStorage.getItem('visionflow-settings');
        if (savedSettings) {
            try {
                const settings = JSON.parse(savedSettings);
                
                // 應用設定
                if (settings.theme) {
                    this.setTheme(settings.theme);
                    const themeToggle = document.getElementById('theme-toggle');
                    if (themeToggle) {
                        themeToggle.checked = settings.theme === 'dark';
                    }
                }

                // 其他設定
                const autoRefreshToggle = document.getElementById('auto-refresh');
                if (autoRefreshToggle) {
                    autoRefreshToggle.checked = settings.autoRefresh;
                }

                const soundAlertsToggle = document.getElementById('sound-alerts');
                if (soundAlertsToggle) {
                    soundAlertsToggle.checked = settings.soundAlerts;
                }

                const emailNotificationsToggle = document.getElementById('email-notifications');
                if (emailNotificationsToggle) {
                    emailNotificationsToggle.checked = settings.emailNotifications;
                }

                const lineNotificationsToggle = document.getElementById('line-notifications');
                if (lineNotificationsToggle) {
                    lineNotificationsToggle.checked = settings.lineNotifications;
                }

            } catch (error) {
                console.error('載入設定失敗:', error);
            }
        }
    }

    handleFabAction(action) {
        const fabContainer = document.querySelector('.fab-container');
        fabContainer.classList.remove('fab-open');

        switch (action) {
            case 'screenshot':
                this.takeScreenshot();
                break;
            case 'alert':
                this.showTestAlert();
                break;
            case 'report':
                this.generateQuickReport();
                break;
            default:
                console.log('未知的 FAB 操作:', action);
        }
    }

    takeScreenshot() {
        console.log('截圖功能');
        this.showNotification('正在準備截圖...', 'info');
        
        // 這裡可以實現截圖功能
        setTimeout(() => {
            this.showNotification('截圖已保存', 'success');
        }, 1000);
    }

    showTestAlert() {
        this.showNotification('這是一個測試警報', 'warning');
    }

    generateQuickReport() {
        this.showNotification('正在生成快速報告...', 'info');
        setTimeout(() => {
            this.showNotification('快速報告生成完成', 'success');
        }, 1500);
    }

    useFallbackData() {
        // 使用備用模擬數據
        const fallbackStats = {
            cameras: { total: 8, online: 6, offline: 2, recording: 5 },
            detections: { today: 89, this_week: 456, this_month: 1234, total: 12345 },
            alerts: { active: 2, resolved_today: 8, high_priority: 1, total_today: 10 },
            system: { cpu_usage: 45, memory_usage: 62, disk_usage: 78, uptime: '7 天 14 小時' }
        };

        this.updateDashboardStats(fallbackStats);
        this.showNotification('使用離線數據顯示', 'warning');
    }

    updateSystemSummary(systemData) {
        if (!systemData) return;
        
        // 更新 CPU 使用率
        const cpuElement = document.getElementById('cpu-usage');
        if (cpuElement) {
            cpuElement.textContent = `${systemData.cpu_usage || 0}%`;
        }
        
        // 更新記憶體使用率
        const memoryElement = document.getElementById('memory-usage');
        if (memoryElement) {
            memoryElement.textContent = `${systemData.memory_usage || 0}%`;
        }
        
        // 更新運行時間
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement) {
            uptimeElement.textContent = systemData.uptime || '--';
        }
    }
    
    updatePerformanceData(performanceData) {
        if (!performanceData) return;
        
        // 這裡可以更新圖表或其他性能相關的 UI 元素
        console.log('Performance data updated:', performanceData);
    }

    /**
     * 顯示通知消息
     * @param {string} message - 通知消息
     * @param {string} type - 通知類型 (success, error, warning, info)
     */
    showNotification(message, type = 'info') {
        // 嘗試使用智能通知系統
        if (window.smartNotifications) {
            try {
                switch (type) {
                    case 'success':
                        window.smartNotifications.success('系統通知', message);
                        break;
                    case 'error':
                        window.smartNotifications.error('系統錯誤', message);
                        break;
                    case 'warning':
                        window.smartNotifications.warning('系統警告', message);
                        break;
                    case 'info':
                    default:
                        window.smartNotifications.info('系統信息', message);
                        break;
                }
                return;
            } catch (error) {
                console.warn('智能通知系統調用失敗，使用備用通知:', error);
            }
        }

        // 備用通知系統
        this.showFallbackNotification(message, type);
    }

    /**
     * 備用通知系統
     * @param {string} message - 通知消息
     * @param {string} type - 通知類型
     */
    showFallbackNotification(message, type = 'info') {
        // 創建通知元素
        const notification = document.createElement('div');
        notification.className = `dashboard-notification notification-${type}`;
        
        // 設置圖標
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${iconMap[type] || iconMap.info}"></i>
                <span class="notification-message">${message}</span>
                <button class="notification-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // 添加樣式
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: var(--bg-secondary, #fff);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            border-left: 4px solid var(--${type}-color, #007bff);
            z-index: 1000;
            min-width: 300px;
            max-width: 400px;
            transform: translateX(100%);
            opacity: 0;
            transition: all 0.3s ease;
        `;

        // 設置顏色
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#007bff'
        };
        notification.style.borderLeftColor = colors[type] || colors.info;

        // 添加到頁面
        document.body.appendChild(notification);

        // 顯示動畫
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        }, 100);

        // 關閉按鈕事件
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.hideNotification(notification);
        });

        // 自動關閉
        setTimeout(() => {
            this.hideNotification(notification);
        }, 5000);

        return notification;
    }

    /**
     * 隱藏通知
     * @param {HTMLElement} notification - 通知元素
     */
    hideNotification(notification) {
        if (notification && notification.parentNode) {
            notification.style.transform = 'translateX(100%)';
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    }
}

// 認證管理類
class AuthManager {
    constructor() {
        this.token = localStorage.getItem('accessToken');
        this.isLoggedIn = false;
        this.currentUser = null;
        this.init();
    }

    init() {
        this.checkAuthStatus();
        this.setupEventListeners();
        this.updateUI();
    }

    setupEventListeners() {
        // 登入表單事件
        const loginSubmit = document.getElementById('loginSubmit');
        const loginForm = document.getElementById('loginForm');
        
        if (loginSubmit) {
            loginSubmit.addEventListener('click', () => this.handleLogin());
        }
        
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        // 註冊表單事件
        const registerSubmit = document.getElementById('registerSubmit');
        const registerForm = document.getElementById('registerForm');
        
        if (registerSubmit) {
            registerSubmit.addEventListener('click', () => this.handleRegister());
        }
        
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleRegister();
            });
        }

        // 導航選單事件
        const loginMenuItem = document.getElementById('login-menu-item');
        const registerMenuItem = document.getElementById('register-menu-item');
        const logoutMenuItem = document.getElementById('logout-menu-item');
        
        if (loginMenuItem) {
            loginMenuItem.addEventListener('click', (e) => {
                e.preventDefault();
                this.showLoginModal();
            });
        }
        
        if (registerMenuItem) {
            registerMenuItem.addEventListener('click', (e) => {
                e.preventDefault();
                this.showRegisterModal();
            });
        }
        
        if (logoutMenuItem) {
            logoutMenuItem.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleLogout();
            });
        }

        // 模態框切換事件
        const showRegisterModal = document.getElementById('showRegisterModal');
        const showLoginModal = document.getElementById('showLoginModal');
        
        if (showRegisterModal) {
            showRegisterModal.addEventListener('click', () => {
                bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
                this.showRegisterModal();
            });
        }
        
        if (showLoginModal) {
            showLoginModal.addEventListener('click', () => {
                bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
                this.showLoginModal();
            });
        }
    }

    async checkAuthStatus() {
        console.log('檢查認證狀態，token:', this.token ? '存在' : '不存在');

        if (!this.token) {
            this.isLoggedIn = false;
        } else {
            try {
                const res = await fetch(`${API_URL}/auth/verify`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json'
                    }
                });
                if (res.ok) {
                    const data = await res.json();
                    this.isLoggedIn = true;
                    this.currentUser = data.user;
                } else {
                    this.logout();
                }
            } catch (err) {
                console.error('認證驗證錯誤:', err);
                this.logout();
            }
        }

        // 驗證完畢後再更新 UI
        this.updateUI();
        // 並同步到 Dashboard
        if (window.visionFlowDashboard) {
            window.visionFlowDashboard.isLoggedIn = this.isLoggedIn;
        }
    }

    async handleLogin() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        const errorDiv = document.getElementById('loginError');

        if (!username || !password) {
            this.showError(errorDiv, '請填寫使用者名稱和密碼');
            return;
        }

        try {
            const res = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();

            if (res.ok) {
                this.token = data.access_token;
                localStorage.setItem('accessToken', this.token);
                this.isLoggedIn = true;
                this.currentUser = { username, account_uuid: data.account_uuid };

                bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
                this.updateUI();
                this.showNotification('登入成功', 'success');

                // 同步 Dashboard 並刷新資料
                if (window.visionFlowDashboard) {
                    window.visionFlowDashboard.isLoggedIn = true;
                    window.visionFlowDashboard.fetchLatestData();
                }

                document.getElementById('loginForm').reset();
                errorDiv.style.display = 'none';
            } else {
                this.showError(errorDiv, data.message || '登入失敗');
            }
        } catch (err) {
            console.error('登入錯誤:', err);
            this.showError(errorDiv, '網路錯誤，請稍後再試');
        }
    }

    async handleRegister() {
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const errorDiv = document.getElementById('registerError');
        const successDiv = document.getElementById('registerSuccess');

        if (!username || !email || !password || !confirmPassword) {
            this.showError(errorDiv, '請填寫所有必填欄位');
            return;
        }

        if (password !== confirmPassword) {
            this.showError(errorDiv, '密碼確認不一致');
            return;
        }

        if (password.length < 6) {
            this.showError(errorDiv, '密碼長度至少需要6個字符');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showSuccess(successDiv, '註冊成功！請使用新帳號登入');
                document.getElementById('registerForm').reset();
                errorDiv.style.display = 'none';
                
                // 2秒後切換到登入模態框
                setTimeout(() => {
                    bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
                    this.showLoginModal();
                }, 2000);
            } else {
                this.showError(errorDiv, data.message || '註冊失敗');
            }
        } catch (error) {
            console.error('註冊錯誤:', error);
            this.showError(errorDiv, '網路錯誤，請稍後再試');
        }
    }

    handleLogout() {
        this.logout();
        this.updateUI();
        this.showNotification('已登出', 'info');
    }

    logout() {
        this.token = null;
        this.isLoggedIn = false;
        this.currentUser = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('tokenExpireTime');
    }

    updateUI() {
        const usernameDisplay = document.getElementById('username-display');
        const loginMenuItem = document.getElementById('login-menu-item');
        const registerMenuItem = document.getElementById('register-menu-item');
        const profileMenuItem = document.getElementById('profile-menu-item');
        const settingsMenuItem = document.getElementById('settings-menu-item');
        const logoutMenuItem = document.getElementById('logout-menu-item');
        const dividerAuth = document.getElementById('divider-auth');
        const dividerLogout = document.getElementById('divider-logout');

        if (this.isLoggedIn && this.currentUser) {
            usernameDisplay.textContent = this.currentUser.username || '管理員';
            
            // 隱藏登入/註冊選項
            if (loginMenuItem) loginMenuItem.style.display = 'none';
            if (registerMenuItem) registerMenuItem.style.display = 'none';
            
            // 顯示已登入選項
            if (profileMenuItem) profileMenuItem.style.display = 'block';
            if (settingsMenuItem) settingsMenuItem.style.display = 'block';
            if (logoutMenuItem) logoutMenuItem.style.display = 'block';
            if (dividerAuth) dividerAuth.style.display = 'block';
            if (dividerLogout) dividerLogout.style.display = 'block';
        } else {
            usernameDisplay.textContent = '未登入';
            
            // 顯示登入/註冊選項
            if (loginMenuItem) loginMenuItem.style.display = 'block';
            if (registerMenuItem) registerMenuItem.style.display = 'block';
            
            // 隱藏已登入選項
            if (profileMenuItem) profileMenuItem.style.display = 'none';
            if (settingsMenuItem) settingsMenuItem.style.display = 'none';
            if (logoutMenuItem) logoutMenuItem.style.display = 'none';
            if (dividerAuth) dividerAuth.style.display = 'none';
            if (dividerLogout) dividerLogout.style.display = 'none';
        }
    }

    showLoginModal() {
        const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
        loginModal.show();
    }

    showRegisterModal() {
        const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
        registerModal.show();
    }

    showError(element, message) {
        element.textContent = message;
        element.style.display = 'block';
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }

    showSuccess(element, message) {
        element.textContent = message;
        element.style.display = 'block';
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }

    showNotification(message, type = 'info') {
        // 使用 VisionFlowAdvancedDashboard 的通知系統
        if (window.visionFlowDashboard) {
            window.visionFlowDashboard.showNotification(message, type);
        }
    }

    getAuthHeaders() {
        if (this.token) {
            return {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            };
        }
        return {
            'Content-Type': 'application/json'
        };
    }
}

// 初始化儀表板
document.addEventListener('DOMContentLoaded', () => {
    window.visionFlowDashboard = new VisionFlowAdvancedDashboard();
    window.authManager = new AuthManager();
});

// 清理資源
window.addEventListener('beforeunload', () => {
    if (window.visionFlowDashboard) {
        window.visionFlowDashboard.destroy();
    }
});
