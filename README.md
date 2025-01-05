# VisionFlow

[中文](./README.md) | [English](./README_en.md)

VisionFlow 是一個用於影像辨識與通知系統的後端應用程式。該專案基於 Flask 框架開發，使用 PostgreSQL 作為資料庫進行資料管理，並整合了 Redis 來管理攝影機影像的處理與分配。所有環境均可透過 Docker 進行配置與管理。

此專案旨在記錄個人的學習歷程，從理論學習到實踐應用，探索影像辨識與後端系統的整合開發。

---

## 功能介面展示

### 登入介面
用戶可以輸入賬號與密碼進行登入，並進入管理系統。
![登入介面](./readme_image/login.PNG)

### 註冊介面
提供用戶創建新賬號的功能，確保用戶權限管理的靈活性。
![註冊介面](./readme_image/register.PNG)

### 辨識串流
實時顯示攝影機的辨識結果，包括影像與辨識到的物件資訊。
- 支援多攝影機影像流展示。
- 根據模型輸出的物件標籤進行顯示。
![辨識串流](./readme_image/stream_interface.PNG)

### 攝影機管理
用戶可以新增、修改、刪除攝影機，並為攝影機指定辨識模型。
- 每個攝影機可綁定不同的模型。
- 配置攝影機的參數（如 URL、名稱、地點等）。
![攝影機管理](./readme_image/camera_management.PNG)

### 辨識區域繪製（可選）
用戶可以繪製多個感興趣區域（ROI），並對每個區域設置持續警報時間與整個通報時間段。
- 支援多邊形繪製。
- 可為每個區域設置單獨的參數。
![辨識區域繪製](./readme_image/detection_area.PNG)

---

## 快速開始

### 先決條件

在開始之前，請確保你已經安裝了以下工具：

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### 設置步驟

1. 將專案 clone 到本地環境：

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

5. 修改 `objectrecognition` 中的模型為你的模型 URL 或 PATH，並確保檔案命名為 `best.pt`。

6. 驗證應用程式是否成功啟動：

    在瀏覽器中訪問 [http://localhost:5000](http://localhost:5000)。

---

## API 說明

詳細 API 使用說明請參考 [API 文檔](./API_Doc.md)。

- 支援影像流處理的 API。
- 提供辨識模型的切換與管理接口。
- 提供攝影機管理的 RESTful API。

---

## 開發與測試

### 本地環境

1. 創建虛擬環境並安裝必要套件：

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2. 啟動 Flask 開發伺服器：

    ```bash
    flask run
    ```

3. 執行測試：

    ```bash
    pytest tests/
    ```

---

## License

本專案使用 [MIT License](LICENSE) 授權。

---

## 貢獻與聯繫方式

如果您對此項目有任何疑問或想要做出貢獻，歡迎與我聯繫。

- Email: sky328423@gmail.com
- GitHub Issues: [Issues](https://github.com/yourusername/VisionFlow/issues)

歡迎提交 PR 或提供建議！
