/**
 * 攝影機串流管理器
 * 處理攝影機串流預覽和管理
 */

class CameraStreamManager {
    constructor() {
        this.streams = new Map();
        this.previewContainer = null;
        this.isInitialized = false;
        this.maxRetries = 3;
        this.retryDelay = 2000;
        
        this.initializeManager();
    }

    initializeManager() {
        try {
            this.previewContainer = document.getElementById('camera-preview-container');
            this.isInitialized = true;
            console.log('[StreamManager] Camera stream manager initialized');
        } catch (error) {
            console.error('[StreamManager] Failed to initialize:', error);
        }
    }

    /**
     * 添加攝影機串流
     */
    async addCameraStream(cameraId, config = {}) {
        if (!this.isInitialized) {
            console.error('[StreamManager] Manager not initialized');
            return false;
        }

        try {
            const streamConfig = {
                cameraId,
                name: config.name || `攝影機 ${cameraId}`,
                url: config.url || `/api/camera/${cameraId}/stream`,
                resolution: config.resolution || '1920x1080',
                fps: config.fps || 30,
                autoplay: config.autoplay !== false,
                controls: config.controls !== false,
                ...config
            };

            // 創建串流元素
            const streamElement = this.createStreamElement(streamConfig);
            
            // 設置串流
            await this.setupStream(streamElement, streamConfig);
            
            // 添加到容器
            if (this.previewContainer) {
                this.previewContainer.appendChild(streamElement);
            }
            
            // 存儲串流信息
            this.streams.set(cameraId, {
                element: streamElement,
                config: streamConfig,
                status: 'loading',
                retryCount: 0
            });

            console.log(`[StreamManager] Added camera stream: ${cameraId}`);
            return true;

        } catch (error) {
            console.error(`[StreamManager] Failed to add camera stream ${cameraId}:`, error);
            return false;
        }
    }

    /**
     * 創建串流元素
     */
    createStreamElement(config) {
        const container = document.createElement('div');
        container.className = 'camera-stream-container';
        container.setAttribute('data-camera-id', config.cameraId);

        container.innerHTML = `
            <div class="stream-header">
                <h6 class="stream-title">${config.name}</h6>
                <div class="stream-controls">
                    <button class="btn btn-sm btn-outline-light stream-fullscreen" title="全螢幕">
                        <i class="fas fa-expand"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-light stream-snapshot" title="截圖">
                        <i class="fas fa-camera"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-light stream-settings" title="設定">
                        <i class="fas fa-cog"></i>
                    </button>
                </div>
            </div>
            <div class="stream-content">
                <video class="stream-video" 
                       ${config.autoplay ? 'autoplay' : ''} 
                       ${config.controls ? 'controls' : ''} 
                       muted 
                       playsinline>
                    <source type="application/x-mpegURL">
                    您的瀏覽器不支援此視頻格式
                </video>
                <div class="stream-overlay">
                    <div class="stream-status">
                        <div class="spinner-border text-light" role="status">
                            <span class="visually-hidden">載入中...</span>
                        </div>
                        <p class="status-text">正在載入串流...</p>
                    </div>
                </div>
                <div class="stream-info">
                    <span class="info-resolution">${config.resolution}</span>
                    <span class="info-fps">${config.fps} FPS</span>
                    <span class="info-status offline">離線</span>
                </div>
            </div>
        `;

        // 添加事件監聽器
        this.attachStreamEvents(container, config);

        return container;
    }

    /**
     * 設置串流
     */
    async setupStream(element, config) {
        const video = element.querySelector('.stream-video');
        const overlay = element.querySelector('.stream-overlay');
        const statusInfo = element.querySelector('.info-status');

        try {
            // 模擬獲取串流 URL（實際應該從 API 獲取）
            const streamResponse = await fetch(config.url);
            const streamData = await streamResponse.json();

            if (streamData.success) {
                // 模擬 WebRTC 或 HLS 串流
                if (this.isHLSSupported() && streamData.data.stream_url.includes('.m3u8')) {
                    await this.setupHLSStream(video, streamData.data.stream_url);
                } else {
                    // 備用方案：使用靜態圖片或模擬串流
                    await this.setupFallbackStream(video, config);
                }

                // 更新狀態
                overlay.style.display = 'none';
                statusInfo.textContent = '線上';
                statusInfo.className = 'info-status online';

                // 更新串流信息
                const streamInfo = this.streams.get(config.cameraId);
                if (streamInfo) {
                    streamInfo.status = 'online';
                }

            } else {
                throw new Error(streamData.error || '無法載入串流');
            }

        } catch (error) {
            console.error(`[StreamManager] Stream setup failed:`, error);
            await this.handleStreamError(element, config, error);
        }
    }

