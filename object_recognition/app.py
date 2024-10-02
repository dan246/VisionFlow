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
        configure_logging()  # 設定日誌
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
        self.SLEEP_INTERVAL = 0.1  # 設定合理的休眠間隔

        # 新增以下兩行
        self.trackers = {}
        self.trace_annotators = {}

    def init_dirs(self):
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
        start_time = time.time()
        # 從 MODEL_CONFIG 加載模型並初始化標註器
        self.models = {}      # 用於存放模型的字典
        self.annotators = {}  # 用於存放各模型的標註器

        for model_name, config in MODEL_CONFIG.items():
            model_paths = config["path"]
            # 目前假設使用第一個路徑
            model_path = model_paths[0]
            # 使用 ultralytics YOLO 加載模型
            self.models[model_name] = YOLO(model_path)
            self.logger.info(f"Model {model_name} loaded from {model_path}")

            # 初始化標註器
            annotators_config = config.get("annotators", {})
            annotators = {}

            for annotator_name, annotator_settings in annotators_config.items():
                annotator_type = annotator_settings.get("type")
                if annotator_type == "BoxAnnotator":
                    # 初始化 BoxAnnotator
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
                    # 初始化 RoundBoxAnnotator
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
                    # 初始化 LabelAnnotator
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
            # 不需要在這裡初始化 TraceAnnotator，因為它需要為每個攝影機單獨管理
            self.annotators[model_name] = annotators

        self.time_logger.info(
            f"Models and annotators initialized in {time.time() - start_time:.2f} seconds"
        )

    async def fetch_camera_status(self, session):
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

    async def fetch_rectangles(self, session, camera_id):
        start_time = time.time()
        try:
            async with session.get(
                f"{os.getenv('CAMERA_SERVICE_URL')}/rectangles/{camera_id}"
            ) as response:
                if response.status == 200:
                    rectangles = await response.json()
                    self.time_logger.info(
                        f"Rectangles received for camera {camera_id} in {time.time() - start_time:.2f} seconds"
                    )
                    return rectangles
                else:
                    self.logger.error(
                        f"Failed to fetch rectangles for camera {camera_id}, HTTP status: {response.status}"
                    )
                    return []
        except Exception as e:
            self.logger.error(
                f"Error fetching rectangles for camera {camera_id}: {str(e)}"
            )
            return []

    async def fetch_snapshot(self, session, camera_id):
        start_time = time.time()
        redis_key = f"camera_{camera_id}_latest_frame"

        # 使用執行緒池來執行阻塞的同步函數
        loop = asyncio.get_event_loop()
        image = await loop.run_in_executor(None, self.image_storage.fetch_image, redis_key)

        self.time_logger.info(
            f"Snapshot for camera {camera_id} fetched in {time.time() - start_time:.2f} seconds"
        )
        return image

    async def process_camera(self, session, camera_id, camera_info, model_camera_ids):
        """
        處理單個攝影機的圖像獲取和辨識
        """
        # 檢查攝影機狀態
        img = await self.fetch_snapshot(session, camera_id)
        rectangles = await self.fetch_rectangles(session, camera_id)
        if img is not None:
            self.logger.info(f"Image from camera {camera_id} ready for processing")

            # 根據攝影機的模型類型進行辨識
            for model_type in model_camera_ids:
                if camera_id in model_camera_ids[model_type]:
                    self.call_model_single(
                        camera_id,
                        img,
                        rectangles,
                        model_type,
                        camera_info
                    )
        else:
            self.logger.warning(f"No image fetched for camera {camera_id}")

    def call_model_single(self, camera_id, image, rectangles, model_type, camera_info):
        """
        單獨處理一個攝影機的圖像進行模型辨識
        """
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

        # 執行模型預測
        results = model.predict(image, conf=model_config["conf"])
        # 轉換為 supervision 的 Detections 格式
        detections = sv.Detections.from_ultralytics(results[0])

        # 更新追蹤器
        detections = tracker.update_with_detections(detections)

        # 根據 target_labels 過濾結果
        labels = [model.names[int(class_id)] for class_id in detections.class_id]
        filtered_indices = [
            i for i, label in enumerate(labels) if label in target_labels
        ]
        filtered_detections = detections[filtered_indices]

        # 標註圖像
        annotated_image, detection_flag, label = self.annotate_image(
            image,
            filtered_detections,
            rectangles,
            model.names,
            camera_info,
            model_type,
            trace_annotator
        )
        # 保存和通知
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
        self, image, detections, rectangles, model_names, camera_info, model_name, trace_annotator
    ):
        annotated_image = image.copy()
        # 獲取該模型的標註器
        annotators = self.annotators.get(model_name, {})
        box_annotator = annotators.get("box_annotator")
        label_annotator = annotators.get("label_annotator")
        # 生成標籤
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

        # 如果有檢測結果，設定 detection_flag 為 True
        detection_flag = len(detections) > 0
        label = ", ".join(labels) if labels else ""

        # 使用標註器在圖像上繪製邊框和標籤
        if box_annotator:
            annotated_image = box_annotator.annotate(
                scene=annotated_image, detections=detections
            )
        if label_annotator:
            annotated_image = label_annotator.annotate(
                scene=annotated_image, detections=detections, labels=labels
            )
        # 使用 TraceAnnotator
        if trace_annotator:
            annotated_image = trace_annotator.annotate(
                scene=annotated_image,
                detections=detections
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
        start_time = time.time()
        annotated_img_path = os.path.join(
            self.ANNOTATED_SAVE_DIR, f"{camera_id}_{timestamp}.jpg"
        )
        cv2.imwrite(annotated_img_path, annotated_image)
        self.logger.info(f"Annotated image saved to {annotated_img_path}")

        # 將最新的圖像保存到串流媒體目錄
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
                self.logger.info("Checking cameras...")

                # 取得攝影機列表
                camera_list = self.api_service.get_camera_list()
                if not camera_list:
                    self.logger.warning("No cameras found")
                    await asyncio.sleep(self.SLEEP_INTERVAL)
                    continue
                else:
                    self.logger.debug(f"Camera list: {camera_list}")

                camera_list_by_id = {int(camera["id"]): camera for camera in camera_list}
                model_camera_ids = {
                    "model1": [],
                    "model2": [],
                    "model3": []
                }
                for camera in camera_list:
                    camera_id = int(camera["id"])
                    recognition_model = camera.get("recognition")
                    if recognition_model in model_camera_ids:
                        model_camera_ids[recognition_model].append(camera_id)

                # 取得攝影機狀態
                camera_status = await self.fetch_camera_status(session)
                if not camera_status:
                    self.logger.warning("No camera status received")
                    await asyncio.sleep(self.SLEEP_INTERVAL)
                    continue
                else:
                    self.logger.debug(f"Camera status: {camera_status}")

                # 建立任務列表，同時處理所有攝影機
                tasks = []
                for camera_id_str, status in camera_status.items():
                    camera_id = int(camera_id_str)
                    if status["alive"] == "True" and status["last_image_timestamp"]:
                        camera_info = camera_list_by_id.get(camera_id)
                        if camera_info:
                            tasks.append(
                                self.process_camera(session, camera_id, camera_info, model_camera_ids)
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
