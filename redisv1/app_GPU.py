import os
import redis
import cv2
import threading
import subprocess
import numpy as np
import time
from time import sleep, localtime, strftime

# 初始化 Redis 連線
redis_host = 'redis'
redis_port = 6379
r = redis.Redis(host=redis_host, port=redis_port, db=0)

camera_threads = {}  # 用來存放 camera_id 與對應的執行控制
camera_threads_lock = threading.Lock()  # 用於保護 camera_threads 的線程鎖

def get_camera_resolution_ffmpeg(camera_id, camera_url, resolution_event, resolution_data, stop_event, max_retries=3):
    """
    使用 FFmpeg 取得攝影機的解析度，在獲取後通知主線程。
    """
    retry_count = 0
    while retry_count < max_retries and not stop_event.is_set():
        try:
            # FFmpeg 命令，用來取得解析度
            ffmpeg_cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height', '-of', 'csv=p=0',
                camera_url
            ]
            # 執行命令並獲取解析度輸出
            result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            resolution = result.stdout.strip()
            
            if resolution:
                width, height = map(int, resolution.split(','))
                print(f"[{camera_id}] 解析度檢測：{width}x{height} for {camera_url}")
                resolution_data['width'] = width
                resolution_data['height'] = height
                resolution_event.set()  # 通知解析度已取得
                return
            else:
                print(f"[{camera_id}] 解析度檢測失敗，無法取得輸出：重試 {retry_count + 1}/{max_retries}")
        except Exception as e:
            print(f"[{camera_id}] 解析度取得失敗 ({retry_count + 1}/{max_retries}): {e}")
        
        retry_count += 1
        sleep(2)  # 每次重試間隔
        
    # 重試次數達到上限，設定狀態為 False
    print(f"[{camera_id}] 無法取得攝影機解析度，請檢查連接設定。")
    r.set(f'camera_{camera_id}_status', 'False')
    resolution_event.set()  # 即使失敗也需要設定事件，避免主線程一直等待

