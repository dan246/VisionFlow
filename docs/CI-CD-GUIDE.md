# VisionFlow CI/CD 使用指南

這個文件說明如何使用 VisionFlow 專案的 CI/CD 流程。

## 📋 目錄結構

```
.github/
├── workflows/
│   ├── ci-cd.yml           # 主要 CI/CD 流程
│   ├── security-scan.yml   # 安全掃描
│   └── release.yml         # 發布流程
scripts/
├── setup-dev.sh           # 開發環境設置
├── deploy.sh             # 部署腳本
└── monitor.sh            # 監控腳本
```

## 🚀 快速開始

### 1. 設置開發環境

```bash
# 執行開發環境設置腳本
./scripts/setup-dev.sh setup

# 或手動設置
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pre-commit install
```

### 2. 啟動開發服務

```bash
# 啟動開發用資料庫和 Redis
./scripts/setup-dev.sh

# 或使用 Docker Compose
docker-compose -f docker-compose.dev.yml up -d
```

### 3. 部署應用

```bash
# 部署到開發環境
./scripts/deploy.sh deploy development

# 部署到測試環境
./scripts/deploy.sh deploy staging

# 部署到生產環境
./scripts/deploy.sh deploy production
```

## 🔄 CI/CD 流程說明

### 分支策略

- `main` - 生產分支，觸發生產部署
- `staging` - 測試分支，觸發測試環境部署
- `dev` - 開發分支，觸發開發環境部署
- `feature/*` - 功能分支，觸發 CI 檢查

### 自動觸發條件

| 事件 | 分支 | 觸發的作業 |
|------|------|-----------|
| Push | `main` | CI → 構建 → 安全掃描 → 生產部署 |
| Push | `staging` | CI → 構建 → 整合測試 → 測試部署 |
| Push | `dev` | CI → 構建 → 基本測試 |
| Pull Request | 任何 | CI → 代碼檢查 → 測試 |
| Tag | `v*.*.*` | 發布流程 → 構建 Release |

### CI/CD 階段

#### 1. 程式碼品質檢查
- 代碼格式檢查 (Black, isort)
- 程式碼風格檢查 (flake8)
- 安全性掃描 (Bandit, Safety)
- 單元測試執行
- 測試覆蓋率報告

#### 2. Docker 映像構建
- 多服務並行構建
- 多架構支援 (amd64, arm64)
- 映像快取優化
- 映像標籤管理

#### 3. 安全掃描
- 依賴性漏洞掃描
- 容器映像掃描 (Trivy)
- 程式碼安全掃描

#### 4. 整合測試
- 服務間整合測試
- API 端點測試
- 健康檢查測試

#### 5. 部署
- 多環境部署支援
- 滾動更新策略
- 自動回滾機制

## 🛠️ 本地開發工作流程

### 開始新功能開發

```bash
# 1. 建立功能分支
git checkout -b feature/new-feature

# 2. 設置開發環境
./scripts/setup-dev.sh

# 3. 開始開發...

# 4. 執行本地測試
./scripts/setup-dev.sh test

# 5. 提交代碼 (pre-commit hooks 會自動執行)
git add .
git commit -m "feat: 新增功能描述"

# 6. 推送到遠端
git push origin feature/new-feature

# 7. 建立 Pull Request
```

### 本地測試

```bash
# 程式碼格式化
black .
isort .

# 程式碼檢查
flake8 .

# 安全檢查
bandit -r .
safety check

# 執行測試
pytest tests/ -v --cov=./

# 整合測試
docker-compose -f docker-compose.test.yml up -d
pytest tests/integration/ -v
```

## 📦 部署管理

### 環境配置

每個環境都有對應的環境檔案：
- `.env.dev` - 開發環境
- `.env.staging` - 測試環境  
- `.env.prod` - 生產環境

### 部署命令

```bash
# 檢查服務狀態
./scripts/deploy.sh status

# 查看服務日誌
./scripts/deploy.sh logs

# 健康檢查
./scripts/deploy.sh health

# 重啟服務
./scripts/deploy.sh restart [environment]

# 停止服務
./scripts/deploy.sh stop

# 清理資源
./scripts/deploy.sh cleanup
```

### 監控和日誌

```bash
# 執行完整監控
./scripts/monitor.sh monitor

# 實時監控
./scripts/monitor.sh realtime

# 生成監控報告
./scripts/monitor.sh report

# 清理舊日誌
./scripts/monitor.sh cleanup 30
```

## 🔐 安全最佳實踐

### 環境變數管理

1. 不要在代碼中硬編碼敏感資訊
2. 使用 GitHub Secrets 管理生產環境變數
3. 定期更新密碼和 API 金鑰
4. 使用強密碼和加密

### 映像安全

1. 定期更新基礎映像
2. 掃描映像漏洞
3. 最小權限原則
4. 移除不必要的套件

### 網路安全

1. 啟用 HTTPS/TLS
2. 設置防火牆規則
3. 使用安全標頭
4. 限制 API 存取頻率

## 📊 監控和告警

### 健康檢查端點

每個服務都應該提供健康檢查端點：
- `GET /health` - 基本健康檢查
- `GET /ready` - 就緒檢查
- `GET /metrics` - Prometheus 指標

### 日誌管理

- 結構化日誌格式
- 適當的日誌等級
- 日誌輪轉和保留
- 集中化日誌收集

### 指標收集

- 系統資源使用率
- 應用程式效能指標
- 業務指標
- 錯誤率和延遲

## 🐛 故障排除

### 常見問題

1. **容器啟動失敗**
   ```bash
   # 檢查容器日誌
   docker-compose logs [service_name]
   
   # 檢查映像是否存在
   docker images
   ```

2. **服務無法連接**
   ```bash
   # 檢查網路連接
   docker network ls
   docker network inspect [network_name]
   
   # 檢查端口映射
   docker-compose ps
   ```

3. **資料庫連接問題**
   ```bash
   # 檢查資料庫狀態
   docker-compose exec db pg_isready
   
   # 檢查環境變數
   docker-compose exec web env | grep POSTGRES
   ```

### 調試技巧

1. 使用 `docker-compose exec` 進入容器調試
2. 檢查日誌文件的詳細錯誤訊息
3. 使用健康檢查端點驗證服務狀態
4. 監控資源使用情況

## 📝 最佳實踐

### Git 工作流程

1. 使用有意義的提交訊息
2. 小而頻繁的提交
3. 代碼審查流程
4. 保持分支同步

### Docker 最佳實踐

1. 使用多階段構建
2. 最小化映像大小
3. 適當的標籤策略
4. 健康檢查配置

### 測試策略

1. 單元測試覆蓋率 > 80%
2. 整合測試關鍵路徑
3. 性能測試
4. 安全測試

## 🔗 相關資源

- [Docker 官方文檔](https://docs.docker.com/)
- [GitHub Actions 文檔](https://docs.github.com/en/actions)
- [Flask 最佳實踐](https://flask.palletsprojects.com/en/2.0.x/)
- [PostgreSQL 文檔](https://www.postgresql.org/docs/)
- [Redis 文檔](https://redis.io/documentation)
