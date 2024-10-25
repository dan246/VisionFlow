import os
import redis
import cv2
import multiprocessing
from time import time, sleep, localtime, strftime
from datetime import datetime

# 初始化 Redis 連線
redis_host = 'redis'
redis_port = 6379
redis_db = 0

def fetch_frame(camera_id, camera_url, worker_key, stop_event):
    # 在每個進程內初始化 Redis 連線
    r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

    cap = cv2.VideoCapture(camera_url)
    reconnect_interval = 30
    frame_count = 0
    last_time = time()
    file_path = None

    while not stop_event.is_set():
        try:
            if not cap.isOpened():
                print(f"[{camera_id}] 攝影機連線中斷，{reconnect_interval} 秒後重新連線...")
                cap.open(camera_url)
                sleep(reconnect_interval)
                r.set(f'camera_{camera_id}_status', 'False')
                continue

            ret, frame = cap.read()
            if not ret:
                print(f"[{camera_id}] 讀取畫面錯誤，重試中...")
                cap.release()
                cap.open(camera_url)
                print(f"[{camera_id}] 重新連線至攝影機 URL: {camera_url}")
                sleep(1)
                r.set(f'camera_{camera_id}_status', 'False')
                continue

            frame_count += 1
            current_time = time()
            elapsed = current_time - last_time

            if elapsed >= 1.0:
                fps = frame_count / elapsed
                r.set(f'camera_{camera_id}_fps', fps)
                print(f"[{camera_id}] 攝影機 FPS: {fps}")
                frame_count = 0
                last_time = current_time

            timestamp = current_time + 8 * 3600  # 調整時區（如果需要）
            timestamp_str = strftime("%Y%m%d%H%M%S", localtime(timestamp))

            if frame_count % 100 == 0:
                folder_path = os.path.join('frames', str(camera_id), timestamp_str[:8], timestamp_str[8:10])
                os.makedirs(folder_path, exist_ok=True)
                file_name = f"{timestamp_str}.jpg"
                file_path = os.path.join(folder_path, file_name)

                # 刪除舊的檔案，只保留最新的一張截圖
                old_file_path = r.get(f'camera_{camera_id}_latest_frame_path')
                if old_file_path:
                    old_file_path = old_file_path.decode('utf-8')
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                        print(f"[{camera_id}] 刪除舊的畫面：{old_file_path}")

                cv2.imwrite(file_path, frame)
                print(f"[{camera_id}] 儲存畫面：{file_path}")
                r.set(f'camera_{camera_id}_latest_frame_path', file_path)

            _, buffer = cv2.imencode('.jpg', frame)
            image_data = buffer.tobytes()
            r.set(f'camera_{camera_id}_latest_frame', image_data)
            r.set(f'camera_{camera_id}_status', 'True')
            r.set(f'camera_{camera_id}_last_timestamp', timestamp_str)
            r.set(f'camera_{camera_id}_url', camera_url)

        except Exception as e:
            print(f"[{camera_id}] 發生例外狀況：{e}")
            r.set(f'camera_{camera_id}_status', 'False')
            break  # 發生例外時退出迴圈

    cap.release()

def monitor_cameras(worker_key, camera_urls):
    processes = []
    for url in camera_urls:
        url_parts = url.decode('utf-8').split('|')
        camera_id = url_parts[0]
        camera_url = url_parts[1]
        print(f"啟動攝影機進程，ID：{camera_id}，URL：{camera_url}")
        stop_event = multiprocessing.Event()
        process = multiprocessing.Process(target=fetch_frame, args=(camera_id, camera_url, worker_key, stop_event))
        process.start()
        processes.append((process, stop_event))
    return processes

def main():
    worker_id = os.getenv('WORKER_ID')
    if worker_id is None:
        raise ValueError("未設定 WORKER_ID 環境變數")
    worker_key = f'worker_{worker_id}_urls'

    r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
    pubsub = r.pubsub()
    pubsub.subscribe([f'{worker_key}_update'])

    current_urls = set(r.smembers(worker_key))
    processes = monitor_cameras(worker_key, current_urls)

    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                new_urls = set(r.smembers(worker_key))
                if new_urls != current_urls:
                    print("檢測到攝影機列表更新，重新啟動進程")
                    for _, stop_event in processes:
                        stop_event.set()
                    for process, _ in processes:
                        process.join()
                    processes = monitor_cameras(worker_key, new_urls)
                    current_urls = new_urls
    finally:
        pubsub.close()
        for _, stop_event in processes:
            stop_event.set()
        for process, _ in processes:
            process.join()

if __name__ == "__main__":
    main()
