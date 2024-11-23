# VisionFlow

VisionFlow 是一個用於影像辨識與通知系統的後端應用程式。該專案使用 Flask 框架，並透過 PostgreSQL 作為資料庫進行資料管理。應用程式中整合了 Redis 來管理攝影機影像的處理與分配。所有環境均可使用 Docker 進行配置和管理。

---

## 功能介面展示

### 登入介面
![登入介面](./readme_image/login.PNG)

### 註冊介面
![註冊介面](./readme_image/register.PNG)

### 辨識串流
![辨識串流](./readme_image/stream_interface.PNG)

### 攝影機管理
![攝影機管理](./readme_image/camera_management.PNG)

### 辨識區域繪製
![辨識區域繪製](./readme_image/detection_area.PNG)

---

## 快速開始

### 先決條件

在開始之前，請確保你已經安裝了以下工具：

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### 設置步驟

1. clone 到本地環境：

    ```bash
    git clone https://github.com/yourusername/VisionFlow.git
    cd VisionFlow
    ```

2. 使用 Docker Compose 啟動服務：

    ```bash
    docker-compose -f docker-compose.yaml -f docker-compose-redis.yaml up -d
    ```

    這會自動下載所需的 Docker image，安裝相關套件，並在 `http://localhost:5000` 上啟動 Flask 應用程式。

3. 若需要遷移資料庫（在第一次運行或模型更新時執行）：

    ```bash
    docker-compose exec backend flask db upgrade
    ```

4. 配置 Redis 與多個 worker 節點：

    ```bash
    docker-compose -f docker-compose-redis.yaml up -d
    ```

5. 修改 `objectrecognition` 中的模型為你的模型 URL OR PATH，並確保檔案命名為 `best.pt`。

---

## API 說明

詳細 API 使用說明請參考 [API 文檔](./API_Doc.md)。

---

## License

本專案使用 [MIT License](LICENSE) 授權。

---

## Contributions & Contact

如果您對此項目有任何疑問或想要做出貢獻，歡迎與我聯繫。

Email: sky328423@gmail.com
