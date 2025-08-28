#!/bin/bash

# VisionFlow 最小化啟動腳本
# 用於測試基本功能，避免系統過載

echo "================================"
echo "VisionFlow 最小化測試啟動"
echo "================================"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 建立必要的環境變數檔案
if [ ! -f .env ]; then
    echo -e "${YELLOW}建立 .env 檔案...${NC}"
    cat > .env << EOF
# PostgreSQL
POSTGRES_USER=admin
POSTGRES_PASSWORD=visionflow123
POSTGRES_DB=visionflow

# Redis
REDIS_PASSWORD=

# Flask
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development
FLASK_DEBUG=true

# Ports
BACKEND_PORT=5000
DB_PORT=5433
REDIS_PORT=6379
CAMERA_PORT=15440

# Performance Settings (降低資源使用)
GUNICORN_WORKERS=2
MAX_CAMERAS=2
YOLO_MODEL=yolo11n.pt
PROCESS_FPS=10
EOF
    echo -e "${GREEN}✓ .env 檔案已建立${NC}"
fi

# 2. 停止所有現有服務
echo -e "\n${YELLOW}停止現有服務...${NC}"
docker-compose -f docker-compose.optimized.yaml down

# 3. 只啟動核心服務（不包含 AI 辨識）
echo -e "\n${YELLOW}啟動核心服務...${NC}"
cat > docker-compose.minimal.yaml << 'EOF'
version: "3.8"

services:
  # PostgreSQL Database
  db:
    container_name: 'visionflow_db'
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-visionflow123}
      POSTGRES_DB: ${POSTGRES_DB:-visionflow}
    ports:
      - "${DB_PORT:-5433}:5432"
    volumes:
      - ./db/:/var/lib/postgresql/data/
    networks:
      - visionflow-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    container_name: 'visionflow_redis'
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "${REDIS_PORT:-6379}:6379"
    networks:
      - visionflow-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Web Backend (簡化版)
  backend:
    container_name: 'visionflow_backend'
    build:
      context: ./web
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      FLASK_ENV: development
      FLASK_DEBUG: "true"
      SECRET_KEY: ${SECRET_KEY:-development-key}
      DATABASE_URL: postgresql://admin:visionflow123@db:5432/visionflow
      REDIS_HOST: redis
      REDIS_PORT: 6379
    volumes:
      - ./web:/app
      - ./shared:/app/shared
      - ./logs:/app/logs
    ports:
      - "${BACKEND_PORT:-5000}:5000"
    depends_on:
      - db
      - redis
    command: >
      sh -c "
        echo 'Waiting for database...' &&
        sleep 10 &&
        python -m flask db upgrade &&
        python app.py
      "
    networks:
      - visionflow-network

networks:
  visionflow-network:
    driver: bridge
EOF

# 4. 啟動最小化服務
docker-compose -f docker-compose.minimal.yaml up -d

# 5. 等待服務啟動
echo -e "\n${YELLOW}等待服務啟動...${NC}"
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""

# 6. 檢查服務狀態
echo -e "\n${YELLOW}檢查服務狀態...${NC}"
docker-compose -f docker-compose.minimal.yaml ps

# 7. 測試 API
echo -e "\n${YELLOW}測試 API 連接...${NC}"

# 測試健康檢查
if curl -s -f http://localhost:5000/health/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 後端 API 正常${NC}"
else
    echo -e "${RED}✗ 後端 API 無回應${NC}"
fi

# 8. 建立測試使用者
echo -e "\n${YELLOW}建立測試使用者...${NC}"
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123","email":"demo@visionflow.com"}' \
  2>/dev/null | python3 -m json.tool

# 9. 提供訪問資訊
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}系統已啟動！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "訪問資訊："
echo "  • 前端介面: http://localhost:5000"
echo "  • 測試帳號: demo / demo123"
echo ""
echo "可用命令："
echo "  • 查看日誌: docker-compose -f docker-compose.minimal.yaml logs -f backend"
echo "  • 停止服務: docker-compose -f docker-compose.minimal.yaml down"
echo "  • 重啟服務: docker-compose -f docker-compose.minimal.yaml restart"
echo ""
echo -e "${YELLOW}注意：這是最小化測試版本，未包含攝影機和 AI 辨識功能${NC}"