    /**
     * 設置 HLS 串流
     */
    async setupHLSStream(video, streamUrl) {
        if (window.Hls && window.Hls.isSupported()) {
            const hls = new window.Hls({
                enableWorker: false,
                lowLatencyMode: true,
                backBufferLength: 90
            });

            hls.loadSource(streamUrl);
            hls.attachMedia(video);

            return new Promise((resolve, reject) => {
                hls.on(window.Hls.Events.MANIFEST_PARSED, () => {
                    video.play().then(resolve).catch(reject);
                });

                hls.on(window.Hls.Events.ERROR, (event, data) => {
                    reject(new Error(`HLS Error: ${data.type} - ${data.details}`));
                });
            });
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            // 原生 HLS 支援（Safari）
            video.src = streamUrl;
            return video.play();
        } else {
            throw new Error('HLS not supported');
        }
    }

    /**
     * 設置備用串流（模擬）
     */
    async setupFallbackStream(video, config) {
        // 創建模擬串流畫布
        const canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 480;
        const ctx = canvas.getContext('2d');

        // 生成模擬畫面
        const generateFrame = () => {
            // 清除畫布
            ctx.fillStyle = '#1a1a1a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // 添加攝影機信息
            ctx.fillStyle = '#ffffff';
            ctx.font = '24px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(config.name, canvas.width / 2, 50);

            // 添加時間戳
            ctx.font = '16px Arial';
            ctx.fillText(new Date().toLocaleString(), canvas.width / 2, canvas.height - 30);

            // 添加模擬移動物體
            const time = Date.now() / 1000;
            const x = (Math.sin(time * 0.5) + 1) * (canvas.width - 100) / 2 + 50;
            const y = (Math.cos(time * 0.3) + 1) * (canvas.height - 150) / 2 + 100;

            ctx.fillStyle = '#3b82f6';
            ctx.beginPath();
            ctx.arc(x, y, 20, 0, 2 * Math.PI);
            ctx.fill();

            // 添加檢測框（模擬）
            if (Math.random() > 0.7) {
                ctx.strokeStyle = '#ef4444';
                ctx.lineWidth = 2;
                ctx.strokeRect(x - 25, y - 25, 50, 50);
                
                ctx.fillStyle = '#ef4444';
                ctx.font = '12px Arial';
                ctx.fillText('Person (89%)', x, y - 30);
            }
        };

        // 設置定時更新
        const frameInterval = setInterval(generateFrame, 1000 / config.fps);
        
        // 將畫布轉換為視頻串流
        const stream = canvas.captureStream(config.fps);
        video.srcObject = stream;

        // 存儲清理函數
        video.dataset.cleanup = () => {
            clearInterval(frameInterval);
        };

        return video.play();
    }

    /**
     * 處理串流錯誤
     */
    async handleStreamError(element, config, error) {
        const overlay = element.querySelector('.stream-overlay');
        const statusText = overlay.querySelector('.status-text');
        const statusInfo = element.querySelector('.info-status');
        const spinner = overlay.querySelector('.spinner-border');

        const streamInfo = this.streams.get(config.cameraId);
        if (streamInfo && streamInfo.retryCount < this.maxRetries) {
            // 重試連接
            streamInfo.retryCount++;
            statusText.textContent = `連接失敗，正在重試 (${streamInfo.retryCount}/${this.maxRetries})...`;
            
            setTimeout(() => {
                this.setupStream(element, config);
            }, this.retryDelay);

        } else {
            // 顯示錯誤狀態
            spinner.style.display = 'none';
            statusText.textContent = `連接失敗: ${error.message}`;
            statusInfo.textContent = '離線';
            statusInfo.className = 'info-status offline';

            if (streamInfo) {
                streamInfo.status = 'error';
            }
        }
    }

    /**
     * 附加串流事件
     */
    attachStreamEvents(container, config) {
        const video = container.querySelector('.stream-video');
        const fullscreenBtn = container.querySelector('.stream-fullscreen');
        const snapshotBtn = container.querySelector('.stream-snapshot');
        const settingsBtn = container.querySelector('.stream-settings');

        // 全螢幕功能
        fullscreenBtn.addEventListener('click', () => {
            this.toggleFullscreen(container);
        });

        // 截圖功能
        snapshotBtn.addEventListener('click', () => {
            this.takeSnapshot(config.cameraId);
        });

        // 設定功能
        settingsBtn.addEventListener('click', () => {
            this.showStreamSettings(config.cameraId);
        });

        // 視頻事件
        video.addEventListener('loadstart', () => {
            console.log(`[StreamManager] Stream loading started: ${config.cameraId}`);
        });

        video.addEventListener('loadeddata', () => {
            console.log(`[StreamManager] Stream data loaded: ${config.cameraId}`);
        });

        video.addEventListener('error', (e) => {
            console.error(`[StreamManager] Video error: ${config.cameraId}`, e);
        });
    }

