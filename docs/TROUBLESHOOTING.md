# VisionFlow 故障排除指南

本文檔提供 VisionFlow 系統常見問題的診斷和解決方案。

## 🚨 緊急故障處理

### 系統完全無法存取

1. **檢查所有服務狀態**
   ```bash
   ./scripts/deploy.sh status
   ```

2. **檢查 Docker 服務**
   ```bash
   docker ps -a
   docker-compose ps
   ```

3. **快速重啟**
   ```bash
   ./scripts/deploy.sh restart production
   ```

4. **檢查系統資源**
   ```bash
   df -h          # 磁碟空間
   free -m        # 記憶體使用
   top            # CPU 使用率
   ```

### 服務部分故障

1. **識別故障服務**
   ```bash
   ./scripts/monitor.sh health
   ```

2. **檢查特定服務日誌**
   ```bash
   docker-compose logs --tail=100 [service_name]
   ```

3. **重啟故障服務**
   ```bash
   docker-compose restart [service_name]
   ```

## 🔍 診斷工具

### 自動診斷腳本

```bash
#!/bin/bash
# 快速診斷腳本

echo "=== VisionFlow 系統診斷 ==="
echo "時間: $(date)"
echo ""

echo "1. 容器狀態:"
docker-compose ps
echo ""

echo "2. 系統資源:"
echo "磁碟使用: $(df -h / | tail -1 | awk '{print $5}')"
echo "記憶體使用: $(free | grep Mem | awk '{printf "%.1f%%\n", $3/$2 * 100.0}')"
echo "CPU 負載: $(uptime | awk -F'load average:' '{print $2}')"
echo ""

echo "3. 服務健康檢查:"
curl -s http://localhost:5000/health && echo " ✅ Web 服務正常" || echo " ❌ Web 服務異常"
curl -s http://localhost:5001/health && echo " ✅ 相機服務正常" || echo " ❌ 相機服務異常"
curl -s http://localhost:5002/health && echo " ✅ 辨識服務正常" || echo " ❌ 辨識服務異常"
echo ""

echo "4. 網路連接:"
ping -c 1 8.8.8.8 > /dev/null && echo " ✅ 網路連接正常" || echo " ❌ 網路連接異常"
echo ""

echo "5. 最近錯誤日誌:"
tail -20 logs/*.log | grep -i error | tail -5
echo ""
```

### 日誌分析

```bash
# 查看所有錯誤日誌
grep -r "ERROR\|CRITICAL\|FATAL" logs/

# 查看最近的警告
grep -r "WARNING" logs/ | tail -20

# 分析特定時間段的日誌
grep "2025-06-01 14:" logs/*.log

# 統計錯誤類型
grep -r "ERROR" logs/ | awk -F: '{print $3}' | sort | uniq -c | sort -rn
```

## 🐳 Docker 相關問題

### 容器無法啟動

**症狀**: 容器狀態顯示 "Exited" 或 "Restarting"

**診斷步驟**:
```bash
# 查看容器日誌
docker logs [container_name]

# 查看詳細錯誤
docker-compose logs [service_name]

# 檢查映像是否存在
docker images | grep visionflow
```

**常見原因和解決方案**:

1. **端口衝突**
   ```bash
   # 檢查端口使用情況
   lsof -i :5000
   netstat -tulpn | grep :5000
   
   # 解決方案: 修改 docker-compose.yaml 中的端口映射
   ```

2. **環境變數錯誤**
   ```bash
   # 檢查環境文件
   cat .env
   
   # 驗證環境變數
   docker-compose config
   ```

3. **映像損壞**
   ```bash
   # 重新拉取映像
   docker-compose pull
   
   # 重建映像
   docker-compose build --no-cache
   ```

### 容器記憶體不足

**症狀**: 容器被 OOM Killer 終止

**診斷**:
```bash
# 檢查容器資源使用
docker stats

# 檢查系統記憶體
dmesg | grep -i "killed process"
```

**解決方案**:
```yaml
# 在 docker-compose.yaml 中增加記憶體限制
services:
  web:
    mem_limit: 1g
    mem_reservation: 512m
```

### 網路連接問題

**症狀**: 服務間無法通訊

**診斷**:
```bash
# 檢查 Docker 網路
docker network ls
docker network inspect visionflow_default

# 測試服務間連接
docker-compose exec web ping camera_ctrl
```

**解決方案**:
```bash
# 重建網路
docker-compose down
docker network prune
docker-compose up -d
```

## 🗄️ 資料庫問題

### PostgreSQL 連接失敗

**症狀**: 應用無法連接到資料庫

**診斷步驟**:
```bash
# 檢查資料庫容器狀態
docker-compose exec db pg_isready

# 測試連接
docker-compose exec db psql -U user -d vision_notify -c "\l"

# 檢查資料庫日誌
docker-compose logs db
```

**常見問題**:

1. **資料庫未啟動**
   ```bash
   docker-compose up -d db
   docker-compose logs db
   ```

