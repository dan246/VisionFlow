# VisionFlow 專案結構引導文件

## 目錄結構規範

```
VisionFlow/
├── .claude/                    # Claude AI 專用配置
│   └── steering/              # 專案引導文件
├── web/                       # 【主要 Web 服務】
│   ├── models/               # 資料模型定義
│   ├── routes/               # API 路由處理
│   ├── services/             # 商業邏輯層
│   ├── static/               # 靜態資源
│   ├── templates/            # HTML 模板
│   └── migrations/           # 資料庫遷移
├── camera_ctrler/            # 【攝影機控制服務】
│   ├── stream/              # 串流處理
│   └── images/              # 快照儲存
├── object_recognition/       # 【AI 辨識服務】
│   ├── config/              # 模型配置
│   ├── model/               # 模型檔案
│   └── saved_images/        # 處理後影像
├── redisv1/                  # 【Redis Worker 服務】
│   ├── frames/              # 影格暫存
│   └── storage/             # 持久化儲存
├── shared/                   # 【共享模組】
│   └── logging_config.py   # 統一日誌配置
├── AImodels/                # 【AI 模型儲存】
│   └── object_recognition/ # 物件辨識模型
├── docs/                    # 【文檔】
├── scripts/                 # 【自動化腳本】
├── logs/                    # 【集中日誌】
└── db/                      # 【資料庫檔案】
```

## 檔案命名慣例

### Python 檔案
- **模組**：使用 snake_case（例：`camera_manager.py`）
- **類別檔案**：與類別名稱對應（例：`YOLOModel.py` 包含 `YOLOModel` 類別）
- **配置檔**：`config.py` 或 `<service>_config.py`
- **工具函式**：`utils.py` 或 `<domain>_utils.py`

### JavaScript 檔案
- **一般檔案**：使用 kebab-case（例：`advanced-dashboard.js`）
- **元件**：與功能對應（例：`camera-stream.js`）
- **服務**：`<service>-service.js`

### 配置檔案
- **Docker**：`Dockerfile` 或 `<service>Dockerfile`
- **Compose**：`docker-compose.<environment>.yaml`
- **環境變數**：`.env` 或 `.env.<environment>`

## 程式碼組織模式

### Flask 應用結構（web/）
```python
web/
├── app.py              # 應用程式入口，使用工廠模式
├── config.py           # 配置類別定義
├── extensions.py       # 擴展初始化
├── models/            # SQLAlchemy 模型
│   ├── __init__.py
│   ├── user.py       # User 模型
│   └── camera.py     # Camera 模型
├── routes/            # Blueprint 路由
│   ├── __init__.py
│   ├── auth_routes.py    # 認證相關
│   └── camera_routes.py  # 攝影機相關
└── services/          # 商業邏輯
    ├── __init__.py
    └── camera_service.py  # 攝影機服務
```

### 微服務通訊模式
```python
# 服務間通訊使用 Redis 佇列
# 發布者
redis_client.publish('channel_name', json.dumps(data))

# 訂閱者
pubsub = redis_client.pubsub()
pubsub.subscribe('channel_name')
```

### API 路由命名
```python
# RESTful 慣例
GET    /api/cameras           # 列出所有
GET    /api/cameras/<id>      # 取得單一
POST   /api/cameras           # 建立新的
PUT    /api/cameras/<id>      # 更新
DELETE /api/cameras/<id>      # 刪除

# 動作導向端點
POST   /api/cameras/<id>/start     # 啟動攝影機
POST   /api/cameras/<id>/stop      # 停止攝影機
GET    /api/cameras/<id>/snapshot  # 取得快照
```

## 編碼標準

### Python 編碼規範
```python
# PEP 8 標準，使用 black 格式化
# 每行最大長度：88 字元（black 預設）

# 匯入順序
import os                      # 標準函式庫
import sys

import flask                   # 第三方函式庫
import numpy as np

from models.user import User   # 本地匯入
from services.auth import authenticate

# 類別定義
class CameraManager:
    """管理攝影機連線和串流"""
    
    def __init__(self, config: dict):
        """初始化攝影機管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.cameras = {}
    
    def add_camera(self, camera_id: str, url: str) -> bool:
        """新增攝影機
        
        Args:
            camera_id: 攝影機識別碼
            url: RTSP URL
            
        Returns:
            是否成功新增
        """
        pass
```