    /**
     * 切換全螢幕
     */
    toggleFullscreen(container) {
        if (!document.fullscreenElement) {
            container.requestFullscreen().catch(err => {
                console.error('Cannot enter fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    /**
     * 截圖功能
     */
    async takeSnapshot(cameraId) {
        try {
            const streamInfo = this.streams.get(cameraId);
            if (!streamInfo) {
                throw new Error('Stream not found');
            }

            const video = streamInfo.element.querySelector('.stream-video');
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            ctx.drawImage(video, 0, 0);

            // 轉換為 Blob
            const blob = await new Promise(resolve => {
                canvas.toBlob(resolve, 'image/jpeg', 0.9);
            });

            // 下載截圖
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `camera_${cameraId}_${Date.now()}.jpg`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            // 顯示成功訊息
            if (window.Swal) {
                Swal.fire({
                    title: '截圖成功',
                    text: '截圖已保存到下載資料夾',
                    icon: 'success',
                    timer: 2000,
                    showConfirmButton: false
                });
            }

        } catch (error) {
            console.error('[StreamManager] Snapshot failed:', error);
            if (window.Swal) {
                Swal.fire({
                    title: '截圖失敗',
                    text: error.message,
                    icon: 'error'
                });
            }
        }
    }

    /**
     * 顯示串流設定
     */
    showStreamSettings(cameraId) {
        const streamInfo = this.streams.get(cameraId);
        if (!streamInfo) return;

        if (window.Swal) {
            Swal.fire({
                title: `${streamInfo.config.name} 設定`,
                html: `
                    <div class="text-start">
                        <div class="mb-3">
                            <label class="form-label">解析度</label>
                            <select class="form-select" id="resolution">
                                <option value="1920x1080" ${streamInfo.config.resolution === '1920x1080' ? 'selected' : ''}>1080p</option>
                                <option value="1280x720" ${streamInfo.config.resolution === '1280x720' ? 'selected' : ''}>720p</option>
                                <option value="640x480" ${streamInfo.config.resolution === '640x480' ? 'selected' : ''}>480p</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">幀率</label>
                            <select class="form-select" id="fps">
                                <option value="30" ${streamInfo.config.fps === 30 ? 'selected' : ''}>30 FPS</option>
                                <option value="25" ${streamInfo.config.fps === 25 ? 'selected' : ''}>25 FPS</option>
                                <option value="15" ${streamInfo.config.fps === 15 ? 'selected' : ''}>15 FPS</option>
                            </select>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="autoplay" ${streamInfo.config.autoplay ? 'checked' : ''}>
                            <label class="form-check-label" for="autoplay">自動播放</label>
                        </div>
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: '保存',
                cancelButtonText: '取消'
            }).then((result) => {
                if (result.isConfirmed) {
                    // 更新設定（這裡可以實現實際的設定更新邏輯）
                    console.log('[StreamManager] Settings updated for camera:', cameraId);
                }
            });
        }
    }

    /**
     * 移除攝影機串流
     */
    removeCameraStream(cameraId) {
        const streamInfo = this.streams.get(cameraId);
        if (streamInfo) {
            // 清理資源
            const video = streamInfo.element.querySelector('.stream-video');
            if (video.dataset.cleanup) {
                eval(video.dataset.cleanup)();
            }

            // 移除元素
            streamInfo.element.remove();
            
            // 清除記錄
            this.streams.delete(cameraId);
            
            console.log(`[StreamManager] Removed camera stream: ${cameraId}`);
        }
    }

    /**
     * 獲取串流狀態
     */
    getStreamStatus(cameraId) {
        const streamInfo = this.streams.get(cameraId);
        return streamInfo ? streamInfo.status : 'not_found';
    }

    /**
     * 檢查 HLS 支援
     */
    isHLSSupported() {
        return !!(window.Hls && window.Hls.isSupported());
    }

    /**
     * 清理所有串流
     */
    cleanup() {
        this.streams.forEach((streamInfo, cameraId) => {
            this.removeCameraStream(cameraId);
        });
        this.streams.clear();
    }
}

// 創建全域實例
window.CameraStreamManager = CameraStreamManager;