def fetch_frame(camera_id, camera_url, stop_event, width, height, max_retries=3):
    """
    使用 FFmpeg 獲取影像幀，若達到最大重試次數則切換到 OpenCV。
    """
    try:
        retry_count = 0
        frame_size = width * height * 3  # 根據像素格式調整

        while not stop_event.is_set():
            ffmpeg_cmd = [
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-loglevel', 'error',
                'timeout','1000000',
                '-flags','low_delay',
                '-fflags','nobuffer',
                '-i', camera_url,
                '-vf', 'fps=1',
                '-f', 'rawvideo',
                '-pix_fmt', 'bgr24',  # 使用 'bgr24' 格式
                'pipe:'
            ]

            try:
                process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"[{camera_id}] [GPU] 嘗試使用 FFmpeg 連接到攝影機。")
                print(f"[{camera_id}] [GPU] 成功連接")
            except Exception as e:
                print(f"[{camera_id}] [GPU] 無法啟動 FFmpeg 進程: {e}")
                retry_count += 1
                sleep(2)
                continue

            stderr_thread = threading.Thread(target=read_stderr, args=(camera_id, process.stderr))
            
            stderr_thread.start()

            while not stop_event.is_set():
                try:
                    raw_frame = process.stdout.read(frame_size)
                    if not raw_frame:
                        print(f"[{camera_id}] [GPU] 無法從 FFmpeg 讀取影像幀，可能連線中斷。")
                        retry_count += 1
                        if retry_count >= max_retries:
                            print(f"[{camera_id}] [GPU] 已達到最大重試次數。切換到使用 OpenCV。")
                            process.terminate()
                            process.wait()
                            # 呼叫 OpenCV 方法
                            fetch_frame_opencv(camera_id, camera_url, stop_event)
                            return
                        break

                    retry_count = 0  # 成功讀取影像後重置重試次數
                    
                    frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
                    
                    # 保存最新影像
                    current_time = time.time()
                    timestamp_str = strftime("%Y%m%d%H%M%S", localtime(current_time + 8 * 3600))
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_data = buffer.tobytes()
                    r.set(f'camera_{camera_id}_latest_frame', image_data)
                    r.set(f'camera_{camera_id}_status', 'True')
                    r.set(f'camera_{camera_id}_last_timestamp', timestamp_str)
                    r.set(f'camera_{camera_id}_url', camera_url)

                except Exception as e:
                    print(f"[{camera_id}] [GPU] 出現錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"[{camera_id}] [GPU] 已達到最大重試次數。切換到使用 OpenCV。")
                        process.terminate()
                        process.wait()
                        # 呼叫 OpenCV 方法
                        fetch_frame_opencv(camera_id, camera_url, stop_event)
                        return
                    break

            if process:
                process.terminate()
                process.wait()
                print(f"[{camera_id}] [GPU] 停止獲取影像幀。")

    except Exception as e:
        print(f"[{camera_id}] [GPU] 未處理的異常: {e}")
        import traceback
        traceback.print_exc()
        stop_event.set()

def fetch_frame_opencv(camera_id, camera_url, stop_event):
    """
    使用 OpenCV 直接從攝影機讀取影像。
    """
    print(f"[{camera_id}] [CPU] 使用 OpenCV 連接到攝影機。")
    cap = cv2.VideoCapture(camera_url)

    if not cap.isOpened():
        print(f"[{camera_id}] [CPU] 無法使用 OpenCV 打開攝影機。")
        r.set(f'camera_{camera_id}_status', 'False')
        return

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print(f"[{camera_id}] [CPU] 使用 OpenCV 讀取影像失敗，嘗試重新連接。")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(camera_url)
            if not cap.isOpened():
                print(f"[{camera_id}] [CPU] 無法重新連接攝影機。")
                r.set(f'camera_{camera_id}_status', 'False')
                stop_event.set()
                break
            continue

        # 保存最新影像
        current_time = time.time()
        timestamp_str = strftime("%Y%m%d%H%M%S", localtime(current_time + 8 * 3600))
        _, buffer = cv2.imencode('.jpg', frame)
        image_data = buffer.tobytes()
        r.set(f'camera_{camera_id}_latest_frame', image_data)
        r.set(f'camera_{camera_id}_status', 'True')
        r.set(f'camera_{camera_id}_last_timestamp', timestamp_str)
        r.set(f'camera_{camera_id}_url', camera_url)

    cap.release()
    print(f"[{camera_id}] [CPU] 停止使用 OpenCV 獲取影像。")

def read_stderr(camera_id, stderr_pipe):
    """
    持續讀取 FFmpeg 的錯誤輸出並打印。
    """
    for line in iter(stderr_pipe.readline, b''):
        print(f"[{camera_id}] [GPU] FFmpeg 錯誤輸出：{line.decode('utf-8').strip()}")

def get_resolution_and_start_fetching(camera_id, camera_url, stop_event):
    """
    獲取攝影機解析度並開始獲取影像。
    """
    try:
        # 如果 stop_event 已被設置，則清除它
        if stop_event.is_set():
            stop_event.clear()
        resolution_event = threading.Event()
        resolution_data = {}
        # 啟動取得解析度的線程
        resolution_thread = threading.Thread(
            target=get_camera_resolution_ffmpeg,
            args=(camera_id, camera_url, resolution_event, resolution_data, stop_event)
        )
        resolution_thread.start()
        # 等待解析度取得或停止事件
        while not resolution_event.is_set() and not stop_event.is_set():
            time.sleep(0.1)
        # 如果成功獲取解析度，啟動影像獲取線程
        if 'width' in resolution_data and 'height' in resolution_data:
            width = resolution_data['width']
            height = resolution_data['height']
            fetch_thread = threading.Thread(
                target=fetch_frame,
                args=(camera_id, camera_url, stop_event, width, height)
            )
            fetch_thread.start()
            with camera_threads_lock:
                camera_threads[camera_id]['fetch_thread'] = fetch_thread
            fetch_thread.join()
        else:
            print(f"[{camera_id}] 無法取得解析度，改用 OpenCV 直接連接。")
            # 呼叫 OpenCV 方法
            fetch_frame_opencv(camera_id, camera_url, stop_event)
    except Exception as e:
        print(f"[{camera_id}] 在取得解析度時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        # 呼叫 OpenCV 方法
        fetch_frame_opencv(camera_id, camera_url, stop_event)

def manage_camera_threads(current_camera_data):
    """
    管理攝影機線程，啟動新攝影機、停止已移除的攝影機，以及處理 URL 變更的情況。
    """
    global camera_threads

    with camera_threads_lock:
        existing_camera_ids = set(camera_threads.keys())
        new_camera_ids = set(current_camera_data.keys())

        # 找出需要停止的攝影機（在舊清單中，但不在新清單中）
        cameras_to_stop = existing_camera_ids - new_camera_ids
        # 找出需要啟動的攝影機（在新清單中，但不在舊清單中）
        cameras_to_start = new_camera_ids - existing_camera_ids

        # 停止不再需要的攝影機線程
        for camera_id in cameras_to_stop:
            stop_event = camera_threads[camera_id]['stop_event']
            stop_event.set()
            del camera_threads[camera_id]
            print(f"[{camera_id}] Camera thread stopped.")

        # 處理 URL 更新或啟動新的攝影機線程
        for camera_id in new_camera_ids.union(existing_camera_ids):
            new_url = current_camera_data.get(camera_id)
            if camera_id in camera_threads:
                old_url = camera_threads[camera_id]['camera_url']
                # 檢查 URL 是否發生變化
                if new_url != old_url:
                    print(f"[{camera_id}] URL 發生變化，重新啟動攝影機線程。")
                    stop_event = camera_threads[camera_id]['stop_event']
                    stop_event.set()  # 停止舊線程
                    del camera_threads[camera_id]

                    # 啟動新的線程
                    stop_event = threading.Event()
                    camera_thread = threading.Thread(
                        target=get_resolution_and_start_fetching,
                        args=(camera_id, new_url, stop_event)
                    )
                    camera_thread.start()
                    camera_threads[camera_id] = {
                        'thread': camera_thread,
                        'stop_event': stop_event,
                        'camera_url': new_url,
                        'retry_count': 0
                    }
                    print(f"[{camera_id}] Camera thread restarted with new URL.")
            else:
                # 啟動新的攝影機線程
                print(f"[{camera_id}] 啟動新的攝影機線程。")
                stop_event = threading.Event()
                camera_thread = threading.Thread(
                    target=get_resolution_and_start_fetching,
                    args=(camera_id, new_url, stop_event)
                )
                camera_thread.start()
                camera_threads[camera_id] = {
                    'thread': camera_thread,
                    'stop_event': stop_event,
                    'camera_url': new_url,
                    'retry_count': 0
                }
                print(f"[{camera_id}] Camera thread started.")

def monitor_cameras():
    """
    監控攝影機清單的更新，並管理攝影機線程。
    """
    worker_id = os.getenv('WORKER_ID')
    if worker_id is None:
        raise ValueError("WORKER_ID 環境變數未設定。")
    else:
        print(f"WORKER_ID: {worker_id}")

    worker_key = f'worker_{worker_id}_urls'
    pubsub = r.pubsub()
    pubsub.subscribe(f'{worker_key}_update')

    print(f"Monitoring updates for worker {worker_id}.")
    camera_data = get_camera_data(worker_key)
    manage_camera_threads(camera_data)

    last_camera_data = camera_data.copy()  # 記錄最後一次的攝影機清單

    while True:
        # 設置消息超時，避免阻塞主程序
        message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1)

        if message:
            # 無論收到什麼訊息，都重新獲取攝影機清單，並比較是否有變化
            current_camera_data = get_camera_data(worker_key)
            if current_camera_data != last_camera_data:
                print("Detected update event. Refreshing camera list.")
                manage_camera_threads(current_camera_data)
                last_camera_data = current_camera_data.copy()
            else:
                # 攝影機清單沒有變化，不進行任何操作
                pass

        # 加入短暫等待，防止進程過度佔用
        time.sleep(0.5)

def get_camera_data(worker_key):
    """
    從 Redis 中獲取攝影機 URL 清單。
    """
    camera_urls = r.smembers(worker_key)
    camera_data = {}

    for url in camera_urls:
        url_parts = url.decode('utf-8').split('|')
        camera_id, camera_url = url_parts[0], url_parts[1]
        camera_data[camera_id] = camera_url

    return camera_data

def monitor_camera_threads():
    """
    監控攝影機線程，嘗試重新啟動已停止的線程。
    """
    while True:
        with camera_threads_lock:
            for camera_id, thread_info in list(camera_threads.items()):
                thread = thread_info['thread']
                stop_event = thread_info['stop_event']

                if not thread.is_alive():
                    print(f"[{camera_id}] 線程已停止。嘗試重新啟動。")
                    # 清除停止事件
                    stop_event.clear()
                    # 創建新的線程
                    new_thread = threading.Thread(
                        target=get_resolution_and_start_fetching,
                        args=(camera_id, thread_info['camera_url'], stop_event)
                    )
                    new_thread.start()
                    camera_threads[camera_id]['thread'] = new_thread
        time.sleep(5)  # 每隔 5 秒檢查一次

if __name__ == "__main__":
    threading.Thread(target=monitor_camera_threads, daemon=True).start()
    monitor_cameras()