### JavaScript 編碼規範
```javascript
// 使用 ES6+ 語法
// 使用 const/let，避免 var

// 模組化程式碼
class CameraStream {
    constructor(cameraId) {
        this.cameraId = cameraId;
        this.socket = null;
        this.isConnected = false;
    }
    
    // 使用 async/await
    async connect() {
        try {
            const response = await fetch(`/api/cameras/${this.cameraId}`);
            const data = await response.json();
            this.initializeSocket(data);
        } catch (error) {
            console.error('連線失敗:', error);
        }
    }
    
    // 私有方法使用 _ 前綴
    _handleError(error) {
        console.error(`Camera ${this.cameraId} error:`, error);
    }
}

// 匯出模組
export default CameraStream;
```

### 環境變數命名
```bash
# 使用大寫和底線
# 加上專案前綴避免衝突

# 資料庫配置
VISIONFLOW_DB_HOST=localhost
VISIONFLOW_DB_PORT=5432
VISIONFLOW_DB_NAME=visionflow
VISIONFLOW_DB_USER=admin
VISIONFLOW_DB_PASSWORD=secret

# Redis 配置
VISIONFLOW_REDIS_HOST=localhost
VISIONFLOW_REDIS_PORT=6379

# 應用程式配置
VISIONFLOW_SECRET_KEY=your-secret-key
VISIONFLOW_JWT_EXPIRY=86400
VISIONFLOW_LOG_LEVEL=INFO
```

## 資料庫規範

### 表格命名
- 使用單數名詞（例：`user`、`camera`）
- 使用 snake_case
- 關聯表：`<table1>_<table2>`（例：`user_camera`）

### 欄位命名
```sql
CREATE TABLE camera (
    id SERIAL PRIMARY KEY,           -- 主鍵固定為 id
    user_id INTEGER NOT NULL,        -- 外鍵使用 _id 後綴
    name VARCHAR(100) NOT NULL,      -- 描述性名稱
    rtsp_url VARCHAR(255),          -- 使用 snake_case
    is_active BOOLEAN DEFAULT true,  -- 布林值使用 is_ 前綴
    created_at TIMESTAMP DEFAULT NOW(), -- 時間戳記
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

## 測試結構

### 單元測試
```python
# tests/test_<module>.py
import pytest
from services.camera_service import CameraService

class TestCameraService:
    """攝影機服務測試"""
    
    @pytest.fixture
    def camera_service(self):
        """建立測試用服務實例"""
        return CameraService(test_config)
    
    def test_add_camera(self, camera_service):
        """測試新增攝影機功能"""
        result = camera_service.add_camera("cam1", "rtsp://test")
        assert result is True
```

## 日誌規範

### 日誌格式
```python
# 統一日誌格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 日誌層級使用
logger.debug("詳細除錯資訊")      # 開發階段
logger.info("一般操作資訊")        # 正常流程
logger.warning("警告但不影響")     # 潛在問題
logger.error("錯誤需要處理")       # 可恢復錯誤
logger.critical("系統崩潰")        # 致命錯誤
```

## Git 規範

### 分支策略
- `main`：穩定版本
- `develop`：開發分支
- `feature/<name>`：功能開發
- `bugfix/<name>`：錯誤修復
- `hotfix/<name>`：緊急修復

### Commit 訊息
```bash
# 格式：<類型>: <簡短描述>

feat: 新增攝影機即時串流功能
fix: 修正 JWT token 過期問題
docs: 更新 API 文件
refactor: 重構攝影機管理模組
test: 新增使用者認證測試
chore: 更新依賴套件版本
```

## Docker 最佳實踐

### Dockerfile 結構
```dockerfile
# 多階段建置
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["gunicorn", "app:app"]
```

### 服務健康檢查
```yaml
# docker-compose.yaml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 新功能開發流程

1. **需求分析**：明確功能需求和接受條件
2. **設計文件**：撰寫技術設計文件
3. **建立分支**：從 develop 建立 feature 分支
4. **實作功能**：遵循編碼規範開發
5. **撰寫測試**：單元測試和整合測試
6. **程式碼審查**：Pull Request 審查
7. **合併部署**：合併到 develop 並測試

## 效能考量

### 資料庫查詢
- 使用索引優化常用查詢
- 避免 N+1 查詢問題
- 使用分頁處理大量資料

### 快取策略
- Redis 快取熱門資料
- 設定合理的 TTL
- 實作快取失效機制

### 非同步處理
- 使用 Celery 處理耗時任務
- WebSocket 用於即時通訊
- 事件驅動架構處理高併發