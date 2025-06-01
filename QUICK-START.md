# 🚀 VisionFlow 快速啟動指南

## ⚡ 一分鐘快速體驗

### 📋 前置要求
- ✅ Docker & Docker Compose 已安裝
- ✅ 8GB+ 可用內存
- ✅ Chrome/Firefox/Safari 瀏覽器

### 🎯 一鍵啟動
```bash
# 1. 進入項目目錄
cd VisionFlow

# 2. 執行自動部署腳本
./deploy-and-test.sh

# 3. 等待約 2-3 分鐘完成部署
```

### 🌐 訪問應用
- **🏠 主應用**: http://localhost:5000
- **⚙️ 通知設定**: http://localhost:5000/notifications-settings  
- **📊 分析儀表板**: http://localhost:5000/analytics-dashboard
- **🔌 API 文檔**: http://localhost:5001/health

---

## 🧪 功能測試流程

### 1️⃣ 用戶註冊和登入
```
1. 訪問 http://localhost:5000
2. 點擊註冊 → 創建測試帳號
3. 登入系統 → 進入儀表板
```

### 2️⃣ PWA 功能測試
```
1. 在 Chrome 中訪問應用
2. 按 F12 → Application → Manifest
3. 檢查 PWA 配置正確性
4. 嘗試 "Add to Home Screen" 功能
```

### 3️⃣ 智能通知測試
```
1. 訪問: /notifications-settings
2. 開啟各種通知通道
3. 點擊 "測試桌面通知"
4. 查看統計數據更新
```

### 4️⃣ 實時功能測試
```
1. 開啟瀏覽器開發者工具
2. 查看 Network → WS (WebSocket)
3. 確認 WebSocket 連接正常
4. 測試實時通知推送
```

---

## 🔧 故障排除

### ❓ 常見問題

**Q: 服務啟動失敗？**
```bash
# 檢查端口佔用
lsof -i :5000 -i :5001 -i :5432 -i :6379

# 清理並重新啟動
docker-compose down --volumes
./deploy-and-test.sh
```

**Q: 通知不工作？**
```bash
# 檢查瀏覽器通知權限
# Chrome: 設定 → 隱私和安全性 → 網站設定 → 通知

# 檢查 WebSocket 連接
# 開發者工具 → Network → WS
```

**Q: PWA 無法安裝？**
```bash
# 檢查 HTTPS (本地開發可忽略)
# 檢查 Manifest.json 格式
curl http://localhost:5000/static/manifest.json | jq .

# 檢查 Service Worker
curl http://localhost:5000/static/js/service-worker.js
```

### 🔍 日誌查看
```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f redis
```

---

## 📱 PWA 特性體驗

### 🎯 桌面安裝
1. **Chrome**: 網址列右側 "安裝" 圖標
2. **Firefox**: 選單 → "安裝這個網站"
3. **Safari**: 分享 → "加入主畫面"

### ⚡ 離線功能
1. 在線時正常使用應用
2. 斷開網路連接
3. 重新載入頁面 → 應顯示快取內容
4. 恢復網路 → 自動同步

### 🔔 推送通知
1. 允許瀏覽器通知權限
2. 在通知設定中測試各種通道
3. 查看桌面/系統通知效果
4. 驗證通知歷史記錄

---

## 🎨 自定義配置

### 🎵 添加音效文件
```bash
# 參考音效設置指南
cat web/static/sounds/setup-audio.md

# 將音效文件複製到指定位置
cp your-sounds/*.mp3 web/static/sounds/
```

### 🌈 自定義主題
```bash
# 修改主題顏色
# 編輯: web/static/manifest.json
"theme_color": "#your-color"

# 修改應用圖標
# 替換: web/static/images/icon-*.png
```

### ⚙️ 環境配置
```bash
# 修改環境變數
# 編輯: .env
FLASK_ENV=production
DEBUG=false

# 重新啟動服務
docker-compose down && docker-compose up -d
```

---

## 📊 監控和維護

### 🏥 健康檢查
```bash
# 系統健康狀態
curl http://localhost:5001/health

# 詳細健康信息
curl http://localhost:5001/health/detailed
```

### 📈 效能監控
```bash
# 資源使用情況
docker stats

# 服務狀態
docker-compose ps
```

### 🔄 更新和維護
```bash
# 更新應用
git pull origin main
docker-compose down
docker-compose up -d --build

# 數據備份
docker-compose exec db pg_dump -U visionflow_user visionflow > backup.sql
```

---

## 🆘 支援和幫助

### 📚 文檔資源
- **📖 部署指南**: `DEPLOYMENT.md`
- **🔌 API 文檔**: `API_ENHANCED.md`  
- **🏗️ 項目總覽**: `PROJECT_SUMMARY.md`
- **📱 PWA 報告**: `PWA-COMPLETION-REPORT.md`

### 🐛 問題回報
1. 檢查現有文檔和 FAQ
2. 收集錯誤日誌和系統信息
3. 描述重現步驟
4. 提供環境詳細信息

### 🤝 貢獻指南
1. Fork 項目倉庫
2. 創建功能分支
3. 提交更改並測試
4. 發送 Pull Request

---

## 🎯 下一步建議

### 🔄 短期改進
- [ ] 添加實際音效文件
- [ ] 測試更多設備和瀏覽器
- [ ] 優化 PWA 圖標設計

### 🚀 長期發展
- [ ] 添加更多通知通道 (Slack, Discord)
- [ ] 實現智能通知分組
- [ ] 添加通知排程功能
- [ ] 支援多語言界面

---

**🎉 恭喜！您已成功部署 VisionFlow 智能監控系統！**

**📞 需要幫助？** 請參考上述文檔或檢查項目 README.md
