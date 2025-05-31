# GitHub Repository 設定指南

此文件說明如何設定 GitHub repository 以支援完整的 CI/CD 流程。

## 🔧 必要設定

### 1. 啟用 GitHub Actions

1. 進入 GitHub repository
2. 點擊 `Settings` → `Actions` → `General`
3. 確保 "Allow all actions and reusable workflows" 已啟用

### 2. 設定環境保護 (Environment Protection)

#### 建立 Staging 環境
1. 進入 `Settings` → `Environments`
2. 點擊 `New environment`
3. 環境名稱：`staging`
4. 設定保護規則（可選）：
   - Required reviewers: 可以留空
   - Wait timer: 0 分鐘
   - Deployment branches: 限制為 `staging` 分支

#### 建立 Production 環境
1. 點擊 `New environment`
2. 環境名稱：`production`
3. 設定保護規則（建議）：
   - ✅ Required reviewers: 添加團隊成員
   - ✅ Wait timer: 5-10 分鐘
   - ✅ Deployment branches: 限制為 `main` 分支

### 3. 設定 Secrets

進入 `Settings` → `Secrets and variables` → `Actions`，添加以下 secrets：

#### Repository Secrets
- `GITHUB_TOKEN` - GitHub 自動提供
- `SONAR_TOKEN` - SonarCloud 分析 token（可選）

#### 生產環境 Secrets（如果使用外部服務）
- `DOCKER_HUB_USERNAME` - Docker Hub 用戶名
- `DOCKER_HUB_TOKEN` - Docker Hub 存取 token
- `DEPLOY_KEY` - 部署伺服器 SSH 金鑰

### 4. 設定分支保護規則

#### 保護 main 分支
1. 進入 `Settings` → `Branches`
2. 點擊 `Add rule`
3. 分支名稱模式：`main`
4. 啟用以下選項：
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Restrict pushes to matching branches

#### 設定必需的狀態檢查
添加以下 checks：
- `程式碼檢查與測試`
- `構建 Docker 映像`
- `安全性掃描`

## 🚀 啟用環境保護後

啟用環境保護後，可以取消註釋 `ci-cd.yml` 中的 environment 設定：

```yaml
deploy-staging:
  # ...
  environment: staging  # 取消註釋

deploy-production:
  # ...
  environment: production  # 取消註釋
```

## 🔧 手動批准設定

### 選項 1: 使用 GitHub 環境保護
- 在環境設定中啟用 "Required reviewers"
- 系統會自動要求審查者批准部署

### 選項 2: 使用第三方 Action
安裝 `trstringer/manual-approval` action：

```yaml
- name: 等待手動批准
  uses: trstringer/manual-approval@v1
  with:
    secret: ${{ secrets.GITHUB_TOKEN }}
    approvers: user1,user2
    minimum-approvals: 1
```

## 📊 監控設定

### 1. 啟用 GitHub Packages
1. 進入 `Settings` → `Actions` → `General`
2. 在 "Workflow permissions" 中：
   - 選擇 "Read and write permissions"
   - ✅ Allow GitHub Actions to create and approve pull requests

### 2. 設定通知
1. 進入 `Settings` → `Notifications`
2. 啟用 Actions 相關通知
3. 設定 Slack/Discord webhook（可選）

## 🔐 安全最佳實踐

1. **最小權限原則**
   - 只給必要的權限
   - 定期審查 secrets

2. **環境隔離**
   - 不同環境使用不同的 secrets
   - 限制分支存取權限

3. **審計日誌**
   - 定期檢查 Actions 日誌
   - 監控異常活動

## ❗ 常見問題

### Q: 為什麼 environment 顯示紅色錯誤？
A: 需要先在 GitHub repository 設定中建立對應的環境。

### Q: 如何測試 CI/CD 流程？
A: 
1. 建立測試分支
2. 推送變更觸發 Actions
3. 檢查 Actions 頁面的執行結果

### Q: 部署失敗怎麼辦？
A: 
1. 檢查 Actions 日誌
2. 確認 secrets 設定正確
3. 檢查目標環境狀態

---

完成這些設定後，您的 VisionFlow CI/CD 流程就可以完全運作了！
