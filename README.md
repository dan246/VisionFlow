<div align="center">

# 🎯 VisionFlow

**智能影像辨識與監控系統 - 個人學習開發歷程記錄**

> ⚠️ **免責聲明與專案性質**：  
> 📖 這是一個**個人學習開發歷程記錄專案**，記錄我在學習 AI 影像辨識技術過程中的實作經驗與心得。  
> 🎓 本專案**僅供學習參考使用**，屬於個人技術學習的成果展示與紀錄。  
> ⚠️ **請勿直接用於生產環境或商業用途**，作者不對使用本專案所造成的任何問題負責。  
> 🔧 如有實際應用需求，請基於本專案進行重新設計、安全審查及完整測試。  
> 💡 歡迎其他學習者參考交流，但請理解這只是個人學習過程的記錄，非完整的產品級解決方案。

[![Docker](https://img.shields.io/badge/Docker-20.10+-blue?style=flat-square&logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-green?style=flat-square&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-orange?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7+-red?style=flat-square&logo=redis)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
![Learning Project](https://img.shields.io/badge/Status-學習專案-orange?style=flat-square)

[🇹🇼 中文](./README.md) | [🇺🇸 English](./README_en.md)

</div>

---

## 📋 專案概述

**VisionFlow** 是我在學習 AI 影像辨識與監控系統開發過程中的實作專案。這個專案記錄了我在學習微服務架構、深度學習技術和現代化部署方案時的開發歷程與實作經驗。

> 📝 **學習歷程記錄**：  
> 這個專案完整記錄了我從零開始學習以下技術的過程：
> - 🤖 深度學習與電腦視覺 (YOLO 模型應用)
> - 🏗️ 微服務架構設計與實作經驗
> - 🐳 Docker 容器化技術與服務編排
> - 🌐 Flask Web 框架與 RESTful API 開發
> - 🗄️ 資料庫設計與管理 (PostgreSQL + Redis)
> - 📡 即時通訊技術與 WebSocket 實作

> ⚠️ **學習專案聲明**：
> - 這是我個人的**學習實作記錄**，程式碼可能存在不完善之處
> - 未經過完整的安全性檢查和企業級測試
> - 主要目的是**記錄學習過程**和**技術實驗**
> - 如需用於實際專案，請自行評估並進行必要的改進

### 🌟 核心特色

> 💡 **學習重點**：透過實作以下功能來學習相關技術

- 🚀 **實時影像辨識** - 使用 YOLO 模型進行高效物件檢測
- 🎥 **多攝影機支援** - 同時管理多個攝影機串流
- 🔒 **用戶權限管理** - 完整的身份驗證與授權系統
- 🎨 **自定義檢測區域** - 支援多邊形 ROI 繪製
- 📱 **響應式介面** - 現代化的 Web 管理界面
- 🐳 **容器化部署** - 完整的 Docker 支援
- ⚡ **高效能架構** - Redis 快取與負載均衡

### 🛠️ 技術架構

> 📚 **學習技術棧**：

- **後端框架**: Flask + RESTful API
- **資料庫**: PostgreSQL (主要) + Redis (快取)
- **AI 模型**: YOLO v11 物件檢測
- **容器化**: Docker + Docker Compose
- **前端**: 現代化 JavaScript + Bootstrap
- **通訊**: WebSocket 實時串流

---

## 🖼️ 功能展示

<div align="center">

### 🔐 登入介面
<details>
<summary>點擊查看詳細畫面</summary>

用戶可以輸入賬號與密碼進行登入，並進入管理系統。

![登入介面](./readme_image/login.PNG)

</details>

### 📝 註冊介面
<details>
<summary>點擊查看詳細畫面</summary>

提供用戶創建新賬號的功能，確保用戶權限管理的靈活性。

![註冊介面](./readme_image/register.PNG)

</details>

### 🎬 實時辨識串流
<details>
<summary>點擊查看詳細畫面</summary>

**核心功能亮點：**
- ⚡ 實時顯示攝影機的辨識結果
- 🎯 支援多攝影機影像流展示
- 🏷️ 根據模型輸出的物件標籤進行顯示
- 📊 即時檢測統計資訊

![辨識串流](./readme_image/stream_interface.PNG)

</details>

### 📹 攝影機管理
<details>
<summary>點擊查看詳細畫面</summary>

**管理功能：**
- ➕ 新增、修改、刪除攝影機
- 🔧 為攝影機指定辨識模型
- ⚙️ 配置攝影機參數（URL、名稱、地點等）
- 🔄 即時狀態監控

![攝影機管理](./readme_image/camera_management.PNG)

</details>

### 🎨 智能檢測區域設定
<details>
<summary>點擊查看詳細畫面</summary>

**進階功能：**
- 🖌️ 支援多邊形 ROI 繪製
- ⏰ 可為每個區域設置警報時間
- 🎯 自定義檢測靈敏度
- 📐 精確的座標定位

![辨識區域繪製](./readme_image/detection_area.PNG)

</details>

</div>

---

## 🚀 快速開始

> ⚠️ **重要提醒**：以下步驟僅適用於**學習環境**，這只是我個人學習過程的記錄！  
> 📚 如果你也在學習相關技術，歡迎參考我的實作經驗，但請注意這並非完整的產品級解決方案。

### 📋 系統需求

在開始之前，請確保您的系統已安裝：

| 工具 | 版本要求 | 說明 |
|------|----------|------|
| 🐳 [Docker](https://www.docker.com/) | 20.10+ | 容器化平台 |
| 🏗️ [Docker Compose](https://docs.docker.com/compose/) | 2.0+ | 多容器編排工具 |
| 💻 作業系統 | Linux/macOS/Windows | 支援跨平台部署 |

### ⚡ 快速體驗（學習用途）

<details>
<summary><strong>📦 標準部署（適合學習測試）</strong></summary>

```bash
# 1️⃣ 克隆專案
git clone https://github.com/yourusername/VisionFlow.git
cd VisionFlow

# 2️⃣ 啟動所有服務
docker-compose -f docker-compose.optimized.yaml up -d

# 3️⃣ 等待服務啟動完成（約 2-3 分鐘）
docker-compose -f docker-compose.optimized.yaml ps

# 4️⃣ 初始化資料庫
docker-compose -f docker-compose.optimized.yaml exec backend flask db upgrade
```

> 🎓 **學習提示**：觀察 docker-compose 的編排過程，了解微服務的啟動順序

</details>

<details>
<summary><strong>🔧 開發者模式（適合程式碼學習）</strong></summary>

```bash
# 1️⃣ 克隆專案
git clone https://github.com/yourusername/VisionFlow.git
cd VisionFlow

# 2️⃣ 啟動基礎服務
docker-compose -f docker-compose.yaml up -d

# 3️⃣ 啟動 Redis 工作節點
docker-compose -f docker-compose-redis.yaml up -d

# 4️⃣ 資料庫遷移
docker-compose exec backend flask db upgrade
```

> 🎓 **學習提示**：可以透過修改程式碼來觀察系統行為變化

</details>

### 🎯 驗證部署

部署完成後，請訪問以下地址確認服務狀態：

| 服務 | 地址 | 說明 |
|------|------|------|
| 🌐 Web 界面 | [http://localhost:5001](http://localhost:5001) | 主要管理界面 |
| 📹 攝影機串流 | [http://localhost:15440](http://localhost:15440) | 攝影機控制器 |
| 📊 Redis 管理 | [http://localhost:6379](http://localhost:6379) | Redis 資料庫 |
| 🗄️ PostgreSQL | [http://localhost:5433](http://localhost:5433) | 主資料庫 |

### 🔧 自定義配置

<details>
<summary><strong>📝 環境變數設定</strong></summary>

創建 `.env` 檔案並設定以下變數：

```bash
# 資料庫設定
POSTGRES_DB=visionflow_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password

# Redis 設定
REDIS_HOST=redis
REDIS_PORT=6379

# 應用程式設定
FLASK_ENV=production
SECRET_KEY=your_secret_key_here

# 模型設定
MODEL_PATH=/app/models/yolo11n.pt
CONFIDENCE_THRESHOLD=0.5
```

</details>

---

## 📚 API 文檔

<div align="center">

### 🔗 完整 API 參考

| 文檔類型 | 連結 | 說明 |
|----------|------|------|
| 📖 **基礎 API** | [API_Doc.md](./API_Doc.md) | 核心 API 使用說明 |
| 🚀 **進階 API** | [API_ENHANCED.md](./API_ENHANCED.md) | 高級功能與擴展 API |
| 🎯 **專案總覽** | [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) | 專案架構與設計理念 |

</div>

### 🌟 主要 API 功能

<details>
<summary><strong>🎥 影像串流 API</strong></summary>

```http
# 獲取實時串流
GET /recognized_stream/{camera_id}

# 獲取原始串流
GET /get_stream/{camera_id}

# 獲取快照
GET /get_snapshot/{camera_id}
```

</details>

<details>
<summary><strong>📹 攝影機管理 API</strong></summary>

```http
# 獲取所有攝影機
GET /api/camera/cameras

# 新增攝影機
POST /api/camera/cameras

# 更新攝影機
PATCH /api/camera/cameras/{id}

# 刪除攝影機
DELETE /api/camera/cameras/{id}
```

</details>

<details>
<summary><strong>🔐 認證與授權 API</strong></summary>

```http
# 用戶登入
POST /api/auth/login

# 用戶註冊
POST /api/auth/register

# Token 刷新
POST /api/auth/refresh
```

</details>

---

## 🛠️ 開發指南

### 💻 本地開發環境

<details>
<summary><strong>🐍 Python 環境設定</strong></summary>

```bash
# 1️⃣ 創建虛擬環境
python3 -m venv venv

# 2️⃣ 啟用虛擬環境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3️⃣ 安裝依賴套件
pip install -r requirements.txt

# 4️⃣ 啟動開發伺服器
flask run --debug
```

</details>

<details>
<summary><strong>🧪 測試與品質檢查</strong></summary>

```bash
# 🔍 執行單元測試
pytest tests/ -v

# 📊 程式碼覆蓋率
pytest --cov=./ tests/

# 🎨 程式碼格式化
black . --line-length 88

# 🔧 靜態分析
flake8 . --max-line-length 88
```

</details>

### 🏗️ 專案架構

```
VisionFlow/
├── 🌐 web/                 # Web 後端服務
├── 📹 camera_ctrler/       # 攝影機控制器
├── 🤖 object_recognition/  # AI 辨識服務
├── 📦 redisv1/            # Redis 工作節點
├── 🗄️ db/                 # 資料庫檔案
├── 📊 shared/             # 共享模組
└── 🐳 docker-compose.*.yaml # 容器編排配置
```

---

## 🤝 貢獻與支援

<div align="center">

### 🌟 加入我們的開發者社群

[![GitHub Issues](https://img.shields.io/badge/Issues-歡迎回報-red?style=for-the-badge&logo=github)](https://github.com/yourusername/VisionFlow/issues)
[![Pull Requests](https://img.shields.io/badge/PR-歡迎貢獻-green?style=for-the-badge&logo=github)](https://github.com/yourusername/VisionFlow/pulls)
[![Discussions](https://img.shields.io/badge/討論區-加入討論-blue?style=for-the-badge&logo=github)](https://github.com/yourusername/VisionFlow/discussions)

</div>

### 📞 聯絡方式

| 聯絡管道 | 資訊 | 說明 |
|----------|------|------|
| 📧 **Email** | [sky328423@gmail.com](mailto:sky328423@gmail.com) | 學習交流與技術討論 |
| 🐛 **Bug 回報** | [GitHub Issues](https://github.com/yourusername/VisionFlow/issues) | 問題回報與功能建議 |
| 💬 **討論** | [GitHub Discussions](https://github.com/yourusername/VisionFlow/discussions) | 學習心得分享與經驗交流 |

### 🎯 如何貢獻

<details>
<summary><strong>🔧 程式碼貢獻</strong></summary>

1. **Fork** 本專案
2. 創建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟一個 **Pull Request**

</details>

<details>
<summary><strong>📝 文檔貢獻</strong></summary>

- 改善 README 或 API 文檔
- 翻譯文檔到其他語言
- 增加使用範例和教學

</details>

<details>
<summary><strong>🐛 問題回報</strong></summary>

回報問題時請包含：
- 作業系統版本
- Docker 版本
- 錯誤訊息截圖
- 重現步驟

</details>

---

## 📄 授權條款

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

本專案採用 **MIT 授權條款** - 詳見 [LICENSE](LICENSE) 檔案

</div>

---

<div align="center">

### 🌟 如果這個學習記錄對您有幫助，請給我一個 Star ⭐

**感謝您的支持！這是我持續學習和改進的動力！**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/VisionFlow?style=social)](https://github.com/dan246/VisionFlow/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/VisionFlow?style=social)](https://github.com/dan246/VisionFlow/network)

---

**🚀 VisionFlow - 個人學習歷程記錄專案**

*記錄我在 AI 影像辨識領域的學習與成長 📚*

</div>
