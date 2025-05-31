<div align="center">

# 🚀 VisionFlow 部署指南

**完整的生產環境部署手冊**

[![Docker](https://img.shields.io/badge/Docker-20.10+-blue?style=flat-square&logo=docker)](https://www.docker.com/)
[![Production Ready](https://img.shields.io/badge/Production-Ready-success?style=flat-square)](.)
[![Cloud Support](https://img.shields.io/badge/Cloud-AWS%20%7C%20GCP%20%7C%20Azure-orange?style=flat-square)](.)

</div>

---

## 📋 目錄

- [⚡ 快速部署](#-快速部署)
- [🛠️ 環境要求](#️-環境要求)
- [⚙️ 配置設定](#️-配置設定)
- [🐳 部署選項](#-部署選項)
- [📊 監控與維護](#-監控與維護)
- [🔧 故障排除](#-故障排除)
- [☁️ 雲端部署](#️-雲端部署)

---

## ⚡ 快速部署

### 🎯 一鍵部署（推薦）

<details>
<summary><strong>📦 標準生產環境</strong></summary>

```bash
# 1️⃣ 複製專案
git clone https://github.com/yourusername/VisionFlow.git
cd VisionFlow

# 2️⃣ 配置環境變數
cp .env.example .env
# 編輯 .env 檔案設定您的參數

# 3️⃣ 啟動所有服務
docker-compose -f docker-compose.optimized.yaml up -d

# 4️⃣ 初始化資料庫
docker-compose -f docker-compose.optimized.yaml exec backend flask db upgrade

# 5️⃣ 驗證部署
curl -f http://localhost:5001/health || echo "Deployment failed"
```

</details>

<details>
<summary><strong>🔧 開發環境</strong></summary>

```bash
# 開發環境部署
docker-compose up -d

# 啟動所有工作節點
docker-compose -f docker-compose-redis.yaml up -d

# 檢查服務狀態
docker-compose ps
```

</details>

### ✅ 部署驗證清單

| 服務 | 檢查項目 | 預期結果 |
|------|----------|----------|
| 🌐 **Backend** | `curl http://localhost:5001/health` | ✅ Status: OK |
| 📹 **Camera Controller** | `curl http://localhost:15440/camera_status` | ✅ Camera services active |
| 🗄️ **Database** | `docker-compose exec db pg_isready` | ✅ PostgreSQL ready |
| 📦 **Redis** | `docker-compose exec redis redis-cli ping` | ✅ PONG |

---

## 🛠️ 環境要求

### 💻 硬體需求

| 配置等級 | CPU | RAM | 儲存空間 | 網路 |
|----------|-----|-----|----------|------|
| **最低配置** | 2 cores | 4 GB | 20 GB | 100 Mbps |
| **建議配置** | 4 cores | 8 GB | 50 GB | 1 Gbps |
| **高效能配置** | 8+ cores | 16+ GB | 100+ GB | 10 Gbps |

### 🐳 軟體需求
  - CPU: 2 核心
  - RAM: 4GB
  - 存儲: 20GB 可用空間
  
- **建議配置:**
  - CPU: 4+ 核心
  - RAM: 8GB+
  - 存儲: 50GB+ SSD
  - GPU: NVIDIA GPU (可選，用於加速推理)

### 軟體要求
- Docker 20.10+
- Docker Compose 2.0+
- Git
- (可選) NVIDIA Docker 支援用於 GPU

---

## ⚙️ 詳細配置設定

> **全面的系統配置指南，支援多環境部署**

### 🏗️ 核心基礎設定

<details>
<summary><b>🗄️ 資料庫配置</b></summary>

```bash
# PostgreSQL 主資料庫
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=visionflow_user
POSTGRES_PASSWORD=your_ultra_secure_password_here
POSTGRES_DB=vision_notify

# 連接池設定
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=0
POSTGRES_POOL_TIMEOUT=30
POSTGRES_POOL_RECYCLE=3600
```

**🔧 進階設定:**
- **連接池**: 優化資料庫連接效能
- **SSL 模式**: 生產環境建議啟用 `POSTGRES_SSLMODE=require`
- **備份策略**: 建議每日自動備份

</details>

<details>
<summary><b>⚡ Redis 快取配置</b></summary>

```bash
# Redis 快取伺服器
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_secure_password
REDIS_DB=0

# 效能調校
REDIS_MAX_CONNECTIONS=50
REDIS_CONNECTION_POOL_KWARGS='{"retry_on_timeout": true, "socket_keepalive": true}'
REDIS_SOCKET_TIMEOUT=5
```

**⚡ 效能優化:**
- **持久化**: 配置 RDB + AOF 雙重持久化
- **記憶體限制**: 設定 `maxmemory-policy allkeys-lru`
- **連接池**: 最佳化連接管理

</details>

<details>
<summary><b>🌐 Flask 應用配置</b></summary>

```bash
# 應用基礎設定
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
APP_NAME=VisionFlow
APP_VERSION=2.0.0

# Web 伺服器設定
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_MAX_REQUESTS=1000
GUNICORN_TIMEOUT=30

# 安全設定
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=86400
```

</details>

### 🤖 AI 模型配置

<details>
<summary><b>🎯 模型啟用設定</b></summary>

```bash
# 模型啟用/停用控制
MODEL1_ENABLED=true     # 通用物件檢測 (推薦)
MODEL2_ENABLED=false    # 室內物件檢測
MODEL3_ENABLED=false    # 廚房物件檢測
MODEL4_ENABLED=false    # 戶外環境檢測
MODEL5_ENABLED=false    # 人臉檢測 (隱私考量)

# 模型路徑配置
MODEL1_PATH=/models/yolo_general.pt
MODEL2_PATH=/models/yolo_indoor.pt
MODEL3_PATH=/models/yolo_kitchen.pt
```

</details>

<details>
<summary><b>📊 信心度閾值調整</b></summary>

```bash
# 通用模型閾值
MODEL1_CONF=0.5              # 預設信心度
MODEL1_CONF_PERSON=0.7       # 人員檢測
MODEL1_CONF_CAR=0.6          # 車輛檢測
MODEL1_CONF_BICYCLE=0.6      # 自行車檢測

# 動物檢測
MODEL1_CONF_DOG=0.8          # 狗
MODEL1_CONF_CAT=0.8          # 貓
MODEL1_CONF_BIRD=0.7         # 鳥類

# 特殊場景調整
MODEL1_CONF_NIGHT_MODE=0.4   # 夜間模式 (降低閾值)
MODEL1_CONF_WEATHER_MODE=0.6 # 惡劣天氣模式
```

**🎯 閾值調整建議:**
- **安全區域**: 提高閾值 (0.7-0.9) 減少誤報
- **關鍵區域**: 降低閾值 (0.3-0.5) 提高敏感度
- **夜間模式**: 適度降低閾值補償光線不足

</details>

### 📧 通知系統配置

<details>
<summary><b>📨 電子郵件通知</b></summary>

```bash
# 電子郵件啟用控制
ENABLE_EMAIL_NOTIFICATIONS=true
EMAIL_RATE_LIMIT=10          # 每小時最大郵件數
EMAIL_BATCH_SIZE=5           # 批次發送大小

# SMTP 伺服器設定
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=visionflow@company.com
SMTP_PASSWORD=your_app_specific_password
EMAIL_FROM=VisionFlow Security <visionflow@company.com>

# 郵件模板設定
EMAIL_TEMPLATE_ALERT=alert_template.html
EMAIL_TEMPLATE_REPORT=daily_report.html
EMAIL_LOGO_URL=https://your-domain.com/logo.png
```

**📧 設定建議:**
- **Gmail**: 使用應用程式專用密碼
- **企業郵件**: 配置 SMTP 認證
- **模板**: 自訂品牌化郵件樣式

</details>

<details>
<summary><b>💬 LINE 即時通知</b></summary>

```bash
# LINE Notify 設定
ENABLE_LINE_NOTIFICATIONS=true
LINE_RATE_LIMIT=50           # 每小時最大通知數
LINE_NOTIFY_TOKEN=your_line_notify_token_here

# 多群組支援
LINE_GROUP_SECURITY=token_for_security_group
LINE_GROUP_MANAGEMENT=token_for_management_group
LINE_GROUP_TECHNICAL=token_for_technical_group

# 通知等級設定
LINE_NOTIFICATION_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LINE_INCLUDE_IMAGES=true      # 是否附加檢測圖片
LINE_MAX_IMAGE_SIZE=1048576   # 最大圖片大小 (1MB)
```

</details>

---

## 🚀 多環境部署選項

<details>
<summary><b>🔧 開發環境部署</b></summary>

**適用場景:** 本地開發、功能測試、Debug

```bash
# 1. 設定開發環境變數
export FLASK_ENV=development
export DEBUG=true
export LOG_LEVEL=DEBUG

# 2. 使用開發配置啟動
docker-compose -f docker-compose.dev.yaml up

# 3. 啟用熱重載
export FLASK_RELOAD=true
docker-compose up --build
```

**🔧 開發環境特色:**
- ✅ 熱重載功能
- ✅ 詳細除錯日誌
- ✅ 簡化驗證流程
- ✅ 測試資料自動載入

</details>

<details>
<summary><b>🏭 生產環境部署</b></summary>

**適用場景:** 正式營運、高可用性需求

```bash
# 1. 生成安全密鑰
export SECRET_KEY=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -hex 16)
export REDIS_PASSWORD=$(openssl rand -hex 16)

# 2. 設定生產環境變數
export FLASK_ENV=production
export DEBUG=false
export LOG_LEVEL=WARNING

# 3. 啟用安全配置
export HTTPS_ONLY=true
export SECURE_HEADERS=true
export RATE_LIMITING=true

# 4. 部署生產環境
docker-compose -f docker-compose.prod.yaml up -d
```

**🛡️ 生產環境安全特色:**
- ✅ HTTPS 強制重導向
- ✅ 安全標頭設定
- ✅ 速率限制保護
- ✅ 自動備份機制

</details>

<details>
<summary><b>🚄 GPU 加速部署</b></summary>

**適用場景:** 高效能推理、大量攝影機

**前置需求:**
```bash
# 安裝 NVIDIA Docker 支援
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

**GPU 部署:**
```bash
# 1. 啟用 GPU 支援
export GPU_ENABLED=true
export CUDA_VISIBLE_DEVICES=0,1  # 指定 GPU

# 2. GPU 記憶體配置
export GPU_MEMORY_FRACTION=0.8   # 使用 80% GPU 記憶體
export GPU_ALLOW_GROWTH=true     # 動態記憶體分配

# 3. 部署 GPU 版本
docker-compose -f docker-compose.gpu.yaml up -d
```

**⚡ GPU 效能提升:**
- 🚀 推理速度提升 5-10x
- 📹 支援更多並發攝影機
- 🎯 更高精度的模型

</details>

<details>
<summary><b>🔄 高可用性叢集部署</b></summary>

**適用場景:** 關鍵業務、零停機需求

```bash
# 1. 負載平衡設定
export LOAD_BALANCER=nginx
export BACKEND_REPLICAS=3
export REDIS_CLUSTER=true

# 2. 資料庫高可用
export POSTGRES_MASTER=postgres-master
export POSTGRES_REPLICA=postgres-replica
export DB_REPLICATION=true

# 3. 服務擴展
docker-compose -f docker-compose.cluster.yaml up -d \
  --scale backend=3 \
  --scale objectrecognition=2 \
  --scale redis-worker=5
```

**🏗️ 叢集架構優勢:**
- ⚡ 自動故障轉移
- 📈 水平擴展能力
- 🔄 滾動更新支援
- 📊 負載分散處理

</details>

---

## 📊 監控與維護

> **全面的系統監控和維護指南**

### 🏥 健康檢查系統

<details>
<summary><b>🔍 健康檢查端點</b></summary>

| 端點 | 用途 | 回應時間 | 檢查項目 |
|------|------|----------|----------|
| `GET /health` | 基本健康檢查 | < 100ms | 服務狀態 |
| `GET /health/detailed` | 詳細健康檢查 | < 500ms | 資料庫、Redis、磁碟 |
| `GET /health/readiness` | 準備狀態檢查 | < 200ms | 依賴服務連接 |
| `GET /health/liveness` | 存活狀態檢查 | < 50ms | 應用程式核心功能 |

**檢查範例:**
```bash
# 基本健康檢查
curl -X GET http://localhost:5000/health

# 詳細健康檢查
curl -X GET http://localhost:5000/health/detailed

# 檢查回應格式
{
  "status": "healthy",
  "timestamp": "2024-01-20T17:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ai_models": "healthy"
  },
  "uptime": "5d 12h 30m",
  "version": "2.0.0"
}
```

</details>

### 📋 日誌監控

<details>
<summary><b>📊 即時日誌監控</b></summary>

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f backend
docker-compose logs -f objectrecognition
docker-compose logs -f camera-controller

# 查看最近 100 行日誌
docker-compose logs -f --tail=100

# 按時間篩選日誌
docker-compose logs -f --since="2024-01-20T10:00:00"

# 搜尋特定關鍵字
docker-compose logs | grep "ERROR"
docker-compose logs | grep "camera_id"
```

**🔧 日誌等級配置:**
```bash
# 開發環境
export LOG_LEVEL=DEBUG

# 測試環境  
export LOG_LEVEL=INFO

# 生產環境
export LOG_LEVEL=WARNING
```

</details>

<details>
<summary><b>📈 效能監控</b></summary>

```bash
# 即時容器資源監控
docker stats

# 查看詳細系統資源
docker system df
docker system events

# 服務狀態檢查
docker-compose ps

# 特定容器詳細資訊
docker inspect <container_name>

# 網路連接監控
docker network ls
docker network inspect visionflow_default
```

**📊 關鍵效能指標:**
- CPU 使用率 < 80%
- 記憶體使用率 < 85%
- 磁碟空間使用率 < 90%
- 網路延遲 < 100ms
- 資料庫連接數 < 最大連接數的 80%

</details>

### 💾 備份與恢復策略

<details>
<summary><b>🗄️ 資料庫備份</b></summary>

**自動備份腳本:**
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="visionflow_postgres_1"

# 建立備份目錄
mkdir -p $BACKUP_DIR

# 執行資料庫備份
docker exec $CONTAINER_NAME pg_dump -U $POSTGRES_USER $POSTGRES_DB > \
  $BACKUP_DIR/backup_$DATE.sql

# 壓縮備份檔案
gzip $BACKUP_DIR/backup_$DATE.sql

# 清理 7 天前的備份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "資料庫備份完成: backup_$DATE.sql.gz"
```

**設定定時備份:**
```bash
# 編輯 crontab
crontab -e

# 每日凌晨 2 點備份
0 2 * * * /path/to/backup_database.sh

# 每週日進行完整備份
0 3 * * 0 /path/to/full_backup.sh
```

</details>

<details>
<summary><b>🔄 資料恢復</b></summary>

```bash
# 從備份恢復資料庫
#!/bin/bash
BACKUP_FILE="backup_20240120_020000.sql.gz"
CONTAINER_NAME="visionflow_postgres_1"

# 解壓備份檔案
gunzip $BACKUP_FILE

# 停止相關服務
docker-compose stop backend objectrecognition

# 恢復資料庫
docker exec -i $CONTAINER_NAME psql -U $POSTGRES_USER $POSTGRES_DB < \
  ${BACKUP_FILE%.gz}

# 重新啟動服務
docker-compose start backend objectrecognition

echo "資料庫恢復完成"
```

</details>

<details>
<summary><b>📁 檔案系統備份</b></summary>

```bash
# 模型檔案備份
rsync -av --delete /path/to/models/ /backup/models/

# 設定檔備份
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  .env docker-compose*.yaml

# 影像檔案備份 (選擇性)
rsync -av --delete /path/to/saved_images/ /backup/images/
```

</details>

---

## 🚨 故障排除指南

<details>
<summary><b>🔧 常見問題解決</b></summary>

### 🚫 服務無法啟動

**問題:** 容器啟動失敗
```bash
# 檢查容器狀態
docker-compose ps

# 查看錯誤日誌
docker-compose logs <service_name>

# 檢查埠號衝突
netstat -tulpn | grep :5000
```

**解決方案:**
1. 檢查環境變數配置
2. 確認埠號未被佔用
3. 檢查磁碟空間是否充足
4. 驗證 Docker 映像完整性

### 🗄️ 資料庫連接問題

**問題:** 無法連接到 PostgreSQL
```bash
# 測試資料庫連接
docker exec -it postgres_container psql -U username -d database

# 檢查資料庫日誌
docker logs postgres_container
```

**解決方案:**
1. 驗證資料庫憑證
2. 檢查網路配置
3. 確認資料庫服務狀態
4. 檢查防火牆設定

### ⚡ Redis 快取問題

**問題:** Redis 連接異常
```bash
# 測試 Redis 連接
docker exec -it redis_container redis-cli ping

# 檢查 Redis 配置
docker exec redis_container redis-cli CONFIG GET "*"
```

### 🎥 攝影機串流問題

**問題:** 無法獲取攝影機串流
```bash
# 測試 RTSP 連接
ffprobe rtsp://camera_ip:port/stream

# 檢查網路連通性
ping camera_ip
telnet camera_ip port
```

</details>

<details>
<summary><b>📊 效能調優建議</b></summary>

### 🚀 系統優化

**記憶體優化:**
```bash
# 調整 Docker 記憶體限制
docker update --memory="2g" container_name

# PostgreSQL 記憶體調優
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
```

**CPU 優化:**
```bash
# 限制 CPU 使用
docker update --cpus="1.5" container_name

# 設定 CPU 親和性
docker update --cpuset-cpus="0,1" container_name
```

**磁碟 I/O 優化:**
```bash
# 使用 SSD 儲存關鍵資料
# 設定適當的日誌輪替
# 清理暫存檔案
```

</details>

---

## 🔐 安全最佳實踐

<details>
<summary><b>🛡️ 系統安全強化</b></summary>

### 🔑 存取控制

```bash
# 建立專用使用者
sudo useradd -r -s /bin/false visionflow
sudo usermod -aG docker visionflow

# 設定檔案權限
chmod 600 .env
chmod 755 scripts/
chown -R visionflow:visionflow /opt/visionflow
```

### 🌐 網路安全

```bash
# 配置防火牆規則
sudo ufw allow from trusted_ip to any port 5000
sudo ufw deny from any to any port 5432  # 僅允許內部存取資料庫

# 設定 SSL/TLS
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key -out server.crt
```

### 📊 安全監控

```bash
# 設定安全日誌監控
tail -f /var/log/auth.log | grep "Failed password"

# 監控異常存取
docker logs --since=1h visionflow_backend | grep "401\|403\|500"
```

</details>

---

## 📈 擴展和升級

<details>
<summary><b>🔄 版本升級</b></summary>

### 📦 安全升級流程

```bash
# 1. 備份當前版本
./scripts/backup_all.sh

# 2. 下載新版本
git fetch --tags
git checkout v2.1.0

# 3. 比較配置差異
diff .env.example .env

# 4. 執行升級
./scripts/upgrade.sh

# 5. 驗證升級結果
./scripts/verify_upgrade.sh
```

</details>

<details>
<summary><b>📊 容量規劃</b></summary>

### 💾 儲存需求評估

| 組件 | 基礎需求 | 擴展需求 | 建議 |
|------|----------|----------|------|
| **作業系統** | 20GB | - | SSD |
| **Docker 映像** | 10GB | 20GB | SSD |
| **資料庫** | 5GB | 50GB/年 | SSD + 定期清理 |
| **日誌檔案** | 1GB | 10GB/年 | 自動輪替 |
| **AI 模型** | 500MB | 2GB | SSD |
| **暫存影像** | 2GB | 10GB | 自動清理 |

</details>

---

<div align="center">

## 🎯 部署檢查清單

### ✅ 部署前檢查

- [ ] 系統需求確認
- [ ] 環境變數配置
- [ ] 安全憑證設定
- [ ] 網路連通性測試
- [ ] 備份策略建立

### ✅ 部署後驗證

- [ ] 服務健康檢查
- [ ] 功能測試完成
- [ ] 效能基準確認
- [ ] 監控告警設定
- [ ] 文檔更新完成

---

**🚀 VisionFlow 部署指南 | 企業級智能監控系統**

*如需技術支援，請聯繫: [sky328423@gmail.com](mailto:sky328423@gmail.com)*

</div>
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U user vision_notify > backup_${DATE}.sql
```

#### 配置備份
```bash
# 備份環境變數和配置
cp .env .env.backup.$(date +%Y%m%d)
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env docker-compose*.yaml
```

## 故障排除

### 常見問題

#### 1. 容器無法啟動
```bash
# 檢查日誌
docker-compose logs [service_name]

# 檢查配置
docker-compose config

# 重新建置映像
docker-compose build --no-cache
```

#### 2. 資料庫連線問題
```bash
# 檢查資料庫狀態
docker-compose exec db pg_isready -U user

# 重設資料庫
docker-compose down -v
docker-compose up -d db
```

#### 3. Redis 連線問題
```bash
# 測試 Redis 連線
docker-compose exec redis redis-cli ping

# 檢查 Redis 日誌
docker-compose logs redis
```

#### 4. 模型載入失敗
```bash
# 檢查模型檔案
docker-compose exec objectrecognition ls -la /app/model/

# 下載模型檔案
docker-compose exec objectrecognition python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
```

### 性能調優

#### 內存優化
```bash
# 限制容器記憶體使用
export OBJECT_RECOGNITION_MEMORY_LIMIT=2G
export OBJECT_RECOGNITION_MEMORY_RESERVATION=512M
```

#### CPU 優化
```bash
# 調整 worker 數量
export GUNICORN_WORKERS=4
export CAMERA_WORKER_THREADS=4
export OBJECT_RECOGNITION_MAX_WORKERS=2
```

#### 網路優化
```bash
# 調整連線設定
export GUNICORN_KEEPALIVE=5
export CAMERA_WORKER_CONNECTIONS=1000
```

### 安全建議

1. **定期更新密碼**
   ```bash
   # 更新資料庫密碼
   export POSTGRES_PASSWORD=$(openssl rand -base64 32)
   
   # 更新 SECRET_KEY
   export SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **限制網路存取**
   ```bash
   # 使用防火牆限制連接埠
   sudo ufw allow 5000/tcp
   sudo ufw deny 5432/tcp  # 僅內部存取
   ```

3. **啟用 HTTPS**
   ```bash
   # 使用 nginx 或 traefik 作為反向代理
   # 配置 SSL 憑證
   ```

## 進階配置

### 高可用性部署
- 使用 Docker Swarm 或 Kubernetes
- 配置負載平衡器
- 設定資料庫主從複製

### 監控整合
- Prometheus + Grafana
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Jaeger 分散式追蹤

### CI/CD 整合
- GitHub Actions
- GitLab CI/CD
- Jenkins

如需更多協助，請參考專案文件或提交 issue。
