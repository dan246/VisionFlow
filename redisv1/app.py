import os
import redis
import cv2
import threading
from time import time, sleep, localtime, strftime
from datetime import datetime

# 初始化 Redis 連線
redis_host = 'redis'
redis_port = 6379
r = redis.Redis(host=redis_host, port=redis_port, db=0)

def fetch_frame(camera_id, camera_url, worker_key, stop_event):
    cap = cv2.VideoCapture(camera_url)
    reconnect_interval = 30
    frame_count = 0
    last_time = time()
    file_path = None

    while not stop_event.is_set():
        if not cap.isOpened():
            print(f"[{camera_id}] Camera connection lost. Reconnecting in {reconnect_interval} seconds...")
            cap.open(camera_url)
            sleep(reconnect_interval)
            r.set(f'camera_{camera_id}_status', 'False')
            continue

        ret, frame = cap.read()
        if not ret:
            print(f"[{camera_id}] Error reading frame. Retrying...")
            cap.release()
            cap.open(camera_url)
            print(f"[{camera_id}] Reconnecting to camera at URL: {camera_url}")
            sleep(1)
            r.set(f'camera_{camera_id}_status', 'False')
            continue

        frame_count += 1
        current_time = time()
        elapsed = current_time - last_time

        if elapsed >= 1.0:
            fps = frame_count / elapsed
            r.set(f'camera_{camera_id}_fps', fps)
            print(f"[{camera_id}] Camera FPS: {fps}")
            frame_count = 0
            last_time = current_time

        timestamp = current_time + 8 * 3600
        timestamp_str = strftime("%Y%m%d%H%M%S", localtime(timestamp))

        if frame_count % 100 == 0:
            folder_path = os.path.join('frames', str(camera_id), timestamp_str[:8], timestamp_str[8:10])
            os.makedirs(folder_path, exist_ok=True)
            file_name = f"{timestamp_str}.jpg"
            file_path = os.path.join(folder_path, file_name)
            
            # 刪除舊的檔案，只保留最新的一張截圖
            old_file_path = r.get(f'camera_{camera_id}_latest_frame_path')
            if old_file_path and os.path.exists(old_file_path):
                os.remove(old_file_path)
                print(f"[{camera_id}] Deleted old frame: {old_file_path}")

            cv2.imwrite(file_path, frame)
            print(f"[{camera_id}] Saved frame: {file_path}")
            r.set(f'camera_{camera_id}_latest_frame_path', file_path)

        _, buffer = cv2.imencode('.jpg', frame)
        image_data = buffer.tobytes()
        r.set(f'camera_{camera_id}_latest_frame', image_data)
        r.set(f'camera_{camera_id}_status', 'True')
        r.set(f'camera_{camera_id}_last_timestamp', timestamp_str)
        r.set(f'camera_{camera_id}_url', camera_url)

    cap.release()

def monitor_cameras(worker_key, camera_urls):
    threads = []
    stop_events = []
    for url in camera_urls:
        url_parts = url.decode('utf-8').split('|')
        camera_id = url_parts[0]
        camera_url = url_parts[1]
        stop_event = threading.Event()
        thread = threading.Thread(target=fetch_frame, args=(camera_id, camera_url, worker_key, stop_event))
        thread.start()
        threads.append((thread, stop_event))
    return threads

def setup_camera_manager():
    worker_id = os.getenv('WORKER_ID')
    if worker_id == '999':
        threading.Timer(10, setup_camera_manager).start()
    else:
        print(f"WORKER_ID is {worker_id}. Skipping setup.")

def main():
    setup_camera_manager()
    worker_id = os.getenv('WORKER_ID')
    if worker_id is None:
        raise ValueError("WORKER_ID environment variable is not set.")
    worker_key = f'worker_{worker_id}_urls'

    pubsub = r.pubsub()
    pubsub.subscribe([f'{worker_key}_update'])

    current_urls = set(r.smembers(worker_key))
    threads = monitor_cameras(worker_key, current_urls)

    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                new_urls = set(r.smembers(worker_key))
                if new_urls != current_urls:
                    for _, stop_event in threads:
                        stop_event.set()
                    for thread, _ in threads:
                        thread.join()
                    threads = monitor_cameras(worker_key, new_urls)
                    current_urls = new_urls
    finally:
        pubsub.close()

if __name__ == "__main__":
    main()
