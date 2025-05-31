# VisionFlow CI/CD 實現指南 🚀

這個文件詳細說明了為 VisionFlow 專案實現的完整 CI/CD 流程。

## 📋 實現概覽

### 已完成的 CI/CD 基礎設施

1. **GitHub Actions 工作流程**
   - 主要 CI/CD 流程 (`.github/workflows/ci-cd.yml`)
   - 安全掃描工作流程 (`.github/workflows/security-scan.yml`)
   - 發布自動化 (`.github/workflows/release.yml`)

2. **程式碼品質工具**
   - Pre-commit hooks (`.pre-commit-config.yaml`)
   - YAML 檢查配置 (`.yamllint.yml`)
   - SonarCloud 配置 (`sonar-project.properties`)

3. **環境管理**
   - 多環境配置檔案 (`.env.dev`, `.env.prod`)
   - 環境範例檔案 (`.env.example`)

4. **部署和監控腳本**
   - 多環境部署腳本 (`scripts/deploy.sh`)
   - 系統監控腳本 (`scripts/monitor.sh`)
   - 開發環境設置腳本 (`scripts/setup-dev.sh`)

5. **專案自動化**
   - Makefile 與 40+ 自動化命令
   - 開發工作流程簡化

6. **文檔**
   - CI/CD 使用指南 (`docs/CI-CD-GUIDE.md`)
   - 故障排除指南 (`docs/TROUBLESHOOTING.md`)

## 🛠️ 如何使用

### 快速開始

1. **設置開發環境**
   ```bash
   chmod +x scripts/*.sh
   ./scripts/setup-dev.sh setup
   ```

2. **使用 Makefile 命令**
   ```bash
   make help           # 查看所有可用命令
   make dev-setup      # 設置開發環境
   make quick-start    # 快速啟動整個系統
   make ci-check       # 執行 CI 檢查
   ```

3. **部署到不同環境**
   ```bash
   ./scripts/deploy.sh deploy development   # 開發環境
   ./scripts/deploy.sh deploy staging      # 測試環境
   ./scripts/deploy.sh deploy production   # 生產環境
   ```

### CI/CD 流程觸發

- **推送到 `main` 分支**: 觸發完整 CI/CD 流程，部署到生產環境
- **推送到 `staging` 分支**: 觸發測試環境部署
- **推送到 `dev` 分支**: 觸發開發環境部署
- **建立 Pull Request**: 觸發 CI 檢查和測試
- **建立 Release Tag**: 觸發自動化發布流程

### 監控和維護

```bash
./scripts/monitor.sh monitor    # 完整系統監控
./scripts/monitor.sh health     # 健康檢查
./scripts/monitor.sh realtime   # 實時監控
./scripts/monitor.sh report     # 生成監控報告
```

## 🔧 配置說明

### GitHub Secrets 設置

在 GitHub repository 中需要設置以下 secrets：

- `GITHUB_TOKEN`: GitHub 自動生成
- `SONAR_TOKEN`: SonarCloud 分析 token
- `DOCKER_HUB_USERNAME`: Docker Hub 用戶名 (如果使用)
- `DOCKER_HUB_TOKEN`: Docker Hub 存取 token (如果使用)

### 環境變數配置

1. 複製環境範例檔案：
   ```bash
   cp .env.example .env.dev
   cp .env.example .env.prod
   ```

2. 編輯環境檔案，設置實際的配置值

### 服務映像標籤

CI/CD 流程會自動為每個服務建構 Docker 映像：
- `web` - 主要 Web 應用
- `camera-ctrl` - 相機控制服務
- `object-recognition` - 物件辨識服務  
- `redis-worker` - Redis 工作節點

## 📊 監控和指標

### 健康檢查端點

每個服務都提供健康檢查端點：
- `GET /health` - 基本健康檢查
- `GET /ready` - 就緒狀態檢查

### 自動化監控

- 系統資源監控
- 服務健康狀態檢查
- 日誌收集和分析
- 異常警告通知

## 🔐 安全措施

### 程式碼安全

- **Bandit**: Python 程式碼安全掃描
- **Safety**: 依賴性漏洞檢查
- **Trivy**: 容器映像漏洞掃描

### 存取控制

- 多環境隔離
- 敏感資訊加密存儲
- 最小權限原則

## 📈 效能優化

### Docker 優化

- 多階段建構減少映像大小
- 建構快取提升建構速度
- 多架構支援 (amd64, arm64)

### CI/CD 優化

- 並行執行減少建構時間
- 快取策略優化
- 增量測試和建構

## 🐛 故障排除

### 常見問題

1. **建構失敗**: 檢查 Dockerfile 和依賴
2. **測試失敗**: 檢查測試環境配置
3. **部署失敗**: 檢查環境變數和網路連接
4. **服務啟動失敗**: 檢查容器日誌和資源限制

### 調試命令

```bash
# 檢查服務狀態
make status

# 查看日誌
make logs

# 健康檢查
make health

# 完整診斷
./scripts/monitor.sh monitor
```

## 📝 開發工作流程

### 功能開發

1. 建立功能分支
2. 本地開發和測試
3. 提交程式碼 (pre-commit hooks 自動執行)
4. 建立 Pull Request
5. CI 檢查通過後合併

### 發布流程

1. 建立 Release tag
2. 自動觸發建構和測試
3. 生成 Release 資產
4. 部署到生產環境

## 🎯 最佳實踐

### 程式碼品質

- 程式碼覆蓋率 > 80%
- 通過所有靜態分析檢查
- 遵循專案編碼規範

### 部署策略

- 滾動更新
- 健康檢查驗證
- 自動回滾機制

### 監控和告警

- 關鍵指標監控
- 異常自動告警
- 定期巡檢報告

## 🔗 相關文檔

- [CI/CD 使用指南](docs/CI-CD-GUIDE.md)
- [GitHub Repository 設定指南](docs/GITHUB-SETUP.md) 🆕
- [故障排除指南](docs/TROUBLESHOOTING.md)
- [API 文檔](API_Doc.md)
- [專案總覽](PROJECT_SUMMARY.md)

---

**注意**: 這個 CI/CD 實現是為學習目的而設計的完整解決方案。在實際生產環境中使用時，請根據具體需求進行調整和優化。

## 🎉 總結

VisionFlow 的 CI/CD 實現提供了：

✅ **自動化** - 從程式碼提交到生產部署的完全自動化流程  
✅ **品質保證** - 多層次的程式碼品質和安全檢查  
✅ **多環境支援** - 開發、測試、生產環境的獨立管理  
✅ **監控告警** - 完整的系統監控和異常告警機制  
✅ **文檔完整** - 詳細的使用指南和故障排除文檔  
✅ **擴展性** - 易於根據需求擴展和定制的架構  

這個實現展示了現代軟體開發中 CI/CD 的最佳實踐，適合作為學習和參考的完整範例。
