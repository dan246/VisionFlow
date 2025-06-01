#!/bin/bash

# VisionFlow 系統完整測試腳本
# 用於驗證 PWA 功能和智能通知系統

set -e

echo "🚀 VisionFlow 系統部署與測試"
echo "======================================"

# 檢查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

echo "✅ Docker 環境檢查通過"

# 設置環境變數
export POSTGRES_DB=visionflow
export POSTGRES_USER=visionflow_user
export POSTGRES_PASSWORD=secure_password_2024
export FLASK_ENV=development
export DEBUG=true

echo "📝 環境變數已設置"

# 檢查是否存在 .env 文件
if [ ! -f .env ]; then
    echo "📄 創建 .env 文件..."
    cat > .env << EOF
# Database Configuration
POSTGRES_DB=visionflow
POSTGRES_USER=visionflow_user
POSTGRES_PASSWORD=secure_password_2024
DATABASE_URL=postgresql://visionflow_user:secure_password_2024@db:5432/visionflow

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Flask Configuration
FLASK_ENV=development
FLASK_PORT=5000
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=true

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=2592000

# API Configuration
API_VERSION=v1
CORS_ORIGINS=*

# Notification Configuration
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_LINE_NOTIFICATIONS=true
EMAIL_RATE_LIMIT=10
LINE_RATE_LIMIT=20

# AI Configuration
AI_MODEL_PATH=/app/models
DETECTION_CONFIDENCE=0.5
DETECTION_NMS_THRESHOLD=0.4
MAX_DETECTION_AREAS=10

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_FORMAT=detailed

# Performance Configuration
MAX_WORKERS=4
WORKER_TIMEOUT=30
MAX_CONNECTIONS=100
CONNECTION_TIMEOUT=30
EOF
    echo "✅ .env 文件已創建"
fi

# 清理舊的容器和網路
echo "🧹 清理舊的容器..."
docker-compose down --remove-orphans 2>/dev/null || true
docker system prune -f --volumes 2>/dev/null || true

# 準備部署環境和權限
echo "🔧 準備部署環境..."
mkdir -p logs camera_data shared
chmod 755 logs camera_data shared

# 確保日誌目錄權限正確
if [ -d "logs" ]; then
    echo "📁 設置 logs 目錄權限..."
    chmod -R 755 logs
fi

# 創建必要的子目錄
mkdir -p logs/backend logs/camera logs/worker
chmod -R 755 logs/

echo "🏗️ 啟動 VisionFlow 系統..."

# 使用優化版的 docker-compose 文件
if [ -f docker-compose.optimized.yaml ]; then
    echo "📦 使用優化版 Docker Compose 配置"
    docker-compose -f docker-compose.optimized.yaml up -d --build
else
    echo "📦 使用標準 Docker Compose 配置"
    docker-compose up -d --build
fi

echo "⏳ 等待服務啟動..."
sleep 30

# 健康檢查
echo "🏥 執行健康檢查..."

# 檢查後端服務
echo "🔍 檢查後端服務..."
for i in {1..10}; do
    if curl -f http://localhost:5001/health >/dev/null 2>&1; then
        echo "✅ 後端服務健康"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ 後端服務啟動失敗"
        docker-compose logs web
        exit 1
    fi
    echo "⏳ 等待後端服務啟動... (${i}/10)"
    sleep 5
done

# 檢查前端服務
echo "🔍 檢查前端服務..."
if curl -f http://localhost:5000 >/dev/null 2>&1; then
    echo "✅ 前端服務健康"
else
    echo "❌ 前端服務啟動失敗"
    docker-compose logs web
fi

# 檢查資料庫
echo "🔍 檢查資料庫連接..."
if docker-compose exec -T db pg_isready -U visionflow_user >/dev/null 2>&1; then
    echo "✅ 資料庫連接正常"
else
    echo "❌ 資料庫連接失敗"
    docker-compose logs db
fi

# 檢查 Redis
echo "🔍 檢查 Redis 連接..."
if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis 連接正常"
else
    echo "❌ Redis 連接失敗"
    docker-compose logs redis
fi

# API 測試
echo "🧪 執行 API 測試..."

# 註冊測試用戶
echo "👤 註冊測試用戶..."
TEST_USER_RESPONSE=$(curl -s -X POST http://localhost:5001/auth/register \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "email": "test@visionflow.com",
        "password": "testpassword123"
    }' || echo '{"error": "registration failed"}')

echo "註冊回應: $TEST_USER_RESPONSE"

# 登入測試
echo "🔐 測試用戶登入..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5001/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "password": "testpassword123"
    }' || echo '{"error": "login failed"}')

echo "登入回應: $LOGIN_RESPONSE"

# 提取訪問令牌
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$ACCESS_TOKEN" ]; then
    echo "✅ 用戶登入成功，獲得訪問令牌"
    
    # 測試通知設定 API
    echo "🔔 測試通知設定 API..."
    NOTIFICATION_SETTINGS=$(curl -s -X GET http://localhost:5001/api/notifications/settings \
        -H "Authorization: Bearer $ACCESS_TOKEN" || echo '{"error": "api failed"}')
    
    echo "通知設定: $NOTIFICATION_SETTINGS"
    
    # 測試通知測試功能
    echo "📢 測試通知發送..."
    TEST_NOTIFICATION=$(curl -s -X POST http://localhost:5001/api/notifications/test \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "channel": "desktop",
            "message": "測試通知"
        }' || echo '{"error": "notification test failed"}')
    
    echo "測試通知回應: $TEST_NOTIFICATION"
else
    echo "❌ 用戶登入失敗，無法進行進階測試"
fi

# PWA 功能檢查
echo "📱 檢查 PWA 功能..."

# 檢查 manifest.json
if curl -f http://localhost:5000/static/manifest.json >/dev/null 2>&1; then
    echo "✅ PWA Manifest 可用"
else
    echo "❌ PWA Manifest 不可用"
fi

# 檢查 service worker
if curl -f http://localhost:5000/static/js/service-worker.js >/dev/null 2>&1; then
    echo "✅ Service Worker 可用"
else
    echo "❌ Service Worker 不可用"
fi

# 檢查智能通知系統
if curl -f http://localhost:5000/static/js/smart-notifications.js >/dev/null 2>&1; then
    echo "✅ 智能通知系統 JavaScript 可用"
else
    echo "❌ 智能通知系統 JavaScript 不可用"
fi

# 顯示服務狀態
echo ""
echo "📊 服務狀態總覽:"
echo "=================="
docker-compose ps

echo ""
echo "🎯 測試完成！"
echo "=================="
echo "🌐 前端地址: http://localhost:5000"
echo "🔌 後端 API: http://localhost:5001"
echo "📊 系統健康檢查: http://localhost:5001/health"
echo "📱 PWA Manifest: http://localhost:5000/static/manifest.json"
echo "⚙️ Service Worker: http://localhost:5000/static/js/service-worker.js"
echo ""
echo "🔧 如需停止服務，執行: docker-compose down"
echo "📋 如需查看日誌，執行: docker-compose logs -f"
echo ""
echo "🎉 VisionFlow 智能監控系統已就緒！"
