#!/bin/bash

# PWA 功能驗證腳本
# 檢查 VisionFlow PWA 功能是否正常運作

echo "📱 VisionFlow PWA 功能驗證"
echo "=========================="

BASE_URL="http://localhost:5000"

# 檢查 PWA 基本文件
echo "🔍 檢查 PWA 基本文件..."

files=(
    "/static/manifest.json:PWA Manifest"
    "/static/js/service-worker.js:Service Worker"
    "/static/js/smart-notifications.js:智能通知系統"
    "/static/css/smart-notifications.css:通知系統樣式"
    "/static/images/icon-192x192.png:PWA 圖標 192x192"
    "/static/images/icon-512x512.png:PWA 圖標 512x512"
    "/static/images/apple-touch-icon.png:Apple Touch 圖標"
)

for file_info in "${files[@]}"; do
    IFS=':' read -r file_path description <<< "$file_info"
    if curl -f "${BASE_URL}${file_path}" >/dev/null 2>&1; then
        echo "✅ $description"
    else
        echo "❌ $description - 文件不可用: $file_path"
    fi
done

# 檢查 Manifest.json 內容
echo ""
echo "📄 檢查 Manifest.json 內容..."
manifest_content=$(curl -s "${BASE_URL}/static/manifest.json")
if echo "$manifest_content" | jq . >/dev/null 2>&1; then
    echo "✅ Manifest.json 格式正確"
    
    # 檢查關鍵字段
    if echo "$manifest_content" | jq -e '.name' >/dev/null 2>&1; then
        app_name=$(echo "$manifest_content" | jq -r '.name')
        echo "✅ 應用名稱: $app_name"
    else
        echo "❌ 缺少應用名稱"
    fi
    
    if echo "$manifest_content" | jq -e '.start_url' >/dev/null 2>&1; then
        start_url=$(echo "$manifest_content" | jq -r '.start_url')
        echo "✅ 起始 URL: $start_url"
    else
        echo "❌ 缺少起始 URL"
    fi
    
    if echo "$manifest_content" | jq -e '.display' >/dev/null 2>&1; then
        display_mode=$(echo "$manifest_content" | jq -r '.display')
        echo "✅ 顯示模式: $display_mode"
    else
        echo "❌ 缺少顯示模式"
    fi
    
    # 檢查圖標
    icon_count=$(echo "$manifest_content" | jq '.icons | length')
    echo "✅ 圖標數量: $icon_count"
    
else
    echo "❌ Manifest.json 格式錯誤"
fi

# 檢查 Service Worker 語法
echo ""
echo "🔧 檢查 Service Worker..."
sw_content=$(curl -s "${BASE_URL}/static/js/service-worker.js")
if echo "$sw_content" | grep -q "addEventListener.*install"; then
    echo "✅ Service Worker 包含安裝事件監聽器"
else
    echo "❌ Service Worker 缺少安裝事件監聽器"
fi

if echo "$sw_content" | grep -q "addEventListener.*activate"; then
    echo "✅ Service Worker 包含啟動事件監聽器"
else
    echo "❌ Service Worker 缺少啟動事件監聽器"
fi

if echo "$sw_content" | grep -q "addEventListener.*fetch"; then
    echo "✅ Service Worker 包含網路請求攔截"
else
    echo "❌ Service Worker 缺少網路請求攔截"
fi

if echo "$sw_content" | grep -q "addEventListener.*push"; then
    echo "✅ Service Worker 包含推送通知處理"
else
    echo "❌ Service Worker 缺少推送通知處理"
fi

# 檢查智能通知系統
echo ""
echo "🔔 檢查智能通知系統..."
notification_js=$(curl -s "${BASE_URL}/static/js/smart-notifications.js")

if echo "$notification_js" | grep -q "class SmartNotificationSystem"; then
    echo "✅ 智能通知系統類別存在"
else
    echo "❌ 智能通知系統類別不存在"
fi

if echo "$notification_js" | grep -q "setupWebSocketConnection"; then
    echo "✅ WebSocket 連接功能存在"
else
    echo "❌ WebSocket 連接功能不存在"
fi

if echo "$notification_js" | grep -q "requestPermissions"; then
    echo "✅ 權限請求功能存在"
else
    echo "❌ 權限請求功能不存在"
fi

# 檢查頁面是否包含 PWA 註冊
echo ""
echo "📝 檢查頁面 PWA 註冊..."
main_page=$(curl -s "${BASE_URL}/")

if echo "$main_page" | grep -q "serviceWorker.register"; then
    echo "✅ 主頁面包含 Service Worker 註冊"
else
    echo "❌ 主頁面缺少 Service Worker 註冊"
fi

if echo "$main_page" | grep -q 'rel="manifest"'; then
    echo "✅ 主頁面包含 Manifest 連結"
else
    echo "❌ 主頁面缺少 Manifest 連結"
fi

if echo "$main_page" | grep -q 'name="theme-color"'; then
    echo "✅ 主頁面包含主題顏色"
else
    echo "❌ 主頁面缺少主題顏色"
fi

# 檢查通知設定頁面
echo ""
echo "⚙️ 檢查通知設定頁面..."
if curl -f "${BASE_URL}/notifications-settings" >/dev/null 2>&1; then
    echo "✅ 通知設定頁面可訪問"
    
    settings_page=$(curl -s "${BASE_URL}/notifications-settings")
    if echo "$settings_page" | grep -q "smart-notifications.js"; then
        echo "✅ 通知設定頁面包含智能通知系統"
    else
        echo "❌ 通知設定頁面缺少智能通知系統"
    fi
else
    echo "❌ 通知設定頁面不可訪問"
fi

# 檢查分析儀表板
echo ""
echo "📊 檢查分析儀表板..."
if curl -f "${BASE_URL}/analytics-dashboard" >/dev/null 2>&1; then
    echo "✅ 分析儀表板可訪問"
else
    echo "❌ 分析儀表板不可訪問"
fi

# PWA 安裝能力檢查
echo ""
echo "💾 PWA 安裝能力檢查..."
echo "要測試 PWA 安裝功能，請在 Chrome 瀏覽器中："
echo "1. 開啟 ${BASE_URL}"
echo "2. 按 F12 開啟開發者工具"
echo "3. 前往 Application > Manifest 標籤"
echo "4. 檢查是否顯示 'Add to homescreen' 連結"
echo "5. 前往 Application > Service Workers 標籤"
echo "6. 檢查 Service Worker 是否已註冊並運行"

# Lighthouse PWA 檢查建議
echo ""
echo "🔍 Lighthouse PWA 檢查建議..."
echo "要進行完整的 PWA 檢查，請在 Chrome 中："
echo "1. 開啟 ${BASE_URL}"
echo "2. 按 F12 開啟開發者工具"
echo "3. 前往 Lighthouse 標籤"
echo "4. 選擇 'Progressive Web App' 類別"
echo "5. 點擊 'Generate report'"

echo ""
echo "🎯 PWA 功能驗證完成！"
echo "====================="
echo ""
echo "📋 下一步驗證建議："
echo "1. 🌐 在不同瀏覽器中測試 PWA 功能"
echo "2. 📱 在移動設備上測試安裝和使用"
echo "3. 🔔 測試推送通知功能"
echo "4. ⚡ 測試離線功能"
echo "5. 🔄 測試應用更新機制"
