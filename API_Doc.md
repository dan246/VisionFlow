
<div align="center">

# 🚀 VisionFlow API Documentation

**完整的 API 使用指南與參考文檔**

[![API Version](https://img.shields.io/badge/API-v1.0-blue?style=flat-square)](.)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0-green?style=flat-square)](.)
[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)](.)

</div>

---

## 📚 目錄

- [🔐 使用者認證 API](#-使用者認證-api)
- [📹 攝影機管理 API](#-攝影機管理-api)
- [🎥 影像串流 API](#-影像串流-api)
- [🎨 檢測區域 API](#-檢測區域-api)
- [📊 系統狀態 API](#-系統狀態-api)
- [🛠️ 工具與配置](#️-工具與配置)

---

## 🔐 使用者認證 API

<details>
<summary><strong>📝 使用者註冊</strong></summary>

### 取得註冊頁面
```http
GET /register
```

**描述:** 返回使用者註冊頁面

**回應:**
```html
<!-- 註冊頁面 HTML -->
```

---

### 註冊新使用者
```http
POST /register
```

**描述:** 建立新的使用者帳號

**請求範例:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password_123"
}
```

**成功回應:**
```json
{
    "message": "User registered successfully",
    "account_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "status": "success"
}
```

**錯誤回應:**
```json
{
    "message": "Username already exists",
    "status": "error"
}
```

</details>

<details>
<summary><strong>🔑 使用者登入</strong></summary>

### 使用者登入
```http
POST /login
```

**描述:** 用戶登入並獲取授權 Token

**Request Body:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "message": "Login successful",
    "account_uuid": "account-uuid-string",
    "access_token": "access-token-string",
    "refresh_token": "refresh-token-string"
}
```

---

### 4. Token 刷新
**Endpoint:**  
`POST /token/refresh`

**描述:**  
刷新訪問 Token。

**Request Body:**
```json
{
    "refresh_token": "your_refresh_token"
}
```

**Response:**
```json
{
    "access_token": "new-access-token-string"
}
```

---

## 📹 攝影機管理 API

> **全面的攝影機配置與監控 API**

<details>
<summary><strong>📋 獲取攝影機列表</strong></summary>

### 獲取當前用戶的攝影機列表
```http
GET /cameras
```

**描述:** 返回當前用戶擁有的所有攝影機配置

**請求頭:**
```http
Authorization: Bearer <access_token>
```

**成功回應:**
```json
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "name": "主入口攝影機",
            "stream_url": "rtsp://camera1.example.com:554/stream",
            "recognition": true,
            "location": "主入口",
            "model_name": "yolo_v11_detect",
            "status": "online",
            "created_at": "2024-01-15T10:30:00Z",
            "last_active": "2024-01-20T15:45:00Z"
        }
    ],
    "total": 1
}
```

</details>

<details>
<summary><strong>➕ 新增攝影機</strong></summary>

### 新增攝影機
```http
POST /cameras
```

**描述:** 新增一台攝影機並關聯到當前用戶

**請求頭:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**請求範例:**
```json
{
    "name": "側門攝影機",
    "stream_url": "rtsp://camera2.example.com:554/stream",
    "recognition": true,
    "location": "側門入口",
    "model_name": "yolo_v11_detect",
    "detection_areas": [
        {
            "name": "入口區域",
            "coordinates": [[100, 100], [300, 100], [300, 200], [100, 200]],
            "alert_duration": 5
        }
    ]
}
```

**成功回應:**
```json
{
    "status": "success",
    "message": "攝影機新增成功",
    "data": {
        "id": 2,
        "name": "側門攝影機",
        "stream_url": "rtsp://camera2.example.com:554/stream",
        "recognition": true,
        "location": "側門入口",
        "model_name": "yolo_v11_detect",
        "status": "connecting",
        "created_at": "2024-01-20T16:00:00Z"
    }
}
```

</details>

<details>
<summary><strong>✏️ 更新攝影機設定</strong></summary>

### 更新攝影機信息
```http
PATCH /cameras/<int:camera_id>
```

**描述:** 部分更新攝影機信息和設定

**請求頭:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**請求範例:**
```json
{
    "name": "主入口攝影機 (更新)",
    "stream_url": "rtsp://camera1-new.example.com:554/stream",
    "recognition": false,
    "location": "主入口大廳"
}
```

**成功回應:**
```json
{
    "status": "success",
    "message": "攝影機更新成功",
    "data": {
        "id": 1,
        "name": "主入口攝影機 (更新)",
        "stream_url": "rtsp://camera1-new.example.com:554/stream",
        "recognition": false,
        "location": "主入口大廳",
        "updated_at": "2024-01-20T16:15:00Z"
    }
}
```

</details>

<details>
<summary><strong>🗑️ 刪除攝影機</strong></summary>

### 刪除攝影機
```http
DELETE /cameras/<int:camera_id>
```

**描述:** 安全刪除指定攝影機及相關數據

**請求頭:**
```http
Authorization: Bearer <access_token>
```

**成功回應:**
```json
{
    "status": "success",
    "message": "攝影機刪除成功",
    "deleted_camera_id": 1
}
```

**錯誤回應:**
```json
{
    "status": "error",
    "message": "攝影機不存在或無權限訪問",
    "error_code": "CAMERA_NOT_FOUND"
}
```

</details>
```json
{
    "message": "Camera updated successfully",
    "id": 1,
    "name": "Updated Camera Name",
    "stream_url": "http://new-stream-url",
    "recognition": true
}
```

---

### 4. 刪除攝影機
**Endpoint:**  
`DELETE /cameras/<int:camera_id>`

**描述:**  
刪除指定攝影機。

**Response:**
```json
{
    "message": "Camera deleted successfully."
}
```

---

## 🎥 流媒體與影像辨識 API

> **實時影像處理與 AI 辨識功能**

<details>
<summary><strong>📹 即時辨識影像流</strong></summary>

### 獲取辨識後的即時影像流
```http
GET /recognized_stream/<camera_id>
```

**描述:** 返回經過 AI 辨識處理的即時影像流

**請求頭:**
```http
Authorization: Bearer <access_token>
Accept: multipart/x-mixed-replace
```

**參數:**
- `camera_id` (integer): 攝影機 ID

**回應格式:** `multipart/x-mixed-replace; boundary=frame`

**功能特色:**
- 🎯 實時物件偵測標註
- 📊 信心度分數顯示
- 🎨 動態邊界框繪製
- ⚡ 低延遲串流傳輸

</details>

<details>
<summary><strong>📸 攝影機快照</strong></summary>

### 快照 UI 顯示
```http
GET /snapshot_ui/<camera_id>
```

**描述:** 顯示攝影機快照及檢測區域配置介面

**請求頭:**
```http
Authorization: Bearer <access_token>
```

**回應格式:** HTML 頁面

**功能特色:**
- 🖼️ 即時快照預覽
- 🎨 區域標註工具
- 📐 精確座標顯示
- 💾 配置保存功能

</details>

<details>
<summary><strong>🖼️ 影像檢視</strong></summary>

### 顯示圖片
```http
GET /showimage/<path:image_path>
```

**描述:** 返回指定路徑的圖片資源

**參數:**
- `image_path` (string): 圖片檔案路徑

**回應格式:** Image Binary Data

**支援格式:**
- 📷 JPEG/JPG
- 🖼️ PNG
- 🎭 WebP
- 📸 BMP

</details>

<details>
<summary><strong>📺 原始影像流</strong></summary>

### 獲取實時影像流
```http
GET /get_stream/<int:camera_id>
```

**描述:** 獲取原始實時影像流（未經 AI 處理）

**回應格式:** `multipart/x-mixed-replace; boundary=frame`

**技術規格:**
- 🎬 格式: MJPEG Stream
- 📺 解析度: 依攝影機設定
- ⚡ 幀率: 最高 30 FPS
- 🔄 自動重連機制

</details>

---

## 🔷 多邊形區域管理 API

> **智能檢測區域配置與管理**

<details>
<summary><strong>💾 保存檢測區域</strong></summary>

### 保存多邊形區域
```http
POST /rectangles/<camera_id>
```

**描述:** 保存攝影機的多邊形檢測區域配置

**請求頭:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**請求範例:**
```json
{
    "regions": [
        {
            "name": "入口區域",
            "coordinates": [
                {"x": 100, "y": 150},
                {"x": 300, "y": 150},
                {"x": 300, "y": 400},
                {"x": 100, "y": 400}
            ],
            "alert_duration": 5,
            "notification_enabled": true,
            "detection_classes": ["person", "vehicle"]
        }
    ]
}
```

**成功回應:**
```json
{
    "status": "success",
    "message": "多邊形區域已成功儲存",
    "data": {
        "camera_id": 1,
        "regions_count": 1,
        "saved_at": "2024-01-20T16:30:00Z"
    }
}
```

</details>

<details>
<summary><strong>📋 獲取檢測區域</strong></summary>

### 獲取多邊形區域
```http
GET /rectangles/<camera_id>
```

**描述:** 獲取指定攝影機的所有檢測區域配置

**請求頭:**
```http
Authorization: Bearer <access_token>
```

**成功回應:**
```json
{
    "status": "success",
    "data": {
        "camera_id": 1,
        "regions": [
            {
                "id": 1,
                "name": "入口區域",
                "coordinates": [
                    {"x": 100, "y": 150},
                    {"x": 300, "y": 150},
                    {"x": 300, "y": 400},
                    {"x": 100, "y": 400}
                ],
                "alert_duration": 5,
                "notification_enabled": true,
                "detection_classes": ["person", "vehicle"],
                "created_at": "2024-01-20T16:30:00Z"
            }
        ],
        "total_regions": 1
    }
}
```

</details>

<details>
<summary><strong>🗑️ 刪除檢測區域</strong></summary>

### 刪除多邊形區域
```http
DELETE /rectangles/<camera_id>
```

**描述:** 刪除指定攝影機的所有檢測區域

**請求頭:**
```http
Authorization: Bearer <access_token>
```

**成功回應:**
```json
{
    "status": "success",
    "message": "所有檢測區域已成功刪除",
    "data": {
        "camera_id": 1,
        "deleted_regions": 3,
        "deleted_at": "2024-01-20T16:45:00Z"
    }
}
```

**錯誤回應:**
```json
{
    "status": "error",
    "message": "無權限刪除此攝影機的檢測區域",
    "error_code": "INSUFFICIENT_PERMISSIONS"
}
```

</details>

<details>
<summary><strong>🎨 生成遮罩圖像</strong></summary>

### 生成遮罩
```http
GET /mask/<camera_id>
```

**描述:** 生成黑白遮罩圖像，將多邊形檢測區域視覺化

**請求頭:**
```http
Authorization: Bearer <access_token>
```

**回應格式:** PNG 圖像

**功能特色:**
- ⚫ 背景區域: 黑色 (0, 0, 0)
- ⚪ 檢測區域: 白色 (255, 255, 255)
- 📐 精確邊界繪製
- 🖼️ 高解析度輸出

</details>

---

## 🔔 通知管理 API

> **智能警報與通知系統**

<details>
<summary><strong>📋 獲取通知列表</strong></summary>

### 獲取所有通知
```http
GET /notifications
```

**描述:** 返回當前用戶的所有通知記錄

**請求頭:**
```http
Authorization: Bearer <access_token>
```

**查詢參數:**
- `page` (integer): 頁碼 (預設: 1)
- `limit` (integer): 每頁數量 (預設: 20)
- `status` (string): 狀態篩選 (unread/read/all)

**成功回應:**
```json
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "account_uuid": "550e8400-e29b-41d4-a716-446655440000",
            "camera_id": 1,
            "camera_name": "主入口攝影機",
            "message": "檢測到可疑活動",
            "image_path": "/notifications/images/20240120_163000.jpg",
            "detection_type": "person",
            "confidence": 0.95,
            "status": "unread",
            "created_at": "2024-01-20T16:30:00Z"
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 87,
        "items_per_page": 20
    }
}
```

</details>

<details>
<summary><strong>➕ 新增通知</strong></summary>

### 新增通知
```http
POST /notifications
```

**描述:** 創建新的檢測事件通知

**請求頭:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**請求範例:**
```json
{
    "camera_id": 1,
    "message": "檢測到未授權人員進入",
    "image_path": "/notifications/images/alert_20240120_164500.jpg",
    "detection_type": "person",
    "confidence": 0.92,
    "region_name": "入口區域",
    "metadata": {
        "bounding_box": {
            "x": 150,
            "y": 200,
            "width": 100,
            "height": 150
        }
    }
}
```

**成功回應:**
```json
{
    "status": "success",
    "message": "通知創建成功",
    "data": {
        "id": 25,
        "created_at": "2024-01-20T16:45:00Z",
        "notification_sent": true
    }
}
```

</details>

---

## 📧 郵件接收者管理 API

> **電子郵件通知配置**

<details>
<summary><strong>📋 獲取郵件接收者</strong></summary>

### 獲取所有郵件接收者
```http
GET /email_recipients
```

**描述:** 返回當前用戶配置的所有郵件接收者

**請求頭:**
```http
Authorization: Bearer <access_token>
```

**成功回應:**
```json
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "account_uuid": "550e8400-e29b-41d4-a716-446655440000",
            "email": "security@company.com",
            "name": "安全部門",
            "active": true,
            "verified": true,
            "created_at": "2024-01-15T10:00:00Z",
            "last_notification": "2024-01-20T16:30:00Z"
        }
    ],
    "total": 1
}
```

</details>

<details>
<summary><strong>➕ 新增郵件接收者</strong></summary>

### 新增郵件接收者
```http
POST /email_recipients
```

**描述:** 新增電子郵件通知接收者

**請求頭:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**請求範例:**
```json
{
    "email": "manager@company.com",
    "name": "部門經理",
    "notification_types": ["alerts", "daily_reports"],
    "active": true
}
```

**成功回應:**
```json
{
    "status": "success",
    "message": "郵件接收者新增成功",
    "data": {
        "id": 2,
        "email": "manager@company.com",
        "verification_sent": true,
        "created_at": "2024-01-20T17:00:00Z"
    }
}
```

</details>

---

## 💬 LINE Token 管理 API

> **LINE 即時通知整合**

<details>
<summary><strong>📋 獲取 LINE Tokens</strong></summary>

### 獲取所有 LINE Tokens
```http
GET /line_tokens
```

**描述:** 返回當前用戶配置的所有 LINE 通知 Token

**請求頭:**
```http
Authorization: Bearer <access_token>
```

**成功回應:**
```json
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "account_uuid": "550e8400-e29b-41d4-a716-446655440000",
            "token": "AbCdEf1234567890...",
            "name": "主管群組",
            "active": true,
            "verified": true,
            "created_at": "2024-01-15T10:00:00Z",
            "last_used": "2024-01-20T16:30:00Z"
        }
    ],
    "total": 1
}
```

</details>

<details>
<summary><strong>➕ 新增 LINE Token</strong></summary>

### 新增 LINE Token
```http
POST /line_tokens
```

**描述:** 新增 LINE Notify Token 用於即時通知

**請求頭:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**請求範例:**
```json
{
    "token": "AbCdEf1234567890GhIjKl1234567890",
    "name": "安全監控群組",
    "notification_types": ["alerts", "system_status"],
    "active": true
}
```

**成功回應:**
```json
{
    "status": "success",
    "message": "LINE Token 新增成功",
    "data": {
        "id": 2,
        "name": "安全監控群組",
        "token_verified": true,
        "created_at": "2024-01-20T17:15:00Z"
    }
}
```

</details>

---

## ⚠️ 錯誤代碼說明

| 錯誤代碼 | HTTP 狀態 | 描述 | 解決方案 |
|---------|-----------|-----|----------|
| `AUTH_REQUIRED` | 401 | 需要認證 | 提供有效的 Authorization Header |
| `INVALID_TOKEN` | 401 | Token 無效 | 重新登入獲取新 Token |
| `INSUFFICIENT_PERMISSIONS` | 403 | 權限不足 | 聯繫管理員提升權限 |
| `RESOURCE_NOT_FOUND` | 404 | 資源不存在 | 檢查資源 ID 是否正確 |
| `VALIDATION_ERROR` | 422 | 請求數據驗證失敗 | 檢查請求參數格式 |
| `RATE_LIMIT_EXCEEDED` | 429 | 請求頻率超限 | 降低請求頻率 |
| `SERVER_ERROR` | 500 | 伺服器內部錯誤 | 聯繫技術支援 |

---

## 📝 API 使用範例

### JavaScript 範例
```javascript
// 設定基本配置
const API_BASE = 'http://localhost:5000';
const token = localStorage.getItem('access_token');

// 獲取攝影機列表
async function getCameras() {
    const response = await fetch(`${API_BASE}/cameras`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    return await response.json();
}

// 新增攝影機
async function addCamera(cameraData) {
    const response = await fetch(`${API_BASE}/cameras`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(cameraData)
    });
    return await response.json();
}
```

### Python 範例
```python
import requests

API_BASE = 'http://localhost:5000'
token = 'your_access_token_here'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# 獲取攝影機列表
def get_cameras():
    response = requests.get(f'{API_BASE}/cameras', headers=headers)
    return response.json()

# 新增攝影機
def add_camera(camera_data):
    response = requests.post(
        f'{API_BASE}/cameras',
        headers=headers,
        json=camera_data
    )
    return response.json()
```

---

<div align="center">

**📚 完整 API 文檔 | VisionFlow 智能監控系統**

*如有任何問題，請聯繫技術支援: [sky328423@gmail.com](mailto:sky328423@gmail.com)*

</div>

