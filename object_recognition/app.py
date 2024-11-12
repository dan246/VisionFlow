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

    async def fetch_camera_status(self, session):
        """從 API 獲取攝影機狀態"""
        start_time = time.time()
        try:
            async with session.get(
                f"{os.getenv('CAMERA_SERVICE_URL')}/camera_status"
            ) as response:
                if response.status == 200:
                    camera_status = await response.json()
                    self.logger.debug(f"Fetched camera_status: {camera_status}")
                    return camera_status
                else:
                    self.logger.error(
                        f"Failed to fetch camera status, HTTP status: {response.status}"
                    )
                    return {}
        except Exception as e:
            self.logger.error(f"Error fetching camera status: {str(e)}")
            return {}

    async def fetch_mask(self, session, camera_id):
        """從 API 獲取指定攝影機的遮罩資料"""
        start_time = time.time()
        try:
            async with session.get(
                f"{os.getenv('CAMERA_SERVICE_URL')}/mask/{camera_id}"
            ) as response:
                if response.status == 200:
                    mask_data = await response.read()
                    mask_array = np.frombuffer(mask_data, dtype=np.uint8)
                    mask_image = cv2.imdecode(mask_array, cv2.IMREAD_GRAYSCALE)
                    self.time_logger.info(
                        f"Mask received for camera {camera_id} in {time.time() - start_time:.2f} seconds"
                    )
                    return mask_image
                else:
                    self.logger.error(
                        f"Failed to fetch mask for camera {camera_id}, HTTP status: {response.status}"
                    )
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching mask for camera {camera_id}: {str(e)}")
            return None

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

    async def process_camera(self, session, camera_id, camera_info, model_camera_ids):
        """處理單個攝影機的影像獲取和辨識"""
        img = await self.fetch_snapshot(session, camera_id)
        mask = await self.fetch_mask(session, camera_id)
        if img is not None:
            self.logger.info(f"Image from camera {camera_id} ready for processing")
            recognition_model = camera_info.get("recognition")
            if recognition_model in self.models:
                self.call_model_single(
                    camera_id,
                    img,
                    mask,
                    recognition_model,
                    camera_info
                )
            else:
                self.logger.warning(f"No valid recognition model for camera {camera_id}")
        else:
            self.logger.warning(f"No image fetched for camera {camera_id}")

    def call_model_single(self, camera_id, image, mask, model_type, camera_info):
        """使用指定的模型處理單個攝影機的影像"""
        start_time = time.time()
        notify_message = {
            "model1": "模型1檢測",
            "model2": "模型2檢測",
            "model3": "模型3檢測",
        }

        model = self.models[model_type]
        model_config = MODEL_CONFIG[model_type]
        target_labels = list(model_config["label_conf"].keys())

        # 初始化追蹤器和標註器
        if model_type not in self.trackers:
            self.trackers[model_type] = {}
        if camera_id not in self.trackers[model_type]:
            self.trackers[model_type][camera_id] = sv.ByteTrack()
        tracker = self.trackers[model_type][camera_id]

        if model_type not in self.trace_annotators:
            self.trace_annotators[model_type] = {}
        if camera_id not in self.trace_annotators[model_type]:
            self.trace_annotators[model_type][camera_id] = sv.TraceAnnotator()
        trace_annotator = self.trace_annotators[model_type][camera_id]

        results = model.predict(image, conf=model_config["conf"])
        detections = sv.Detections.from_ultralytics(results[0])
        detections = tracker.update_with_detections(detections)

        labels = [model.names[int(class_id)] for class_id in detections.class_id]
        filtered_indices = [
            i for i, label in enumerate(labels) if label in target_labels
        ]
        filtered_detections = detections[filtered_indices]

        annotated_image, detection_flag, label = self.annotate_image(
            image,
            filtered_detections,
            mask,
            model.names,
            camera_info,
            model_type,
            trace_annotator
        )

        timestamp = time.time()
        self.save_and_notify(
            camera_id,
            annotated_image,
            timestamp,
            camera_info,
            model_type,
            notify_message,
            detection_flag,
            label,
        )

        self.time_logger.info(
            f"Model {model_type} processing for camera {camera_id} completed in {time.time() - start_time:.2f} seconds"
        )

    def annotate_image(
        self, image, detections, mask, model_names, camera_info, model_name, trace_annotator
    ):
        """對影像進行標註，並根據遮罩篩選符合的區域"""
        annotated_image = image.copy()
        annotators = self.annotators.get(model_name, {})
        box_annotator = annotators.get("box_annotator")
        label_annotator = annotators.get("label_annotator")

        if detections.tracker_id is not None:
            labels = [
                f"#{tracker_id} {model_names[int(class_id)]} {confidence:.2f}"
                for tracker_id, class_id, confidence in zip(
                    detections.tracker_id, detections.class_id, detections.confidence
                )
            ]
        else:
            labels = [
                f"{model_names[int(class_id)]} {confidence:.2f}"
                for class_id, confidence in zip(
                    detections.class_id, detections.confidence
                )
            ]

        detection_flag = len(detections) > 0
        label = ", ".join(labels) if labels else ""

        # 檢查遮罩是否為全黑或不存在，若是則使用整張圖，若遮罩無效，將其設為 None，表示不進行局部範圍檢查
        if mask is None or np.max(mask) == 0:
            self.logger.info("Mask is missing or completely black; processing the entire image.")
            mask = None  


        for detection in detections:
            x1, y1, x2, y2 = detection.xyxy[0]

            # 若遮罩有效，則僅在框選範圍內檢查
            if mask is not None:
                mask_crop = mask[int(y1):int(y2), int(x1):int(x2)]

                # 白色像素比例小於50%，跳過該檢測結果
                if mask_crop.size == 0 or np.sum(mask_crop == 255) / mask_crop.size < 0.5:
                    continue  

            # 使用標註器在影像上繪製邊框和標籤
            if box_annotator:
                annotated_image = box_annotator.annotate(
                    scene=annotated_image, detections=detections
                )
            if label_annotator:
                annotated_image = label_annotator.annotate(
                    scene=annotated_image, detections=detections, labels=labels
                )
            if trace_annotator:
                annotated_image = trace_annotator.annotate(
                    scene=annotated_image, detections=detections
                )

        return annotated_image, detection_flag, label

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
        """主迴圈，不斷檢查攝影機狀態並處理影像"""
        async with aiohttp.ClientSession() as session:
            while True:
                start_time = time.time()
                self.logger.info("Checking cameras...")

                # 獲取攝影機列表
                camera_list = self.api_service.get_camera_list()
                if not camera_list:
                    self.logger.warning("No cameras found")
                    await asyncio.sleep(self.SLEEP_INTERVAL)
                    continue
                else:
                    self.logger.debug(f"Camera list: {camera_list}")

                camera_list_by_id = {int(camera["id"]): camera for camera in camera_list}
                camera_status = await self.fetch_camera_status(session)
                if not camera_status:
                    self.logger.warning("No camera status received")
                    await asyncio.sleep(self.SLEEP_INTERVAL)
                    continue
                else:
                    self.logger.debug(f"Camera status: {camera_status}")

                tasks = []
                for camera_id_str, status in camera_status.items():
                    camera_id = int(camera_id_str)
                    if status["alive"] == "True" and status["last_image_timestamp"]:
                        camera_info = camera_list_by_id.get(camera_id)
                        if camera_info:
                            tasks.append(
                                self.process_camera(session, camera_id, camera_info, None)
                            )

                if tasks:
                    await asyncio.gather(*tasks)
                else:
                    self.logger.warning("No cameras to process.")

                await asyncio.sleep(self.SLEEP_INTERVAL)
                self.time_logger.info(
                    f"Processing completed in {time.time() - start_time:.2f} seconds"
                )

if __name__ == "__main__":
    app = MainApp()
    asyncio.run(app.main_loop())
