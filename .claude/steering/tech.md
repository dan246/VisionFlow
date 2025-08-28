# VisionFlow 技術架構引導文件

## 技術棧總覽

### 核心語言
- **Python 3.11+**：主要後端開發語言
- **JavaScript ES6+**：前端互動邏輯
- **HTML5/CSS3**：現代化網頁標準
- **Bash/Shell**：自動化腳本

### 後端框架
| 框架/函式庫 | 版本 | 用途 | 選擇原因 |
|------------|------|------|---------|
| Flask | 3.0.3 | Web 框架 | 輕量級、易學習、適合微服務 |
| Flask-SQLAlchemy | 3.x | ORM | 簡化資料庫操作 |
| Flask-SocketIO | 5.x | WebSocket | 即時通訊支援 |
| Gunicorn | 21.x | WSGI 伺服器 | 生產級部署 |
| Celery | 5.x | 任務佇列 | 非同步任務處理 |

### AI/ML 技術
| 技術 | 版本 | 用途 | 可替換方案 |
|------|------|------|-----------|
| YOLO | v11 | 物件偵測 | YOLOv8、Detectron2 |
| OpenCV | 4.x | 影像處理 | PIL、scikit-image |
| PyTorch | 2.x | 深度學習框架 | TensorFlow |
| Ultralytics | latest | YOLO 封裝 | 自定義實現 |

### 資料儲存
| 技術 | 版本 | 用途 | 配置 |
|------|------|------|------|
| PostgreSQL | 15 | 主資料庫 | 關聯式資料、使用者資訊 |
| Redis | 7 | 快取/佇列 | Session、任務佇列、即時資料 |
| 檔案系統 | - | 影像儲存 | 本地儲存處理後的影像 |

### 前端技術
| 技術 | 版本 | 用途 |
|------|------|------|
| Bootstrap | 5.3 | UI 框架 |
| Chart.js | 3.x | 資料視覺化 |
| Socket.IO Client | 4.x | 即時通訊 |
| Service Worker | - | PWA 支援 |

### 基礎設施
| 技術 | 用途 | 配置 |
|------|------|------|
| Docker | 容器化 | 多階段建置優化 |
| Docker Compose | 服務編排 | 開發/生產環境配置 |
| Nginx | 反向代理 | 負載平衡（選用） |
| GitHub Actions | CI/CD | 自動化測試部署（計劃中） |

## 架構決策記錄（ADR）

### ADR-001: 微服務架構
**決策**：採用微服務架構分離關注點
**原因**：
- 展示微服務設計能力
- 各服務可獨立開發和部署
- 易於擴展和維護
**權衡**：增加系統複雜度，但作為學習專案可接受

### ADR-002: YOLO 模型選擇
**決策**：使用 YOLO v11 作為主要偵測模型
**原因**：
- 即時性能優秀
- 社群支援完善
- 易於整合
**替代方案**：可輕鬆切換到其他模型（如 Detectron2、EfficientDet）

### ADR-003: Flask vs FastAPI
**決策**：選擇 Flask 而非 FastAPI
**原因**：
- 更熟悉的生態系統
- 豐富的擴展套件
- 適合學習專案
**未來考慮**：可遷移到 FastAPI 以獲得更好的性能和自動文檔

### ADR-004: PostgreSQL + Redis 組合
**決策**：使用 PostgreSQL 配合 Redis
**原因**：
- PostgreSQL：ACID 特性、複雜查詢支援
- Redis：高速快取、訊息佇列
**權衡**：增加維護複雜度但展示多資料庫整合能力

## 技術限制與約束

### 效能約束
- 同時處理攝影機數：建議 2-4 路
- 影像處理 FPS：15-30 fps（依硬體而定）
- API 延遲目標：< 500ms
- WebSocket 連線數：< 100 併發

### 安全考量
- JWT Token 過期時間：24 小時
- 密碼加密：bcrypt with salt
- CORS 配置：開發環境寬鬆，生產環境嚴格
- 輸入驗證：所有 API 端點需驗證

### 相容性需求
- 瀏覽器：Chrome 90+、Firefox 88+、Safari 14+
- Docker：20.10+
- Python：3.11+
- Node.js：16+（前端工具）

## 第三方服務整合

| 服務 | 用途 | 配置需求 |
|------|------|---------|
| SMTP | Email 通知 | SMTP 伺服器配置 |
| LINE Notify | 即時訊息 | API Token |
| WebRTC | 視訊串流（未來） | STUN/TURN 伺服器 |

## 開發工具與實踐

### 程式碼品質工具
- **Linting**：flake8、ESLint
- **格式化**：black、prettier
- **型別檢查**：mypy（選用）
- **測試**：pytest、Jest

### 監控與日誌
- **日誌**：Python logging、統一格式
- **監控**：Health check endpoints
- **錯誤追蹤**：Sentry（選用）
- **效能**：APM 工具（未來）

## AI 模型管理策略

### 模型版本控制
- 模型檔案存放在 `AImodels/` 目錄
- 使用語意化版本命名
- 支援模型熱切換

### 模型優化方向
1. **量化**：INT8 量化減少記憶體使用
2. **剪枝**：移除冗餘參數
3. **知識蒸餾**：訓練輕量級模型
4. **Edge 部署**：支援邊緣裝置

## 未來技術演進

### 短期改進（3 個月）
- [ ] 單元測試覆蓋率 > 70%
- [ ] API 文檔自動生成
- [ ] Docker 映像優化
- [ ] 效能監控整合

### 中期目標（6 個月）
- [ ] Kubernetes 部署支援
- [ ] GraphQL API 選項
- [ ] 更多 AI 模型支援
- [ ] 分散式追蹤

### 長期願景（12 個月）
- [ ] 雲端原生架構
- [ ] 自動擴展能力
- [ ] MLOps 流程
- [ ] 多租戶支援