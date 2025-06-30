/**
 * VisionFlow Smart Notification System
 * 智能通知系統 - 多通道、優先級管理、批量處理
 */

class SmartNotificationSystem {
    constructor() {
        this.notifications = [];
        this.channels = {
            desktop: true,
            sound: true,
            vibration: true,
            email: false,
            line: false
        };
        this.settings = {
            maxNotifications: 50,
            autoExpiry: 30000, // 30秒
            groupSimilar: true,
            quietHours: {
                enabled: false,
                start: '22:00',
                end: '08:00'
            },
            priorities: {
                critical: { sound: true, persistent: true, color: '#ff4757' },
                high: { sound: true, persistent: false, color: '#ffa502' },
                medium: { sound: false, persistent: false, color: '#3742fa' },
                low: { sound: false, persistent: false, color: '#2ed573' }
            }
        };
        this.soundCache = new Map();
        this.notificationQueue = [];
        this.isProcessing = false;
        
        this.init();
    }

    async init() {
        await this.requestPermissions();
        await this.loadSettings();
        this.createNotificationContainer();
        this.setupEventListeners();
        this.preloadSounds();
        this.setupWebSocketConnection();
        
        // 啟動通知處理循環
        this.startNotificationProcessor();
        
        console.log('🔔 Smart Notification System initialized');
    }

