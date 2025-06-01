/**
 * VisionFlow PWA Service Worker
 * 提供離線功能和快取管理
 */

const CACHE_NAME = 'visionflow-v1.0.0';
const RUNTIME_CACHE = 'visionflow-runtime-v1.0.0';

// 需要快取的靜態資源
const STATIC_CACHE_URLS = [
    '/',
    '/static/css/advanced-dashboard.css',
    '/static/js/advanced-dashboard.js',
    '/static/js/app.js',
    '/advanced-dashboard',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js',
    'https://cdn.jsdelivr.net/npm/sweetalert2@11',
    'https://cdn.socket.io/4.6.2/socket.io.min.js'
];

// Service Worker 安裝事件
self.addEventListener('install', event => {
    console.log('[SW] Installing Service Worker');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                console.log('[SW] Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('[SW] Failed to cache static assets:', error);
            })
    );
});

// Service Worker 啟動事件
self.addEventListener('activate', event => {
    console.log('[SW] Activating Service Worker');
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(cacheName => {
                            return cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE;
                        })
                        .map(cacheName => {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            })
            .then(() => {
                console.log('[SW] Service Worker activated');
                return self.clients.claim();
            })
    );
});

// 網路請求攔截
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // 只處理 HTTP/HTTPS 請求
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // API 請求策略：網路優先，快取備用
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/health/')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // 靜態資源策略：快取優先，網路備用
    if (url.pathname.startsWith('/static/') || STATIC_CACHE_URLS.includes(url.pathname)) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // 頁面請求策略：網路優先，快取備用
    if (request.mode === 'navigate') {
        event.respondWith(networkFirst(request));
        return;
    }

    // 其他請求使用網路優先策略
    event.respondWith(networkFirst(request));
});

// 快取優先策略
async function cacheFirst(request) {
    try {
        const cache = await caches.open(CACHE_NAME);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            console.log('[SW] Cache hit:', request.url);
            return cachedResponse;
        }

        console.log('[SW] Cache miss, fetching from network:', request.url);
        const response = await fetch(request);
        
        if (response.status === 200) {
            cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        console.error('[SW] Cache first strategy failed:', error);
        return new Response('離線模式：資源暫時無法使用', {
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

// 網路優先策略
async function networkFirst(request) {
    try {
        const response = await fetch(request);
        
        if (response.status === 200) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);
        
        const cache = await caches.open(RUNTIME_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }

        // 如果是導航請求且沒有快取，返回離線頁面
        if (request.mode === 'navigate') {
            const offlineCache = await caches.open(CACHE_NAME);
            const offlinePage = await offlineCache.match('/');
            if (offlinePage) {
                return offlinePage;
            }
        }

        return new Response('離線模式：無法連接到伺服器', {
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

// 推送通知事件
self.addEventListener('push', event => {
    if (!event.data) {
        return;
    }

    try {
        const data = event.data.json();
        const options = {
            body: data.body || '您有新的監控警報',
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/badge-72x72.png',
            tag: data.tag || 'visionflow-notification',
            renotify: true,
            requireInteraction: data.urgent || false,
            actions: [
                {
                    action: 'view',
                    title: '查看詳情',
                    icon: '/static/images/view-icon.png'
                },
                {
                    action: 'dismiss',
                    title: '關閉',
                    icon: '/static/images/dismiss-icon.png'
                }
            ],
            data: data
        };

        event.waitUntil(
            self.registration.showNotification(data.title || 'VisionFlow 監控系統', options)
        );
    } catch (error) {
        console.error('[SW] Push notification error:', error);
    }
});

// 通知點擊事件
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/advanced-dashboard')
        );
    } else if (event.action === 'dismiss') {
        // 通知已經關閉，無需額外操作
    } else {
        // 默認操作：打開應用
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// 後台同步事件
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    try {
        // 同步離線時儲存的數據
        console.log('[SW] Performing background sync');
        
        // 這裡可以實現離線數據同步邏輯
        // 例如：上傳離線時儲存的監控數據
        
    } catch (error) {
        console.error('[SW] Background sync failed:', error);
    }
}

// 錯誤處理
self.addEventListener('error', event => {
    console.error('[SW] Service Worker error:', event.error);
});

self.addEventListener('unhandledrejection', event => {
    console.error('[SW] Unhandled promise rejection:', event.reason);
});

console.log('[SW] Service Worker script loaded');
