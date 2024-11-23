
# VisionFlow API Documentation

以下是基於您提供的所有 API 整理的詳細文檔，按功能分類。

---

## 使用者認證 API

### 1. 註冊頁面
**Endpoint:**  
`GET /register`

**描述:**  
返回註冊頁面。

---

### 2. 註冊新使用者
**Endpoint:**  
`POST /register`

**描述:**  
註冊新的使用者帳號。

**Request Body:**
```json
{
    "username": "your_username",
    "email": "your_email",
    "password": "your_password"
}
```

**Response:**
```json
{
    "message": "User registered successfully",
    "account_uuid": "account-uuid-string"
}
```

---

### 3. 使用者登入
**Endpoint:**  
`POST /login`

**描述:**  
用戶登入並獲取授權 Token。

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

## 攝影機管理 API

### 1. 獲取當前用戶的攝影機列表
**Endpoint:**  
`GET /cameras`

**描述:**  
返回當前用戶擁有的所有攝影機。

**Response:**
```json
[
    {
        "id": 1,
        "name": "Camera 1",
        "stream_url": "http://camera-stream-url",
        "recognition": true
    }
]
```

---

### 2. 新增攝影機
**Endpoint:**  
`POST /cameras`

**描述:**  
新增一台攝影機並關聯到當前用戶。

**Request Body:**
```json
{
    "name": "Camera 1",
    "stream_url": "http://camera-stream-url",
    "recognition": true
}
```

**Response:**
```json
{
    "message": "Camera added successfully",
    "id": 1,
    "name": "Camera 1",
    "stream_url": "http://camera-stream-url",
    "recognition": true
}
```

---

### 3. 更新攝影機信息
**Endpoint:**  
`PATCH /cameras/<int:camera_id>`

**描述:**  
部分更新攝影機信息。

**Request Body:**
```json
{
    "name": "Updated Camera Name",
    "stream_url": "http://new-stream-url"
}
```

**Response:**
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

## 流媒體與影像辨識 API

### 1. 獲取辨識後的即時影像流
**Endpoint:**  
`GET /recognized_stream/<ID>`

**描述:**  
返回處理後的即時影像流。

---

### 2. 快照 UI 顯示
**Endpoint:**  
`GET /snapshot_ui/<ID>`

**描述:**  
顯示攝影機快照及相關區域。

---

### 3. 顯示圖片
**Endpoint:**  
`GET /showimage/<path:image_path>`

**描述:**  
返回指定路徑的圖片。

**Response:**  
成功返回圖片或錯誤消息。

---

### 4. 獲取實時影像流
**Endpoint:**  
`GET /get_stream/<int:ID>`

**描述:**  
獲取實時影像流。返回格式為 `multipart/x-mixed-replace`。

---

## 多邊形區域管理 API

### 1. 管理多邊形
**Endpoint:**  
`POST /rectangles/<ID>`  
`GET /rectangles/<ID>`  
`DELETE /rectangles/<ID>`

**描述:**  
管理多邊形區域數據。POST 用於保存，GET 用於獲取，DELETE 用於刪除。

**POST Request Body:**
```json
[
    {"x": 100, "y": 200},
    {"x": 150, "y": 250}
]
```

**POST Response:**
```json
{
    "message": "多邊形已儲存"
}
```

**GET Response:**
```json
[
    [{"x": 100, "y": 200}, {"x": 150, "y": 250}]
]
```

**DELETE Response:**
```json
{
    "message": "所有多邊形已清除"
}
```

---

### 2. 生成遮罩
**Endpoint:**  
`GET /mask/<ID>`

**描述:**  
生成遮罩圖像，將多邊形區域繪製在黑白遮罩圖中。

**Response:**  
返回 PNG 格式的遮罩圖片。

---

## 通知管理 API

### 1. 獲取所有通知
**Endpoint:**  
`GET /notifications`

**描述:**  
返回所有通知列表。

**Response:**
```json
[
    {
        "id": 1,
        "account_uuid": "account-uuid-string",
        "camera_id": 1,
        "message": "Detected event",
        "image_path": "/path/to/image.jpg",
        "created_at": "2023-01-01T12:00:00"
    }
]
```

---

### 2. 新增通知
**Endpoint:**  
`POST /notifications`

**描述:**  
新增一條通知記錄。

**Request Body:**
```json
{
    "account_uuid": "account-uuid-string",
    "camera_id": 1,
    "message": "Detected event",
    "image_path": "/path/to/image.jpg"
}
```

**Response:**
```json
{
    "message": "Notification created successfully"
}
```

---

## 郵件接收者管理 API

### 1. 獲取所有郵件接收者
**Endpoint:**  
`GET /email_recipients`

**描述:**  
返回所有郵件接收者列表。

**Response:**
```json
[
    {
        "id": 1,
        "account_uuid": "account-uuid-string",
        "email": "recipient@example.com"
    }
]
```

---

### 2. 新增郵件接收者
**Endpoint:**  
`POST /email_recipients`

**描述:**  
新增一個郵件接收者。

**Request Body:**
```json
{
    "account_uuid": "account-uuid-string",
    "email": "recipient@example.com"
}
```

**Response:**
```json
{
    "message": "Email recipient added successfully"
}
```

## 郵件接收者管理 API

### 1. 獲取所有郵件接收者
**Endpoint:**  
`GET /email_recipients`

**描述:**  
返回所有郵件接收者列表。

**Response:**
```json
[
    {
        "id": 1,
        "account_uuid": "account-uuid-string",
        "email": "recipient@example.com"
    }
]
```

### 2. 新增郵件接收者
**Endpoint:**  
`POST /email_recipients`

**描述:**  
新增一個郵件接收者。

**Request Body:**
```json
{
    "account_uuid": "account-uuid-string",
    "email": "recipient@example.com"
}
```

**Response:**
```json
{
    "message": "Email recipient added successfully"
}
```

---

## LINE Token 管理 API

### 1. 獲取所有 LINE Tokens
**Endpoint:**  
`GET /line_tokens`

**描述:**  
返回所有 LINE Token 列表。

**Response:**
```json
[
    {
        "id": 1,
        "account_uuid": "account-uuid-string",
        "token": "line-token-string"
    }
]
```

### 2. 新增 LINE Token
**Endpoint:**  
`POST /line_tokens`

**描述:**  
新增一個 LINE Token。

**Request Body:**
```json
{
    "account_uuid": "account-uuid-string",
    "token": "line-token-string"
}
```

**Response:**
```json
{
    "message": "Line token added successfully"
}
```

---

