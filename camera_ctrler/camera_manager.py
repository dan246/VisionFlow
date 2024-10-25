# camera_manager.py
import threading
import redis
import requests
import logging
import os
import time  # 加入 time 模組以使用 sleep
from env import SERVERIP

# 預設設置工作器 ID
worker_id = int(os.getenv('WORKER_ID', 1))

class CameraManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.worker_id = worker_id
        self.worker_key = f'worker_{self.worker_id}_urls'
        self.SERVERIP = SERVERIP
        self.num_workers = 3  # 3 個工作器

    def clear_old_cameras(self, current_camera_ids):
        # 遍歷所有與攝影機相關的鍵，假設攝影機相關的鍵以 'camera_' 開頭
        for key in self.redis_client.scan_iter("camera_*"):
            # 從鍵名中提取攝影機 ID（假設鍵的格式為 'camera_{camera_id}_data'）
            key_str = key.decode('utf-8')
            camera_id = key_str.split('_')[1]
            if int(camera_id) not in current_camera_ids:
                # 如果攝影機 ID 不在當前資料庫中，則刪除該鍵
                self.redis_client.delete(key)
                logging.info(f"已從 Redis 中刪除舊攝影機資料，攝影機 ID：{camera_id}")

        # 繼續刪除所有工作器的攝影機列表鍵
        for worker_id in range(1, self.num_workers + 1):
            worker_key = f'worker_{worker_id}_urls'
            self.redis_client.delete(worker_key)
            logging.info(f"已清除工作器 {worker_id} 的舊攝影機資料。")

    def fetch_and_update_cameras(self, previous_camera_ids):
        # 從伺服器獲取最新的攝影機列表
        url = f"{self.SERVERIP}/cameras/all"
        headers = {}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            try:
                # 假設 response.json() 返回的是列表
                camera_data = response.json()
                current_camera_ids = set(camera['id'] for camera in camera_data)
                updated = False  # 標記是否有更新

                if current_camera_ids != previous_camera_ids:
                    # 如果攝影機列表有變化，更新 Redis
                    self.clear_old_cameras(current_camera_ids)
                    updated = True  # 標記有變更

                for camera in camera_data:
                    worker_id = int(camera['id']) % self.num_workers + 1
                    worker_key = f'worker_{worker_id}_urls'
                    redis_key = f"{camera['id']}|{camera['stream_url']}"

                    # 若 URL 發生變化，則刪除舊的 key 並添加新的 key
                    # 檢查攝影機是否在 Redis 中
                    existing_urls = self.redis_client.smembers(worker_key)
                    matching_key = next((key for key in existing_urls if key.decode().startswith(f"{camera['id']}|")), None)

                    if matching_key is None or matching_key.decode() != redis_key:
                        # 刪除舊的 key，若存在
                        if matching_key:
                            self.redis_client.srem(worker_key, matching_key)
                            logging.info(f"已移除舊的攝影機 {camera['id']} URL。")

                        # 添加新的 key
                        self.redis_client.sadd(worker_key, redis_key)
                        logging.info(f"已將攝影機 {camera['id']} 的新 URL 更新至 Redis，位於工作器 {worker_id}。")
                        updated = True  # 標記有更新

                if updated:
                    # 發布更新事件給所有工作器
                    for worker_id in range(1, self.num_workers + 1):
                        worker_key = f'worker_{worker_id}_urls'
                        self.redis_client.publish(f'{worker_key}_update', 'updated')
                        logging.info(f"已發布工作器 {worker_id} 的更新。")
                    
                    # 更新之前的攝影機 ID 列表
                    previous_camera_ids.clear()
                    previous_camera_ids.update(current_camera_ids)

            except Exception as e:
                logging.error(f"處理攝影機數據時發生錯誤: {e}")
        else:
            logging.error(f"請求失敗，狀態碼：{response.status_code}")

    def monitor_cameras(self):
        # 定期檢查攝影機列表是否有變化
        previous_camera_ids = set()
        while True:
            self.fetch_and_update_cameras(previous_camera_ids)
            time.sleep(5)  # 每 5 秒檢查一次

    def run(self):
        # 啟動攝影機監控執行緒
        thread = threading.Thread(target=self.monitor_cameras)
        thread.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = CameraManager()
    manager.run()
