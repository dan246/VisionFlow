import asyncio
import datetime
import logging
import os
import time

import aiohttp
import cv2
import numpy as np
import redis
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Point, Polygon
from ultralytics import YOLO
from ApiService import ApiService  # 您原本的 API 服務，如同範例
from image_storage import ImageStorage
from logging_config import configure_logging
from model_config import MODEL_CONFIG  # 您的模型設定
# from your_notification_module import send_notification # 假設未來要通知，可以再 import

class MainApp:
    def __init__(self):
        configure_logging()
        self.logger = logging.getLogger('SideProjectApp')
        self.time_logger = logging.getLogger('TimeLogger')

        # 初始化 Redis
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.r = redis.Redis(host=self.redis_host, port=self.redis_port, db=0)

        self.image_storage = ImageStorage(self.r)
        self.api_service = ApiService(base_url=os.getenv("API_SERVICE_URL", "http://backend:5000"))

        # 讀取模型：若您已有自己的 models 初始化邏輯，也可與公司專案分開
        self.models = {}
        self.load_models_from_config()

        # 時間區段事件狀態管理 (Inside/Outside)
        self.event_states = {}

        # 紀錄最後一次發報時間，避免過度觸發
        self.last_sent_timestamps = {}

        # 是否進入 Debug Mode
        self.debug_mode = os.getenv("DEBUG_MODE", "True").lower() in ('true', '1', 't')

        # 主迴圈每次執行後休息秒數
        self.SLEEP_INTERVAL = 2.0

        # 初始化目錄
        self.init_dirs()

    def init_dirs(self):
        """
        初始化所需目錄
        """
        start_time = time.time()
        self.BASE_SAVE_DIR = "saved_images"
        self.ANNOTATED_SAVE_DIR = os.path.join(self.BASE_SAVE_DIR, "annotated_images")

        os.makedirs(self.ANNOTATED_SAVE_DIR, exist_ok=True)

        if self.debug_mode:
            self.DEBUG_SAVE_DIR = os.path.join(self.BASE_SAVE_DIR, "debug_images")
            os.makedirs(self.DEBUG_SAVE_DIR, exist_ok=True)
            self.logger.info("Debug 模式已啟用，將會儲存除錯圖")
        else:
            self.logger.info("Debug 模式未啟用")
        self.time_logger.info(f"目錄初始化完成，耗時 {time.time() - start_time:.2f} 秒")

    def load_models_from_config(self):
        """
        依據 model_config.py 載入模型
        """
        start_time = time.time()
        for model_name, config in MODEL_CONFIG.items():
            model_paths = config["path"]
            # 假設只用第一個路徑
            model_path = model_paths[0]

            self.models[model_name] = YOLO(model_path)
            self.logger.info(f"載入模型 {model_name} 從 {model_path}")

        self.time_logger.info(f"模型載入完成，耗時 {time.time() - start_time:.2f} 秒")

    async def fetch_camera_status(self):
        """
        從 Redis 獲取所有攝影機的狀態 (alive / 非 alive)。
        狀態鍵命名格式：camera_{id}_status
        """
        try:
            keys = self.r.keys("camera_*_status")
            if not keys:
                self.logger.warning("Redis 中未發現任何攝影機狀態鍵")
                return {}

            status_values = self.r.mget(keys)
            camera_status = {}

            for k, v in zip(keys, status_values):
                cam_id = k.decode("utf-8").split("_")[1]
                alive_str = v.decode("utf-8") if v else "False"
                camera_status[int(cam_id)] = alive_str
            return camera_status
        except Exception as e:
            self.logger.error(f"fetch_camera_status 時發生錯誤: {e}")
            return {}

    async def fetch_snapshot(self, camera_id):
        """
        從 Redis 取最新的攝影機影像
        """
        redis_key = f"camera_{camera_id}_latest_frame"
        image = self.image_storage.fetch_image(redis_key)
        if image is None:
            self.logger.debug(f"無法獲取攝影機 {camera_id} 的影像")
        return image

    async def fetch_time_interval(self, session, camera_id):
        """
        從後台或其他服務獲取指定攝影機的時段
        - 假設後台有 GET /time_intervals/<camera_id> 取得 { start_time: "HH:MM", end_time: "HH:MM" }
        """
        try:
            base_url = os.getenv("CAMERA_SERVICE_URL", "http://camera_ctrl:5000")
            async with session.get(f"{base_url}/time_intervals/{camera_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    start_t = data.get("start_time", "00:00")
                    end_t = data.get("end_time", "23:59")
                    return start_t, end_t
                else:
                    self.logger.warning(f"無法取得攝影機 {camera_id} 的時段，預設全天有效")
                    return "00:00", "23:59"
        except Exception as e:
            self.logger.error(f"fetch_time_interval 發生錯誤: {e}")
            return "00:00", "23:59"

    async def fetch_mask(self, session, camera_id):
        """
        從後台獲取 mask 圖與多邊形資訊
        - 假設後端 GET /mask/<camera_id> 回傳:
            {
              "image_url": "http://xxx/mask.jpg",
              "polygons_info": [
                  {"name": "zoneA", "points": [[x1,y1], [x2,y2], ...], "duration": 3},
                  ...
              ]
            }
        """
        try:
            base_url = os.getenv("CAMERA_SERVICE_URL", "http://camera_ctrl:5000")
            async with session.get(f"{base_url}/mask/{camera_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    image_url = data.get("image_url")
                    polygons_info = data.get("polygons_info", [])

                    # 下載 mask 圖片
                    if image_url:
                        async with session.get(image_url) as img_resp:
                            if img_resp.status == 200:
                                mask_data = await img_resp.read()
                                mask_array = np.frombuffer(mask_data, dtype=np.uint8)
                                mask_image = cv2.imdecode(mask_array, cv2.IMREAD_GRAYSCALE)
                                return mask_image, polygons_info
                            else:
                                self.logger.warning(f"無法下載 mask 圖：{image_url}")
                    return None, polygons_info
                else:
                    self.logger.warning(f"未獲得攝影機 {camera_id} 的 mask 資訊，HTTP {resp.status}")
                    return None, []
        except Exception as e:
            self.logger.error(f"fetch_mask 時發生錯誤: {e}")
            return None, []

    def event_detection_logic(
        self, 
        camera_id, 
        annotated_image, 
        detections, 
        polygons_info, 
        mask=None,
        overlap_threshold=0.5  # 設定遮罩重疊比例門檻為 50%
    ):
        """
        1. 用 YOLO 的結果 detections (boxes/conf/classes)
        2. 逐一檢查 bounding box 在 mask 內的「白像素佔比」
        - 若小於 overlap_threshold，就跳過
        3. 繪製框 & 進行後續狀態機判斷
        """
        if detections.boxes is None or len(detections.boxes) == 0:
            self.logger.debug("無檢測結果")
            return annotated_image

        boxes = detections.boxes.xyxy.cpu().numpy()
        confs = detections.boxes.conf.cpu().numpy()
        classes = detections.boxes.cls.cpu().numpy()
        model_names = detections.names

        final_boxes = []
        final_confs = []
        final_classes = []

        for (box, conf, cls_id) in zip(boxes, confs, classes):
            x1, y1, x2, y2 = map(int, box)

            # ------ (A) 先檢查是否超出畫面範圍 ------
            if x1 < 0: x1 = 0
            if y1 < 0: y1 = 0
            if x2 > annotated_image.shape[1]: x2 = annotated_image.shape[1]
            if y2 > annotated_image.shape[0]: y2 = annotated_image.shape[0]
            w = x2 - x1
            h = y2 - y1
            if w <= 0 or h <= 0:
                continue

            # ------ (B) 如果有 mask，計算 overlap ratio ------
            if mask is not None and np.any(mask):
                # 裁切 mask 區
                mask_crop = mask[y1:y2, x1:x2]
                box_area = w * h
                white_pixels = np.count_nonzero(mask_crop)  # >0 的像素數量
                overlap_ratio = white_pixels / float(box_area)

                if overlap_ratio < overlap_threshold:
                    # 若白色(有效區域)佔比太小，就跳過
                    self.logger.debug(
                        f"Box[{x1},{y1},{x2},{y2}] 與 mask overlap 比例 {overlap_ratio:.2f} < 門檻 {overlap_threshold}, 跳過"
                    )
                    continue

            # ------ (C) 若通過檢查，就收集此框 ------
            final_boxes.append((x1, y1, x2, y2))
            final_confs.append(conf)
            final_classes.append(cls_id)

        # ------ 後續再繪製 final_boxes 與做多邊形(Inside/Outside) ------
        detected_events = []
        for (x1, y1, x2, y2), conf, cls_id in zip(final_boxes, final_confs, final_classes):
            # 取得類別名稱
            if isinstance(model_names, dict):
                class_name = model_names.get(int(cls_id), "Unknown")
            else:
                class_name = model_names[int(cls_id)]

            # 繪製
            color = (0, 0, 255)
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)
            label_text = f"{class_name} {conf:.2f}"
            cv2.putText(
                annotated_image,
                label_text,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )

            # 計算多邊形 matched
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            center_pt = Point(cx, cy)

            matched_polygons = []
            max_duration = 0
            for poly_info in polygons_info:
                polygon = Polygon(poly_info["points"])
                if polygon.contains(center_pt):
                    matched_polygons.append(poly_info["name"])
                    duration_val = poly_info.get("duration", 0)
                    max_duration = max(max_duration, duration_val)

            event_obj = {
                "camera_id": camera_id,
                "event_type": class_name,
                "score": conf,
                "box_coords": (x1, y1, x2, y2),
                "matched_polygons": matched_polygons,
                "required_duration": max_duration
            }
            detected_events.append(event_obj)

        # 狀態機
        self.state_machine(camera_id, detected_events, annotated_image)

        return annotated_image

    def state_machine(self, camera_id, detected_events, annotated_image):
        """
        Inside/Outside 狀態機示範
        """
        current_time = time.time()

        current_map = {}
        for ev in detected_events:
            event_type = ev["event_type"]
            polygons_joined = ",".join(ev["matched_polygons"]) if ev["matched_polygons"] else ""
            key = (camera_id, event_type, polygons_joined)
            current_map[key] = {
                "inside": True,
                "required_duration": ev["required_duration"],
                "score": ev["score"]
            }

        all_keys = set(self.event_states.keys()).union(current_map.keys())
        for k in all_keys:
            if k not in current_map:
                if k in self.event_states:
                    prev_required = self.event_states[k]["required_duration"]
                    prev_score = self.event_states[k].get("score", 0)
                    current_map[k] = {
                        "inside": False,
                        "required_duration": prev_required,
                        "score": prev_score
                    }

        for key, curr_info in current_map.items():
            inside = curr_info["inside"]
            required_duration = curr_info["required_duration"]
            score = curr_info["score"]

            if key not in self.event_states:
                self.event_states[key] = {
                    "state": "inside" if inside else "outside",
                    "start_timestamp": current_time,
                    "required_duration": required_duration,
                    "fired": False,
                    "score": score
                }
            else:
                prev_state = self.event_states[key]["state"]
                prev_fired = self.event_states[key]["fired"]
                start_timestamp = self.event_states[key]["start_timestamp"]

                if inside and prev_state == "outside":
                    self.event_states[key]["state"] = "inside"
                    self.event_states[key]["start_timestamp"] = current_time
                    self.event_states[key]["fired"] = False
                    self.event_states[key]["score"] = score
                elif (not inside) and prev_state == "inside":
                    self.event_states[key]["state"] = "outside"
                    self.event_states[key]["start_timestamp"] = current_time
                    self.event_states[key]["fired"] = False
                    self.event_states[key]["score"] = score
                else:
                    elapsed = current_time - start_timestamp
                    elapsed_minutes = int(elapsed // 60)
                    if elapsed_minutes >= required_duration and (not prev_fired):
                        stable_state = "Inside" if inside else "Outside"
                        event_type = key[1]
                        polygons_str = key[2]
                        msg = f"Camera {camera_id} 事件: {event_type}, 區域: {polygons_str}, 狀態: {stable_state}, 持續 {elapsed_minutes} 分"
                        self.logger.info(f"==== 發報: {msg}")
                        self.event_states[key]["fired"] = True

    async def main_loop(self):
        """
        主迴圈：批次處理不同模型、不同攝影機
        """
        async with aiohttp.ClientSession() as session:
            while True:
                start_loop_time = time.time()

                camera_list = self.api_service.get_camera_list()
                camera_list_by_id = {int(c["id"]): c for c in camera_list} if camera_list else {}
                camera_status = await self.fetch_camera_status()
                if not camera_status:
                    self.logger.warning("Redis 中未發現攝影機狀態，進入休眠")
                    await asyncio.sleep(self.SLEEP_INTERVAL)
                    continue

                model_batches = {}
                for cam_id, alive_str in camera_status.items():
                    if alive_str != "True":
                        continue

                    camera_info = camera_list_by_id.get(cam_id)
                    if not camera_info:
                        continue

                    start_t, end_t = await self.fetch_time_interval(session, cam_id)
                    now_hm = datetime.datetime.now().strftime("%H:%M")
                    if not (start_t <= now_hm <= end_t):
                        continue

                    mask, polygons_info = await self.fetch_mask(session, cam_id)
                    frame = await self.fetch_snapshot(cam_id)
                    if frame is None:
                        continue

                    # 🔴這裡的bitwise_and只是把外面弄成黑，但有時仍會偵測到誤框
                    # 我們會在event_detection_logic再做一次檢查
                    if mask is not None and np.any(mask):
                        frame = cv2.bitwise_and(frame, frame, mask=mask)

                    model_name = camera_info.get("recognition", "model1")
                    if model_name not in self.models:
                        self.logger.warning(f"攝影機 {cam_id} 指定的模型 {model_name} 不存在")
                        continue

                    if model_name not in model_batches:
                        model_batches[model_name] = []
                    model_batches[model_name].append((cam_id, polygons_info, frame, mask))

                for model_name, cam_items in model_batches.items():
                    if not cam_items:
                        continue

                    model = self.models.get(model_name)
                    if not model:
                        self.logger.warning(f"在 model_batches 中找不到已載入的模型 {model_name}")
                        continue

                    frames_to_predict = [item[2] for item in cam_items]  # (cam_id, polygons_info, frame, mask)
                    results = model.predict(frames_to_predict)

                    for i, det_result in enumerate(results):
                        cam_id, polygons_info, original_frame, mask = cam_items[i]
                        annotated = self.event_detection_logic(
                            camera_id=cam_id,
                            annotated_image=original_frame.copy(),
                            detections=det_result,
                            polygons_info=polygons_info,
                            mask=mask   # 🔴 傳給event_detection_logic做中心點檢查
                        )

                        if self.debug_mode:
                            debug_path = os.path.join(self.DEBUG_SAVE_DIR, f"{model_name}_cam_{cam_id}_{int(time.time())}.jpg")
                            cv2.imwrite(debug_path, annotated)
                            self.logger.info(f"Batch Debug: 已存除錯圖 {debug_path}")

                        redis_key_annotated = f"camera_{cam_id}_boxed_image"
                        self.image_storage.save_image(redis_key_annotated, annotated)
                        self.logger.debug(f"已將攝影機 {cam_id} 的標註影像存至 Redis (batch) key={redis_key_annotated}")

                elapsed = time.time() - start_loop_time
                if elapsed < self.SLEEP_INTERVAL:
                    await asyncio.sleep(self.SLEEP_INTERVAL - elapsed)

    def run(self):
        asyncio.run(self.main_loop())


if __name__ == "__main__":
    app = MainApp()
    app.run()