    async requestPermissions() {
        // 請求桌面通知權限
        try {
            if ('Notification' in window) {
                if (Notification.permission === 'default') {
                    const permission = await Notification.requestPermission();
                    console.log('Desktop notification permission:', permission);
                }
            }
        } catch (error) {
            console.warn('Desktop notification permission request failed:', error);
        }

        // 請求媒體權限（用於聲音）- 可選的，不會阻止初始化
        try {
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                // 不實際請求權限，只檢查是否可用
                console.log('Audio features available');
            }
        } catch (error) {
            console.log('Audio features not available:', error);
        }
    }

    async loadSettings() {
        try {
            // 首先嘗試從伺服器加載設定
            const response = await fetch('/api/notifications/settings', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                }
            });

            if (response.ok) {
                const serverResponse = await response.json();
                if (serverResponse.success && serverResponse.data) {
                    // 將 API 響應轉換為內部格式
                    const data = serverResponse.data;
                    
                    // 更新通道設定
                    this.channels = {
                        desktop: data.desktopNotifications,
                        sound: data.soundNotifications,
                        vibration: data.vibrationNotifications,
                        email: data.emailNotifications,
                        line: data.lineNotifications
                    };
                    
                    // 更新設定
                    this.settings = {
                        ...this.settings,
                        maxNotifications: data.maxNotifications,
                        autoExpiry: data.displayDuration * 1000,
                        groupSimilar: data.batchNotifications,
                        importantOnly: data.importantOnly,
                        quietHours: {
                            enabled: data.quietHours,
                            start: data.quietStart,
                            end: data.quietEnd
                        }
                    };
                    
                    console.log('✅ Notification settings loaded from server');
                } else {
                    throw new Error('Invalid server response format');
                }
            } else {
                throw new Error('Failed to load from server');
            }
        } catch (error) {
            console.warn('Failed to load settings from server, using local storage:', error);
            
            // 回退到本地存儲
            const saved = localStorage.getItem('visionflow_notification_settings');
            if (saved) {
                try {
                    const settings = JSON.parse(saved);
                    this.settings = { ...this.settings, ...settings.settings };
                    this.channels = { ...this.channels, ...settings.channels };
                    console.log('📱 Notification settings loaded from local storage');
                } catch (parseError) {
                    console.warn('Failed to parse local settings:', parseError);
                }
            }
        }
    }

    async saveSettings() {
        const settings = {
            settings: this.settings,
            channels: this.channels
        };

        try {
            // 嘗試保存到伺服器
            const response = await fetch('/api/notifications/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                console.log('✅ Notification settings saved to server');
            } else {
                throw new Error('Failed to save to server');
            }
        } catch (error) {
            console.warn('Failed to save settings to server:', error);
        }

        // 總是保存到本地存儲作為備份
        localStorage.setItem('visionflow_notification_settings', JSON.stringify(settings));
        console.log('📱 Notification settings saved to local storage');
    }

    createNotificationContainer() {
        if (document.getElementById('smart-notifications')) return;

        const container = document.createElement('div');
        container.id = 'smart-notifications';
        container.className = 'smart-notifications-container';
        container.innerHTML = `
            <div class="notifications-header">
                <div class="notifications-title">
                    <i class="fas fa-bell"></i>
                    <span>通知</span>
                    <span class="notification-count" id="notificationCount">0</span>
                </div>
                <div class="notifications-controls">
                    <button class="btn-clear-all" id="clearAllNotifications">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="btn-settings" id="notificationSettings">
                        <i class="fas fa-cog"></i>
                    </button>
                </div>
            </div>
            <div class="notifications-list" id="notificationsList"></div>
        `;
        
        document.body.appendChild(container);
        this.container = container;
        this.notificationsList = document.getElementById('notificationsList');
    }

    setupEventListeners() {
        // 清除所有通知
        document.getElementById('clearAllNotifications')?.addEventListener('click', () => {
            this.clearAll();
        });

        // 通知設定
        document.getElementById('notificationSettings')?.addEventListener('click', () => {
            this.showSettings();
        });

        // 鍵盤快捷鍵
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                this.toggleNotificationPanel();
            }
        });

        // 窗口失去焦點時的處理
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.onWindowBlur();
            } else {
                this.onWindowFocus();
            }
        });
    }

    async preloadSounds() {
        const sounds = {
            critical: '/static/sounds/critical-alert.mp3',
            high: '/static/sounds/high-alert.mp3',
            medium: '/static/sounds/medium-alert.mp3',
            success: '/static/sounds/success.mp3',
            info: '/static/sounds/info.mp3'
        };

        for (const [type, url] of Object.entries(sounds)) {
            try {
                const audio = new Audio(url);
                audio.preload = 'auto';
                this.soundCache.set(type, audio);
            } catch (error) {
                console.warn(`Failed to preload sound ${type}:`, error);
            }
        }
    }

    /**
     * 顯示通知
     * @param {Object} options - 通知選項
     */
    async show(options) {
        const notification = this.createNotification(options);
        
        // 檢查是否為安靜時間
        if (this.isQuietTime()) {
            notification.muted = true;
        }

        // 檢查是否需要分組
        if (this.settings.groupSimilar) {
            const grouped = this.groupSimilarNotification(notification);
            if (grouped) {
                this.updateGroupedNotification(grouped, notification);
                return grouped;
            }
        }

        // 添加到隊列
        this.notificationQueue.push(notification);
        
        // 如果沒有在處理，啟動處理
        if (!this.isProcessing) {
            this.processNotificationQueue();
        }

        return notification;
    }

    createNotification(options) {
        const id = this.generateId();
        const now = new Date();
        
        const notification = {
            id,
            title: options.title || '通知',
            message: options.message || '',
            type: options.type || 'info', // info, success, warning, error, critical
            priority: options.priority || 'medium',
            timestamp: now,
            persistent: options.persistent !== undefined ? options.persistent : this.settings.priorities[options.priority]?.persistent,
            actions: options.actions || [],
            data: options.data || {},
            grouped: false,
            groupCount: 1,
            muted: false,
            read: false,
            source: options.source || 'system'
        };

        return notification;
    }

    async processNotificationQueue() {
        if (this.isProcessing || this.notificationQueue.length === 0) return;
        
        this.isProcessing = true;

        while (this.notificationQueue.length > 0) {
            const notification = this.notificationQueue.shift();
            await this.displayNotification(notification);
            
            // 避免過快顯示通知
            await this.delay(100);
        }

        this.isProcessing = false;
    }

    async displayNotification(notification) {
        // 添加到通知列表
        this.notifications.unshift(notification);
        
        // 限制通知數量
        if (this.notifications.length > this.settings.maxNotifications) {
            const removed = this.notifications.splice(this.settings.maxNotifications);
            removed.forEach(n => this.removeNotificationElement(n.id));
        }

        // 創建通知元素
        this.createNotificationElement(notification);
        
        // 顯示桌面通知
        if (this.channels.desktop && !notification.muted) {
            this.showDesktopNotification(notification);
        }

        // 播放聲音
        if (this.channels.sound && !notification.muted) {
            this.playNotificationSound(notification);
        }

        // 振動
        if (this.channels.vibration && !notification.muted && 'vibrate' in navigator) {
            const pattern = this.getVibrationPattern(notification.priority);
            navigator.vibrate(pattern);
        }

        // 發送到外部通道
        this.sendToExternalChannels(notification);

        // 自動過期
        if (!notification.persistent) {
            setTimeout(() => {
                this.remove(notification.id);
            }, this.settings.autoExpiry);
        }

        // 更新計數
        this.updateNotificationCount();

        // 觸發事件
        this.dispatchEvent('notification:created', notification);
    }

    createNotificationElement(notification) {
        const element = document.createElement('div');
        element.className = `smart-notification ${notification.type} priority-${notification.priority}`;
        element.id = `notification-${notification.id}`;
        element.dataset.id = notification.id;

        const priorityConfig = this.settings.priorities[notification.priority];
        const timeAgo = this.formatTimeAgo(notification.timestamp);

        element.innerHTML = `
            <div class="notification-content">
                <div class="notification-header">
                    <div class="notification-icon" style="color: ${priorityConfig.color}">
                        ${this.getNotificationIcon(notification.type)}
                    </div>
                    <div class="notification-meta">
                        <div class="notification-title">${notification.title}</div>
                        <div class="notification-time">${timeAgo}</div>
                    </div>
                    <div class="notification-controls">
                        ${notification.grouped ? `<span class="group-count">${notification.groupCount}</span>` : ''}
                        <button class="btn-mark-read" data-id="${notification.id}">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn-close" data-id="${notification.id}">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <div class="notification-body">
                    <div class="notification-message">${notification.message}</div>
                    ${notification.actions.length > 0 ? this.createActionButtons(notification.actions, notification.id) : ''}
                </div>
                ${notification.data.preview ? `<div class="notification-preview">${notification.data.preview}</div>` : ''}
            </div>
            <div class="notification-progress"></div>
        `;

        // 添加事件監聽器
        this.setupNotificationEventListeners(element, notification);

        // 插入到列表頂部
        this.notificationsList.insertBefore(element, this.notificationsList.firstChild);

        // 添加進入動畫
        setTimeout(() => element.classList.add('show'), 10);

        return element;
    }

    setupNotificationEventListeners(element, notification) {
        // 標記為已讀
        element.querySelector('.btn-mark-read')?.addEventListener('click', () => {
            this.markAsRead(notification.id);
        });

        // 關閉通知
        element.querySelector('.btn-close')?.addEventListener('click', () => {
            this.remove(notification.id);
        });

        // 點擊通知本身
        element.querySelector('.notification-content')?.addEventListener('click', () => {
            this.handleNotificationClick(notification);
        });

        // 操作按鈕
        element.querySelectorAll('.notification-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                this.handleNotificationAction(notification, action);
            });
        });
    }

    createActionButtons(actions, notificationId) {
        return `
            <div class="notification-actions">
                ${actions.map(action => `
                    <button class="notification-action" data-action="${action.id}" data-notification="${notificationId}">
                        ${action.icon ? `<i class="${action.icon}"></i>` : ''}
                        ${action.label}
                    </button>
                `).join('')}
            </div>
        `;
    }

    showDesktopNotification(notification) {
        if (Notification.permission !== 'granted') return;

        const options = {
            body: notification.message,
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/badge-72x72.png',
            tag: notification.source,
            requireInteraction: notification.persistent,
            data: notification.data
        };

        const desktopNotification = new Notification(notification.title, options);
        
        desktopNotification.onclick = () => {
            window.focus();
            this.handleNotificationClick(notification);
            desktopNotification.close();
        };

        // 自動關閉
        if (!notification.persistent) {
            setTimeout(() => desktopNotification.close(), 5000);
        }
    }

    playNotificationSound(notification) {
        const soundType = this.getSoundType(notification.type, notification.priority);
        const audio = this.soundCache.get(soundType);
        
        if (audio) {
            audio.currentTime = 0;
            audio.play().catch(error => {
                console.warn('Failed to play notification sound:', error);
            });
        }
    }

    getSoundType(type, priority) {
        if (priority === 'critical') return 'critical';
        if (priority === 'high') return 'high';
        if (type === 'success') return 'success';
        return 'medium';
    }

    getVibrationPattern(priority) {
        const patterns = {
            critical: [200, 100, 200, 100, 200],
            high: [100, 50, 100],
            medium: [100],
            low: [50]
        };
        return patterns[priority] || patterns.medium;
    }

    getNotificationIcon(type) {
        const icons = {
            info: '<i class="fas fa-info-circle"></i>',
            success: '<i class="fas fa-check-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            critical: '<i class="fas fa-skull-crossbones"></i>',
            detection: '<i class="fas fa-eye"></i>',
            alert: '<i class="fas fa-bell"></i>',
            system: '<i class="fas fa-cog"></i>'
        };
        return icons[type] || icons.info;
    }

    groupSimilarNotification(newNotification) {
        const timeWindow = 5 * 60 * 1000; // 5分鐘
        const now = new Date();

        return this.notifications.find(existing => 
            existing.title === newNotification.title &&
            existing.source === newNotification.source &&
            existing.type === newNotification.type &&
            (now - existing.timestamp) < timeWindow
        );
    }

    updateGroupedNotification(existingNotification, newNotification) {
        existingNotification.groupCount += 1;
        existingNotification.grouped = true;
        existingNotification.timestamp = newNotification.timestamp;
        existingNotification.message = `${newNotification.message} (共 ${existingNotification.groupCount} 條相似通知)`;

        // 更新UI
        const element = document.getElementById(`notification-${existingNotification.id}`);
        if (element) {
            const groupCount = element.querySelector('.group-count');
            if (groupCount) {
                groupCount.textContent = existingNotification.groupCount;
            }
            
            const message = element.querySelector('.notification-message');
            if (message) {
                message.textContent = existingNotification.message;
            }

            const time = element.querySelector('.notification-time');
            if (time) {
                time.textContent = this.formatTimeAgo(existingNotification.timestamp);
            }

            // 添加更新動畫
            element.classList.add('updated');
            setTimeout(() => element.classList.remove('updated'), 1000);
        }
    }

    async sendToExternalChannels(notification) {
        // 發送郵件通知
        if (this.channels.email && (notification.priority === 'critical' || notification.priority === 'high')) {
            try {
                await this.sendEmailNotification(notification);
            } catch (error) {
                console.error('Failed to send email notification:', error);
            }
        }

        // 發送 LINE 通知
        if (this.channels.line && notification.priority === 'critical') {
            try {
                await this.sendLineNotification(notification);
            } catch (error) {
                console.error('Failed to send LINE notification:', error);
            }
        }
    }

    async sendEmailNotification(notification) {
        const response = await fetch('/api/notification/email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
            },
            body: JSON.stringify({
                title: notification.title,
                message: notification.message,
                priority: notification.priority,
                timestamp: notification.timestamp
            })
        });

        if (!response.ok) {
            throw new Error('Email notification failed');
        }
    }

    async sendLineNotification(notification) {
        const response = await fetch('/api/notification/line', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
            },
            body: JSON.stringify({
                message: `${notification.title}\n${notification.message}`,
                priority: notification.priority
            })
        });

        if (!response.ok) {
            throw new Error('LINE notification failed');
        }
    }

    /**
     * 發送測試通知
     * @param {string} channel - 通道類型
     */
    async sendTestNotification(channel) {
        try {
            const response = await fetch('/api/notifications/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                },
                body: JSON.stringify({ channel })
            });

            if (response.ok) {
                const result = await response.json();
                this.success('測試成功', `${channel} 通道測試通知已發送`);
                return result;
            } else {
                throw new Error(`Test failed for ${channel}`);
            }
        } catch (error) {
            this.error('測試失敗', `${channel} 通道測試失敗: ${error.message}`);
            throw error;
        }
    }

    /**
     * 便捷方法：顯示成功通知
     * @param {string} title - 通知標題
     * @param {string} message - 通知訊息
     * @param {Object} options - 額外選項
     */
    success(title, message, options = {}) {
        return this.show({
            title,
            message,
            type: 'success',
            priority: 'medium',
            ...options
        });
    }

    /**
     * 便捷方法：顯示錯誤通知
     * @param {string} title - 通知標題
     * @param {string} message - 通知訊息
     * @param {Object} options - 額外選項
     */
    error(title, message, options = {}) {
        return this.show({
            title,
            message,
            type: 'error',
            priority: 'high',
            persistent: true,
            ...options
        });
    }

    /**
     * 便捷方法：顯示資訊通知
     * @param {string} title - 通知標題
     * @param {string} message - 通知訊息
     * @param {Object} options - 額外選項
     */
    info(title, message, options = {}) {
        return this.show({
            title,
            message,
            type: 'info',
            priority: 'medium',
            ...options
        });
    }

    /**
     * 便捷方法：顯示警告通知
     * @param {string} title - 通知標題
     * @param {string} message - 通知訊息
     * @param {Object} options - 額外選項
     */
    warning(title, message, options = {}) {
        return this.show({
            title,
            message,
            type: 'warning',
            priority: 'high',
            ...options
        });
    }

    /**
     * 獲取通知歷史記錄
     * @param {Object} options - 查詢選項
     */
    async getNotificationHistory(options = {}) {
        try {
            const params = new URLSearchParams({
                page: options.page || 1,
                limit: options.limit || 50,
                priority: options.priority || '',
                type: options.type || '',
                start_date: options.startDate || '',
                end_date: options.endDate || ''
            });

            const response = await fetch(`/api/notifications/history?${params}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                }
            });

            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to fetch notification history');
            }
        } catch (error) {
            console.error('Error fetching notification history:', error);
            throw error;
        }
    }

    /**
     * 更新通知設定
     * @param {Object} newSettings - 新設定
     */
    async updateSettings(newSettings) {
        // 更新本地設定
        if (newSettings.channels) {
            this.channels = { ...this.channels, ...newSettings.channels };
        }
        
        if (newSettings.settings) {
            this.settings = { ...this.settings, ...newSettings.settings };
        }

        // 保存設定
        await this.saveSettings();

        // 觸發設定更新事件
        this.dispatchEvent('notification:settings_updated', {
            channels: this.channels,
            settings: this.settings
        });

        console.log('📋 Notification settings updated');
    }

    /**
     * 獲取統計數據
     */
    async getStatistics() {
        try {
            const response = await fetch('/api/notifications/statistics', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                }
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data) {
                    console.log('✅ Statistics loaded from API:', result.data);
                    return result.data;
                } else {
                    throw new Error('Invalid API response structure');
                }
            } else {
                throw new Error(`API request failed with status: ${response.status}`);
            }
        } catch (error) {
            console.error('Error fetching notification statistics:', error);
            
            // 回退到本地統計
            console.log('📋 Falling back to local statistics');
            return this.getLocalStatistics();
        }
    }

    /**
     * 獲取本地統計數據
     */
    getLocalStatistics() {
        const totalNotifications = this.notifications.length;
        const unreadNotifications = this.notifications.filter(n => !n.read).length;
        const todayNotifications = this.notifications.filter(n => {
            const today = new Date();
            const notificationDate = new Date(n.timestamp);
            return notificationDate.toDateString() === today.toDateString();
        }).length;

        const priorityStats = {
            critical: this.notifications.filter(n => n.priority === 'critical').length,
            high: this.notifications.filter(n => n.priority === 'high').length,
            medium: this.notifications.filter(n => n.priority === 'medium').length,
            low: this.notifications.filter(n => n.priority === 'low').length
        };

        const typeStats = {};
        this.notifications.forEach(n => {
            typeStats[n.type] = (typeStats[n.type] || 0) + 1;
        });

        return {
            totalNotifications,
            unreadNotifications,
            todayNotifications,
            readNotifications: totalNotifications - unreadNotifications,
            priorityStats,
            typeStats,
            averageResponseTime: this.calculateAverageResponseTime()
        };
    }

    /**
     * 計算平均回應時間
     */
    calculateAverageResponseTime() {
        const readNotifications = this.notifications.filter(n => n.read && n.readTime);
        if (readNotifications.length === 0) return 0;

        const totalResponseTime = readNotifications.reduce((total, n) => {
            return total + (n.readTime - n.timestamp);
        }, 0);

        return Math.round(totalResponseTime / readNotifications.length / 1000); // 秒
    }

    /**
     * WebSocket 連接管理
     */
    setupWebSocketConnection() {
        // 使用現有的 SocketIO 連接而不是創建新的 WebSocket
        if (window.io && window.socket) {
            console.log('🔗 Using existing SocketIO connection for notifications');
            
            // 監聽通知相關事件
            window.socket.on('notification', (data) => {
                this.handleWebSocketMessage(data);
            });
            
            // 加入通知房間
            window.socket.emit('join_room', { room: 'notifications' });
            
            this.dispatchEvent('notification:websocket_connected');
            return;
        }
        
        // 如果沒有現有的 SocketIO 連接，暫時禁用 WebSocket 功能
        console.warn('SocketIO not available, WebSocket notifications disabled');
    }

    /**
     * 處理 WebSocket 消息
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'notification':
                this.show(data.payload);
                break;
            case 'bulk_notifications':
                data.payload.forEach(notification => this.show(notification));
                break;
            case 'settings_update':
                this.updateSettings(data.payload);
                break;
            case 'clear_all':
                this.clearAll();
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    handleNotificationClick(notification) {
        this.markAsRead(notification.id);
        
        // 根據通知類型執行不同操作
        if (notification.data.url) {
            window.open(notification.data.url, '_blank');
        } else if (notification.data.action) {
            this.executeAction(notification.data.action, notification.data);
        }

        this.dispatchEvent('notification:clicked', notification);
    }

    handleNotificationAction(notification, actionId) {
        const action = notification.actions.find(a => a.id === actionId);
        if (action && action.handler) {
            action.handler(notification);
        }

        this.dispatchEvent('notification:action', { notification, actionId });
    }

    markAsRead(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (notification && !notification.read) {
            notification.read = true;
            notification.readTime = new Date();
            
            const element = document.getElementById(`notification-${id}`);
            if (element) {
                element.classList.add('read');
            }

            this.updateNotificationCount();
            this.dispatchEvent('notification:read', notification);
        }
    }

    remove(id) {
        const index = this.notifications.findIndex(n => n.id === id);
        if (index > -1) {
            const notification = this.notifications[index];
            this.notifications.splice(index, 1);
            this.removeNotificationElement(id);
            this.updateNotificationCount();
            this.dispatchEvent('notification:removed', notification);
        }
    }

    removeNotificationElement(id) {
        const element = document.getElementById(`notification-${id}`);
        if (element) {
            element.classList.add('removing');
            setTimeout(() => {
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
            }, 300);
        }
    }

    clearAll() {
        this.notifications.forEach(notification => {
            this.removeNotificationElement(notification.id);
        });
        this.notifications = [];
        this.updateNotificationCount();
        this.dispatchEvent('notification:clear_all');
    }

    updateNotificationCount() {
        const unreadCount = this.notifications.filter(n => !n.read).length;
        const countElement = document.getElementById('notificationCount');
        if (countElement) {
            countElement.textContent = unreadCount;
            countElement.style.display = unreadCount > 0 ? 'inline' : 'none';
        }

        // 更新頁面標題
        if (unreadCount > 0) {
            document.title = `(${unreadCount}) VisionFlow - 智能監控系統`;
        } else {
            document.title = 'VisionFlow - 智能監控系統';
        }

        // 更新favicon
        this.updateFavicon(unreadCount > 0);
    }

    updateFavicon(hasUnread) {
        const favicon = document.querySelector('link[rel="icon"]');
        if (favicon) {
            favicon.href = hasUnread 
                ? '/static/images/favicon-notification.png'
                : '/static/images/favicon-32x32.png';
        }
    }

    isQuietTime() {
        if (!this.settings.quietHours.enabled) return false;

        const now = new Date();
        const currentTime = now.getHours() * 60 + now.getMinutes();
        
        const [startHour, startMin] = this.settings.quietHours.start.split(':').map(Number);
        const [endHour, endMin] = this.settings.quietHours.end.split(':').map(Number);
        
        const startTime = startHour * 60 + startMin;
        const endTime = endHour * 60 + endMin;

        if (startTime < endTime) {
            return currentTime >= startTime && currentTime <= endTime;
        } else {
            return currentTime >= startTime || currentTime <= endTime;
        }
    }

    formatTimeAgo(timestamp) {
        const now = new Date();
        const diff = now - timestamp;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days} 天前`;
        if (hours > 0) return `${hours} 小時前`;
        if (minutes > 0) return `${minutes} 分鐘前`;
        return '剛剛';
    }

    generateId() {
        return 'notification_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    showSettings() {
        // 顯示設定對話框
        console.log('Show notification settings');
        // 實作設定UI
    }

    toggleNotificationPanel() {
        if (this.container) {
            this.container.classList.toggle('show');
        }
    }

    onWindowBlur() {
        // 窗口失去焦點時的處理
        this.windowFocused = false;
    }

    onWindowFocus() {
        // 窗口獲得焦點時的處理
        this.windowFocused = true;
        
        // 標記所有通知為已讀（可選）
        // this.markAllAsRead();
    }

    dispatchEvent(eventName, data) {
        const event = new CustomEvent(eventName, { detail: data });
        document.dispatchEvent(event);
    }

    startNotificationProcessor() {
        // 每30秒清理過期通知
        setInterval(() => {
            this.cleanupExpiredNotifications();
        }, 30000);

        // 每分鐘更新時間顯示
        setInterval(() => {
            this.updateTimestamps();
        }, 60000);
    }

    cleanupExpiredNotifications() {
        const expiredTime = new Date(Date.now() - 24 * 60 * 60 * 1000); // 24小時前
        const expired = this.notifications.filter(n => n.timestamp < expiredTime && n.read);
        
        expired.forEach(notification => {
            this.remove(notification.id);
        });
    }

    updateTimestamps() {
        this.notifications.forEach(notification => {
            const element = document.getElementById(`notification-${notification.id}`);
            if (element) {
                const timeElement = element.querySelector('.notification-time');
                if (timeElement) {
                    timeElement.textContent = this.formatTimeAgo(notification.timestamp);
                }
            }
        });
    }

    /**
     * 從 API 獲取設定
     */
    async getSettingsFromAPI() {
        try {
            const response = await fetch('/api/notifications/settings', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                }
            });

            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Failed to fetch settings from API');
            }
        } catch (error) {
            console.error('Error fetching settings from API:', error);
            throw error;
        }
    }

    /**
     * 清除所有通知歷史記錄
     */
    clearHistory() {
        this.notifications = [];
        this.updateNotificationCount();
        
        // 清除 UI 中的通知元素
        if (this.notificationsList) {
            this.notificationsList.innerHTML = '';
        }
        
        this.dispatchEvent('notification:history_cleared');
        console.log('📝 Notification history cleared');
    }

    /**
     * 獲取當前設定（用於向後相容）
     */
    getSettings() {
        return {
            channels: this.channels,
            settings: this.settings
        };
    }

    /**
     * 更新單個設定（用於向後相容）
     */
    updateSetting(key, value) {
        // 這個方法用於向後相容，實際更新通過 updateSettings 方法
        console.log(`Updating setting ${key} to ${value}`);
        
        // 觸發設定更新
        this.dispatchEvent('notification:setting_changed', { key, value });
    }

    /**
     * 重置為預設設定
     */
    async resetToDefaults() {
        const defaultSettings = {
            channels: {
                desktop: true,
                sound: true,
                vibration: true,
                email: false,
                line: false
            },
            settings: {
                maxNotifications: 50,
                autoExpiry: 30000,
                groupSimilar: true,
                quietHours: {
                    enabled: false,
                    start: '22:00',
                    end: '08:00'
                },
                importantOnly: false
            }
        };

        await this.updateSettings(defaultSettings);
        console.log('🔄 Settings reset to defaults');
    }

    // ...existing code...
}

// 創建全域實例
window.smartNotifications = new SmartNotificationSystem();

// 匯出類別
window.SmartNotificationSystem = SmartNotificationSystem;