2. **連接參數錯誤**
   ```bash
   # 檢查環境變數
   echo $POSTGRES_HOST
   echo $POSTGRES_PORT
   echo $POSTGRES_USER
   ```

3. **磁碟空間不足**
   ```bash
   df -h
   docker system df
   ```

### 資料庫效能問題

**症狀**: 查詢緩慢、超時

**診斷**:
```sql
-- 檢查慢查詢
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC;

-- 檢查索引使用情況
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
ORDER BY idx_scan;
```

**解決方案**:
```sql
-- 分析表統計
ANALYZE;

-- 重建索引
REINDEX INDEX index_name;

-- 清理過期資料
VACUUM FULL;
```

## 📡 Redis 問題

### Redis 連接失敗

**診斷**:
```bash
# 檢查 Redis 服務
docker-compose exec redis redis-cli ping

# 檢查連接參數
docker-compose exec redis redis-cli info clients
```

### Redis 記憶體不足

**診斷**:
```bash
# 檢查記憶體使用
docker-compose exec redis redis-cli info memory

# 檢查 key 數量
docker-compose exec redis redis-cli dbsize
```

**解決方案**:
```bash
# 清理過期 key
docker-compose exec redis redis-cli --scan --pattern "*" | xargs docker-compose exec redis redis-cli del

# 設置記憶體限制
# 在 redis.conf 中添加:
# maxmemory 512mb
# maxmemory-policy allkeys-lru
```

## 🎯 AI 模型問題

### 模型載入失敗

**症狀**: 物件辨識服務無法啟動

**診斷**:
```bash
# 檢查模型文件
ls -la object_recognition/model/

# 檢查模型載入日誌
docker-compose logs object_recognition | grep -i model
```

**解決方案**:
```bash
# 重新下載模型
cd object_recognition
wget https://github.com/ultralytics/yolov5/releases/download/v6.0/yolov5s.pt -O yolo11n.pt

# 檢查檔案權限
chmod 644 yolo11n.pt
```

### 辨識效能差

**症狀**: 辨識速度慢、準確率低

**診斷**:
```bash
# 檢查 GPU 使用情況
nvidia-smi  # 如果有 GPU

# 檢查 CPU 使用率
docker stats object_recognition
```

**調優建議**:
```python
# 調整信心度閾值
MODEL1_CONF=0.7

# 啟用 GPU 加速
GPU_ENABLED=true

# 調整批次大小
BATCH_SIZE=4
```

## 🌐 網路和 API 問題

### API 回應緩慢

**診斷**:
```bash
# 測試 API 回應時間
time curl http://localhost:5000/health

# 檢查請求日誌
grep "GET\|POST" logs/web.log | tail -20
```

**解決方案**:
```python
# 增加 worker 數量
WORKER_PROCESSES=4

# 調整連接超時
API_TIMEOUT=60

# 啟用快取
CACHE_ENABLED=true
```

### CORS 錯誤

**症狀**: 前端無法存取 API

**解決方案**:
```python
# 在 Flask 應用中設置 CORS
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])
```

## 📊 監控和告警

### 設置自動監控

```bash
# 建立監控 cron job
crontab -e

# 每5分鐘檢查服務健康
*/5 * * * * /path/to/visionflow/scripts/monitor.sh health

# 每小時收集指標
0 * * * * /path/to/visionflow/scripts/monitor.sh metrics

# 每天生成報告
0 9 * * * /path/to/visionflow/scripts/monitor.sh report
```

### 告警設置

```bash
# 建立告警腳本
cat > scripts/alert.sh << 'EOF'
#!/bin/bash
if ! ./scripts/monitor.sh health > /dev/null; then
    echo "VisionFlow 服務異常 - $(date)" | mail -s "VisionFlow Alert" admin@example.com
fi
EOF

chmod +x scripts/alert.sh
```

## 🔧 效能調優

### 系統層面優化

```bash
# 調整檔案描述符限制
echo "fs.file-max = 65536" >> /etc/sysctl.conf

# 調整 TCP 設定
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf

# 應用設定
sysctl -p
```

### 應用層面優化

```python
# Flask 應用優化
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 資料庫連接池
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

## 📋 檢查清單

### 日常維護檢查

- [ ] 檢查所有服務狀態
- [ ] 檢查磁碟空間使用
- [ ] 檢查記憶體使用情況
- [ ] 檢查錯誤日誌
- [ ] 檢查備份狀態
- [ ] 檢查安全更新

### 故障後檢查

- [ ] 確認問題根本原因
- [ ] 檢查修復措施有效性
- [ ] 更新監控和告警
- [ ] 文檔化問題和解決方案
- [ ] 進行事後分析

## 📞 支援聯絡

如果遇到無法解決的問題：

1. 收集詳細的錯誤日誌
2. 記錄重現步驟
3. 檢查系統環境資訊
4. 聯絡技術支援團隊

---

**注意**: 這是一個學習專案的故障排除指南。在實際生產環境中，請根據具體情況調整診斷和解決方案。
