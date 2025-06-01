#!/bin/bash

# VisionFlow 功能演示腳本
# 此腳本將展示所有已實現的新功能

echo "🚀 VisionFlow 智能監控系統 - 功能演示"
echo "=========================================="

# 檢查服務狀態
echo "🔍 1. 檢查服務狀態..."
docker-compose -f docker-compose.optimized.yaml ps

echo ""
echo "📊 2. 檢查 API 端點..."

# 測試基本 API
echo "   ✅ 測試主頁端點:"
curl -s -o /dev/null -w "      狀態碼: %{http_code}\n" http://localhost:5001/

echo "   ✅ 測試通知設定 API:"
curl -s -o /dev/null -w "      狀態碼: %{http_code}\n" http://localhost:5001/api/notifications/settings

echo "   ✅ 測試 PWA Manifest:"
curl -s -o /dev/null -w "      狀態碼: %{http_code}\n" http://localhost:5001/static/manifest.json

echo "   ✅ 測試 Service Worker:"
curl -s -o /dev/null -w "      狀態碼: %{http_code}\n" http://localhost:5001/static/js/service-worker.js

echo ""
echo "🔔 3. 智能通知系統功能:"
echo "   ✅ 多通道通知支援 (桌面、聲音、振動、郵件、LINE)"
echo "   ✅ 優先級管理 (Critical、High、Medium、Low)"
echo "   ✅ WebSocket 實時通信"
echo "   ✅ 設定持久化 (伺服器+本地雙重存儲)"
echo "   ✅ 批量通知處理"
echo "   ✅ 統計分析和歷史記錄"

echo ""
echo "📱 4. PWA (Progressive Web App) 功能:"
echo "   ✅ 完整的 PWA Manifest 配置"
echo "   ✅ Service Worker 離線支援"
echo "   ✅ 推送通知支援"
echo "   ✅ 安裝到主屏幕功能"
echo "   ✅ 離線快取策略"

echo ""
echo "🎨 5. 用戶界面更新:"
echo "   ✅ 現代化設計 (Bootstrap 5 + 自定義樣式)"
echo "   ✅ 響應式設計 (支援多設備)"
echo "   ✅ 實時設定介面"
echo "   ✅ 互動式測試功能"

echo ""
echo "🔧 6. 開發工具:"
echo "   ✅ 一鍵部署腳本 (deploy-and-test.sh)"
echo "   ✅ PWA 驗證腳本 (verify-pwa.sh)"
echo "   ✅ 完整的文檔說明"

echo ""
echo "🌐 如何查看新功能:"
echo "=========================================="
echo "1. 🏠 主頁面 (PWA 功能):"
echo "   瀏覽器訪問: http://localhost:5001"
echo "   - 注意右上角的「安裝應用程式」圖標"
echo "   - 檢查 PWA 安裝提示"
echo ""
echo "2. ⚙️ 智能通知設定:"
echo "   訪問: http://localhost:5001/notifications-settings"
echo "   - 測試各種通知通道"
echo "   - 查看統計數據"
echo "   - 調整優先級設定"
echo ""
echo "3. 🔔 實時通知測試:"
echo "   在通知設定頁面點擊「測試」按鈕"
echo "   - 測試桌面通知"
echo "   - 測試聲音提醒"
echo "   - 測試振動反饋"

echo ""
echo "🚀 啟動瀏覽器查看功能:"

# 檢查是否為 macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "正在開啟瀏覽器..."
    open "http://localhost:5001"
    sleep 2
    echo "正在開啟通知設定頁面..."
    open "http://localhost:5001/notifications-settings"
else
    echo "請手動在瀏覽器中訪問:"
    echo "- 主頁: http://localhost:5001"
    echo "- 通知設定: http://localhost:5001/notifications-settings"
fi

echo ""
echo "📋 功能檢查清單:"
echo "=================="
echo "□ PWA 安裝提示是否出現"
echo "□ 通知權限請求是否正常"
echo "□ 設定頁面是否載入"
echo "□ 測試通知是否正常顯示"
echo "□ 設定是否能正常保存"
echo "□ 統計數據是否顯示"

echo ""
echo "✨ 演示完成！請在瀏覽器中體驗新功能。"
