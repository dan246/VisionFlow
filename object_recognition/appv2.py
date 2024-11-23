import logging
import asyncio
import time
import datetime
import os
from tempfile import NamedTemporaryFile

import cv2
import numpy as np
import redis
from PIL import Image, ImageDraw, ImageFont
import aiohttp

# 第三方套件
import supervision as sv
from supervision.draw.color import Color
from ultralytics import YOLO

# 本地套件
from ApiService import ApiService
from image_storage import ImageStorage
from logging_config import configure_logging
from model_config import MODEL_CONFIG

class MainApp:
    def __init__(self):

        # 日誌
        configure_logging()  
        self.logger = logging.getLogger('MainApp')
        self.time_logger = logging.getLogger('TimeLogger')

        self.redis_host = 'redis'
        self.redis_port = 6379
        self.r = redis.Redis(host=self.redis_host, port=self.redis_port, db=0)
        self.image_storage = ImageStorage(self.r)

        self.init_dirs()
        self.init_models()

        self.api_service = ApiService(base_url=os.getenv("API_SERVICE_URL"))
        self.last_sent_timestamps = {}

        # 設定休眠
        self.SLEEP_INTERVAL = 0.1  

        # 初始化每個攝影機的追蹤器和標註器
        self.trackers = {}
        self.trace_annotators = {}

    def init_dirs(self):
        """初始化儲存影像的目錄"""
        start_time = time.time()
        self.BASE_SAVE_DIR = "saved_images"
        self.RAW_SAVE_DIR = os.path.join(self.BASE_SAVE_DIR, "raw_images")
        self.ANNOTATED_SAVE_DIR = os.path.join(self.BASE_SAVE_DIR, "annotated_images")
        self.STREAM_SAVE_DIR = os.path.join(self.BASE_SAVE_DIR, "stream")

        for dir_path in [
            self.RAW_SAVE_DIR,
            self.ANNOTATED_SAVE_DIR,
            self.STREAM_SAVE_DIR,
        ]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

        self.time_logger.info(
            f"Directories initialized in {time.time() - start_time:.2f} seconds"
        )

    def init_models(self):
        """初始化模型並設定標註器"""
        start_time = time.time()

        # 用於存放模型的字典
        self.models = {}      

        # 用於存放各模型的標註器
        self.annotators = {}  

        for model_name, config in MODEL_CONFIG.items():
            model_paths = config["path"]
            model_path = model_paths[0]
            self.models[model_name] = YOLO(model_path)
            self.logger.info(f"Model {model_name} loaded from {model_path}")

            annotators_config = config.get("annotators", {})
            annotators = {}

            for annotator_name, annotator_settings in annotators_config.items():
                annotator_type = annotator_settings.get("type")
                if annotator_type == "BoxAnnotator":
                    thickness = annotator_settings.get("thickness", 2)
                    color = annotator_settings.get("color", None)
                    if color:
                        annotators[annotator_name] = sv.BoxAnnotator(
                            thickness=thickness,
                            color=color
                        )
                    else:
                        annotators[annotator_name] = sv.BoxAnnotator(
                            thickness=thickness
                        )
                elif annotator_type == "RoundBoxAnnotator":
                    thickness = annotator_settings.get("thickness", 2)
                    color = annotator_settings.get("color", None)
                    if color:
                        annotators[annotator_name] = sv.RoundBoxAnnotator(
                            thickness=thickness,
                            color=color
                        )
                    else:
                        annotators[annotator_name] = sv.RoundBoxAnnotator(
                            thickness=thickness
                        )
                elif annotator_type == "LabelAnnotator":
                    text_position = annotator_settings.get("text_position", "TOP_CENTER")
                    text_thickness = annotator_settings.get("text_thickness", 2)
                    text_scale = annotator_settings.get("text_scale", 1)
                    position = getattr(sv.Position, text_position)
                    annotators[annotator_name] = sv.LabelAnnotator(
                        text_position=position,
                        text_thickness=text_thickness,
                        text_scale=text_scale
                    )
                else:
                    self.logger.warning(f"Unknown annotator type: {annotator_type}")
            self.annotators[model_name] = annotators

        self.time_logger.info(
            f"Models and annotators initialized in {time.time() - start_time:.2f} seconds"
        )

    async def fetch_camera_status(self):
        """
        從 Redis 獲取所有攝影機的狀態，使用 mget 提高效能。
        """
        start_time = time.time()
        try:
            # 透過鍵模式一次性獲取所有攝影機相關的狀態鍵
            camera_status_keys = self.r.keys("camera_*_status")
            if not camera_status_keys:
                self.logger.warning("未發現任何攝影機狀態鍵")
                return {}

            # 使用 mget 批量獲取所有狀態鍵的值
            status_values = self.r.mget(camera_status_keys)
            camera_status = {}

            for key, status in zip(camera_status_keys, status_values):
                camera_id = int(key.decode("utf-8").split("_")[1])
                status_decoded = status.decode("utf-8") if status else "False"
                # 將狀態儲存到字典
                camera_status[camera_id] = {"alive": status_decoded}

            self.logger.debug(f"從 Redis 批量獲取攝影機狀態：{camera_status}")
            self.time_logger.info(
                f"從 Redis 獲取攝影機狀態耗時 {time.time() - start_time:.2f} 秒"
            )
            return camera_status
        except Exception as e:
            self.logger.error(f"從 Redis 獲取攝影機狀態失敗：{str(e)}")
            return {}

    async def fetch_snapshot(self, session, camera_id):
        """從 Redis 中獲取指定攝影機的最新影像"""
        start_time = time.time()
        redis_key = f"camera_{camera_id}_latest_frame"
        loop = asyncio.get_event_loop()
        image = await loop.run_in_executor(None, self.image_storage.fetch_image, redis_key)
        self.time_logger.info(
            f"Snapshot for camera {camera_id} fetched in {time.time() - start_time:.2f} seconds"
        )
        return image

    async def fetch_mask(self, session, camera_id):
        """Fetches the mask for the specified camera from the mask endpoint."""
        try:
            async with session.get(f"{os.getenv('CAMERA_SERVICE_URL')}/mask/{camera_id}") as response:
                if response.status == 200:
                    mask_data = await response.read()
                    mask_array = np.frombuffer(mask_data, dtype=np.uint8)
                    mask_image = cv2.imdecode(mask_array, cv2.IMREAD_GRAYSCALE)
                    return mask_image
                else:
                    self.logger.warning(f"No mask found for camera {camera_id}. Proceeding without a mask.")
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching mask for camera {camera_id}: {str(e)}")
            return None


    async def process_camera(self, session, camera_id, camera_info, images_batches):
        img = await self.fetch_snapshot(session, camera_id)
        mask = await self.fetch_mask(session, camera_id)
        if img is not None:
            self.logger.info(f"Image from camera {camera_id} ready for processing")
            recognition_model = camera_info.get("recognition")
            if recognition_model in self.models:
                # 根據模型類型將影像和資訊添加到對應的批次
                if recognition_model not in images_batches:
                    images_batches[recognition_model] = {
                        'images': [],
                        'masks': [],
                        'camera_infos': []
                    }
                images_batches[recognition_model]['images'].append(img)
                images_batches[recognition_model]['masks'].append(mask)
                images_batches[recognition_model]['camera_infos'].append((camera_id, camera_info))
            else:
                self.logger.warning(f"No valid recognition model for camera {camera_id}")
        else:
            self.logger.warning(f"No image fetched for camera {camera_id}")


    def call_model_batch(self, model_type, batch_data):
        """使用指定的模型處理批次的影像"""
        start_time = time.time()
        notify_message = {
            "model1": "模型1檢測",
            "model2": "模型2檢測",
            "model3": "模型3檢測",
        }

        model = self.models[model_type]
        model_config = MODEL_CONFIG[model_type]

        images_batch = batch_data['images']
        masks_batch = batch_data['masks']
        camera_infos_batch = batch_data['camera_infos']

        # 模型批次推理
        results = model.predict(images_batch, conf=model_config["conf"])

        for i, detections in enumerate(results):
            image = images_batch[i]
            mask = masks_batch[i]
            camera_id, camera_info = camera_infos_batch[i]

            # 獲取特定標籤和置信度
            label_conf = model_config.get("label_conf", {})
            target_labels = label_conf.keys()

            if not detections.boxes:
                self.logger.warning(f"No detections found for camera {camera_id}")
                continue

            # 標註圖像
            annotated_image, detection_flag, label = self.annotate_image(
                image, detections, mask, model.names, camera_info, model_type
            )

            # 儲存影像並發送通知
            timestamp = time.time()
            self.save_and_notify(
                camera_id,
                annotated_image,
                timestamp,
                camera_info,
                model_type,
                notify_message,
                detection_flag=detection_flag,
                label=label,
            )

        self.time_logger.info(
            f"Batch model {model_type} processing completed in {time.time() - start_time:.2f} seconds"
        )


    def annotate_image(self, image, detections, mask, model_names, camera_info, model_name):
        """
        對影像進行標註，並根據遮罩篩選符合的區域。

        :param image: 原始影像 (np.ndarray)
        :param detections: YOLO 模型的檢測結果
        :param mask: 遮罩影像 (np.ndarray)，若為 None，將處理整張圖像
        :param model_names: 模型的標籤名稱列表
        :param camera_info: 攝影機的額外資訊
        :param model_name: 模型名稱
        :return: 標註後的影像 (np.ndarray)，是否檢測到目標 (bool)，檢測到的標籤名稱 (str)
        """
        annotated_image = image.copy()

        # 確保檢測結果有效
        if detections.boxes is None or len(detections.boxes) == 0:
            self.logger.warning("No detections found to annotate.")
            return annotated_image, False, ""

        # 提取檢測結果
        boxes = detections.boxes.xyxy.cpu().numpy()
        confidences = detections.boxes.conf.cpu().numpy()
        class_ids = detections.boxes.cls.cpu().numpy().astype(int)

        detection_flag = False
        detected_labels = []

        for i, (box, conf, cls_id) in enumerate(zip(boxes, confidences, class_ids)):
            label = model_names[int(cls_id)]
            detected_labels.append(f"{label} {conf:.2f}")

            x1, y1, x2, y2 = map(int, box)

            # 如果提供了遮罩，檢查目標是否在遮罩範圍內
            if mask is not None:
                # 檢查是否為全黑遮罩
                if np.sum(mask) == 0:
                    self.logger.debug("Mask is completely black. Processing the entire image as if no mask is set.")
                    mask = None  # 將 mask 設為 None，後續直接處理整張圖片
                else:
                    mask_crop = mask[y1:y2, x1:x2]
                    if mask_crop.size == 0 or np.sum(mask_crop == 255) / mask_crop.size < 0.5:
                        self.logger.debug(f"Detection {label} skipped due to mask filtering.")
                        continue  # 跳過這個檢測框，但繼續處理下一個檢測框
            else:
                self.logger.debug("Mask is None. Processing the entire image.")

            # 繪製邊框
            color = (0, 255, 0)  # 預設綠色
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)

            # 繪製標籤
            label_text = f"{label} {conf:.2f}"
            cv2.putText(
                annotated_image,
                label_text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

            self.logger.info(f"Annotated: {label} at [{x1}, {y1}, {x2}, {y2}] with confidence {conf:.2f}")

            # 如果有檢測結果，設置標誌
            detection_flag = True

        # 保存帶框的圖像（DEBUG用）
        debug_folder = os.path.join(self.BASE_SAVE_DIR, "debug_images")
        os.makedirs(debug_folder, exist_ok=True)
        debug_image_path = os.path.join(debug_folder, f"{camera_info['id']}_annotated.jpg")
        cv2.imwrite(debug_image_path, annotated_image)
        self.logger.info(f"Annotated debug image saved at {debug_image_path}")

        # 返回標註結果
        return annotated_image, detection_flag, ", ".join(detected_labels)

    def save_and_notify(
        self,
        camera_id,
        annotated_image,
        timestamp,
        camera_info,
        model_type,
        notify_message,
        detection_flag,
        label,
    ):
        """儲存標註影像並發送通知"""
        start_time = time.time()
        annotated_img_path = os.path.join(
            self.ANNOTATED_SAVE_DIR, f"{camera_id}_{timestamp}.jpg"
        )
        cv2.imwrite(annotated_img_path, annotated_image)
        self.logger.info(f"Annotated image saved to {annotated_img_path}")

        stream_img_path = os.path.join(self.STREAM_SAVE_DIR, f"{camera_id}.jpg")
        cv2.imwrite(
            stream_img_path, annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 70]
        )
        self.logger.info(
            f"Latest image (with or without annotations) saved to {stream_img_path} for camera {camera_id}"
        )
        redis_key = f"camera_{camera_id}_boxed_image"
        self.image_storage.save_image(redis_key, annotated_image)

        self.time_logger.info(
            f"Save and notify completed in {time.time() - start_time:.2f} seconds"
        )

    async def main_loop(self):
        async with aiohttp.ClientSession() as session:
            while True:
                start_time = time.time()
                self.logger.info("檢查攝影機狀態...")

                # 獲取攝影機列表
                camera_list = self.api_service.get_camera_list()
                if not camera_list:
                    self.logger.warning("未發現任何攝影機")
                    await asyncio.sleep(self.SLEEP_INTERVAL)
                    continue

                # 將 camera_list 轉換為字典格式
                camera_list_by_id = {int(camera["id"]): camera for camera in camera_list}

                camera_status = await self.fetch_camera_status()
                if not camera_status:
                    self.logger.warning("Redis 中未發現任何攝影機狀態")
                    await asyncio.sleep(self.SLEEP_INTERVAL)
                    continue

                # 初始化批次字典
                images_batches = {}

                # 為每台攝影機創建處理任務
                tasks = []
                for camera_id, status in camera_status.items():
                    if status["alive"] == "True":
                        camera_info = camera_list_by_id.get(camera_id)  # 使用轉換後的字典進行查詢
                        if camera_info:
                            tasks.append(self.process_camera(session, camera_id, camera_info, images_batches))

                if tasks:
                    # 非同步執行所有攝影機的處理任務
                    await asyncio.gather(*tasks)

                    # 所有影像收集完畢，對每個模型類型進行批次推理
                    for model_type, batch_data in images_batches.items():
                        self.call_model_batch(model_type, batch_data)
                else:
                    self.logger.warning("無需處理的攝影機")

                # 動態調整休眠時間
                elapsed_time = time.time() - start_time
                adjusted_sleep = max(0, self.SLEEP_INTERVAL - elapsed_time)
                await asyncio.sleep(adjusted_sleep)

                self.time_logger.info(
                    f"處理完成，耗時 {time.time() - start_time:.2f} 秒"
                )


    # async def main_loop(self):
    #     async with aiohttp.ClientSession() as session:
    #         while True:
    #             start_time = time.time()
    #             self.logger.info("檢查攝影機狀態...")

    #             # 獲取攝影機列表
    #             camera_list = self.api_service.get_camera_list()
    #             if not camera_list:
    #                 self.logger.warning("未發現任何攝影機")
    #                 await asyncio.sleep(self.SLEEP_INTERVAL)
    #                 continue

    #             # 將 camera_list 轉換為字典格式
    #             camera_list_by_id = {int(camera["id"]): camera for camera in camera_list}

    #             camera_status = await self.fetch_camera_status()
    #             if not camera_status:
    #                 self.logger.warning("Redis 中未發現任何攝影機狀態")
    #                 await asyncio.sleep(self.SLEEP_INTERVAL)
    #                 continue

    #             # 初始化批次列表
    #             images_batch = []
    #             masks_batch = []
    #             camera_infos_batch = []

    #             # 為每台攝影機創建處理任務
    #             tasks = []
    #             for camera_id, status in camera_status.items():
    #                 if status["alive"] == "True":
    #                     camera_info = camera_list_by_id.get(camera_id)  # 使用轉換後的字典進行查詢
    #                     if camera_info:
    #                         tasks.append(self.process_camera(session, camera_id, camera_info, None, images_batch, masks_batch, camera_infos_batch))

    #             if tasks:
    #                 # 非同步執行所有攝影機的處理任務
    #                 await asyncio.gather(*tasks)

    #                 # 所有影像收集完畢，進行批次推理
    #                 if images_batch:
    #                     self.call_model_batch(images_batch, masks_batch, camera_infos_batch)
    #                 else:
    #                     self.logger.warning("沒有需要處理的影像")
    #             else:
    #                 self.logger.warning("無需處理的攝影機")

    #             # 動態調整休眠時間
    #             elapsed_time = time.time() - start_time
    #             adjusted_sleep = max(0, self.SLEEP_INTERVAL - elapsed_time)
    #             await asyncio.sleep(adjusted_sleep)

    #             self.time_logger.info(
    #                 f"處理完成，耗時 {time.time() - start_time:.2f} 秒"
    #             )

if __name__ == "__main__":
    app = MainApp()
    asyncio.run(app.main_loop())
