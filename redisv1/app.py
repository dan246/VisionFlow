"""
Redis Worker Application
Enhanced with configuration management and error handling.
"""

import os
import sys
import redis
import cv2
import multiprocessing
import logging
from time import time, sleep, localtime, strftime
from datetime import datetime
from typing import Dict, Any, Optional

# Local imports
from config import RedisWorkerConfig as Config

# Setup logging
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('redis_worker.log')
        ]
    )
    return logging.getLogger(__name__)

# Initialize configuration and logger
config = Config()
logger = setup_logging(config.LOG_LEVEL)

def init_redis_connection() -> redis.Redis:
    """Initialize Redis connection with error handling"""
    try:
        r = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=False,
            socket_timeout=5,
            socket_connect_timeout=5,
            # retry_on_timeout=True
        )
        # Test connection
        r.ping()
        logger.info(f"Redis connection established: {config.REDIS_HOST}:{config.REDIS_PORT}")
        return r
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

def fetch_frame(camera_id: str, camera_url: str, worker_key: str, stop_event):
    """
    Enhanced frame fetching function with better error handling and monitoring
    """
    # Setup per-process logging
    process_logger = logging.getLogger(f"worker-{camera_id}")
    
    # Initialize Redis connection for this process
    try:
        r = init_redis_connection()
    except Exception as e:
        process_logger.error(f"Failed to initialize Redis in worker {camera_id}: {e}")
        return

    cap = None
    reconnect_interval = config.RECONNECT_INTERVAL
    frame_count = 0
    last_time = time()
    consecutive_failures = 0
    max_failures = config.MAX_CONSECUTIVE_FAILURES

    process_logger.info(f"Starting frame capture for camera {camera_id} from {camera_url}")

    while not stop_event.is_set():
        try:
            # Initialize or check video capture
            if cap is None or not cap.isOpened():
                process_logger.info(f"[{camera_id}] Connecting to camera...")
                cap = cv2.VideoCapture(camera_url)
                
                if not cap.isOpened():
                    consecutive_failures += 1
                    process_logger.warning(
                        f"[{camera_id}] Failed to connect to camera. "
                        f"Retrying in {reconnect_interval}s... "
                        f"(Failure {consecutive_failures}/{max_failures})"
                    )
                    
                    if consecutive_failures >= max_failures:
                        process_logger.error(f"[{camera_id}] Max failures reached. Stopping worker.")
                        break
                        
                    r.set(f'camera_{camera_id}_status', 'False')
                    sleep(reconnect_interval)
                    continue

            ret, frame = cap.read()
            if not ret:
                consecutive_failures += 1
                process_logger.warning(f"[{camera_id}] Failed to read frame. Retry {consecutive_failures}")
                
                if consecutive_failures >= max_failures:
                    process_logger.error(f"[{camera_id}] Too many frame read failures. Reconnecting...")
                    cap.release()
                    cap = None
                    consecutive_failures = 0
                    continue
                    
                r.set(f'camera_{camera_id}_status', 'False')
                sleep(1)
                continue

            # Reset failure counter on successful frame read
            consecutive_failures = 0
            frame_count += 1
            current_time = time()
            elapsed = current_time - last_time

            # Calculate and update FPS
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                r.set(f'camera_{camera_id}_fps', f"{fps:.2f}")
                process_logger.debug(f"[{camera_id}] Camera FPS: {fps:.2f}")
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

    # Use configuration from Config class
    config = Config()
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
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
