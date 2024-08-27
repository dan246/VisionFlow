import logging
import asyncio
import cv2
import time
import datetime
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
from tempfile import NamedTemporaryFile
import redis
from YOLOModel import YOLOModel
from ApiService import ApiService
from send_mail import MailService
from send_line import LineService
from image_storage import ImageStorage
import aiohttp
from logging_config import configure_logging


class MainApp:
    def __init__(self):
        configure_logging()  # 配置 logging
        self.logger = logging.getLogger('MainApp')
        self.time_logger = logging.getLogger('TimeLogger')
        self.redis_host = 'localhost'
        self.redis_port = 6379
        self.r = redis.Redis(host=self.redis_host, port=self.redis_port, db=0)
        self.mail_service = MailService()
        self.line_service = LineService()
        self.image_storage = ImageStorage(self.r)
        self.init_dirs()
        self.init_models()
        self.api_service = ApiService(base_url=os.getenv("API_SERVICE_URL"))
        self.last_sent_timestamps = {}
        self.SLEEP_INTERVAL = 0

    def init_dirs(self):
        start_time = time.time()
        self.BASE_SAVE_DIR = "saved_images"
        self.RAW_SAVE_DIR = os.path.join(self.BASE_SAVE_DIR, "raw_images")
        self.ANNOTATED_SAVE_DIR = os.path.join(self.BASE_SAVE_DIR, "annotated_images")
        self.STREAM_SAVE_DIR = os.path.join(self.BASE_SAVE_DIR, "stream")
        for dir_path in [self.RAW_SAVE_DIR, self.ANNOTATED_SAVE_DIR, self.STREAM_SAVE_DIR]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        self.time_logger.info(f"Directories initialized in {time.time() - start_time:.2f} seconds")

    def init_models(self):
        start_time = time.time()
        model_urls = {
            "model1": ["https://example.com/path/to/model1.pt"],
            "model2": ["https://example.com/path/to/model2.pt"],
            "model3": ["https://example.com/path/to/model3.pt"]
        }

        self.model1 = YOLOModel(model_urls["model1"])
        self.model2 = YOLOModel(model_urls["model2"])
        self.model3 = YOLOModel(model_urls["model3"])
        self.time_logger.info(f"Models initialized in {time.time() - start_time:.2f} seconds")

    async def fetch_camera_status(self, session):
        start_time = time.time()
        try:
            async with session.get(f"{os.getenv('CAMERA_SERVICE_URL')}/camera_status") as response:
                if response.status == 200:
                    camera_status = await response.json()
                    return camera_status
                else:
                    self.logger.error(f"Failed to fetch camera status, HTTP status: {response.status}")
                    return {}
        except Exception as e:
            self.logger.error(f"Error fetching camera status: {str(e)}")
            return {}

    async def fetch_rectangles(self, session, camera_id):
        start_time = time.time()
        try:
            async with session.get(f"{os.getenv('CAMERA_SERVICE_URL')}/rectangles/{camera_id}") as response:
                if response.status == 200:
                    rectangles = await response.json()
                    self.time_logger.info(f"Rectangles received for camera {camera_id} in {time.time() - start_time:.2f} seconds")
                    return rectangles
                else:
                    self.logger.error(f"Failed to fetch rectangles for camera {camera_id}, HTTP status: {response.status}")
                    return []
        except Exception as e:
            self.logger.error(f"Error fetching rectangles for camera {camera_id}: {str(e)}")
            return []

    async def fetch_snapshot(self, session, camera_id):
        start_time = time.time()
        redis_key = f"camera_{camera_id}_latest_frame"
        image = self.image_storage.fetch_image(redis_key)
        self.time_logger.info(f"Snapshot for camera {camera_id} fetched in {time.time() - start_time:.2f} seconds")
        return image

    def call_model(self, imagesid, images, rectangles_list, camera_ids, model_type, camera_list_by_id):
        start_time = time.time()
        notify_message = {
            "model1": "Model 1 Detection",
            "model2": "Model 2 Detection",
            "model3": "Model 3 Detection"
        }

        pairs = [(id, img, rect) for id, img, rect in zip(imagesid, images, rectangles_list) if id in camera_ids]
        if pairs:
            imagesid, images, rectangles_list = zip(*pairs)
        else:
            return [], [], []

        model_map = {
            "model1": self.model1,
            "model2": self.model2,
            "model3": self.model3
        }

        model = model_map[model_type]

        self.logger.info(f"Processing {len(images)} images for {model_type} detection")
        all_data = model.predict(images)
        
        # 替換顯示的標籤為通用名稱
        target_labels = ["Label A", "Label B", "Label C", "Label D"]

        for id, data_lists, image, rectangles in zip(imagesid, all_data, images, rectangles_list):
            timestamp = time.time()
            raw_img_path = os.path.join(self.RAW_SAVE_DIR, f'{id}_{timestamp}.jpg')
            cv2.imwrite(raw_img_path, image)
            self.logger.info(f"Raw image saved to {raw_img_path}")

            annotated_image, detection_flag, label = self.annotate_image(image, data_lists, rectangles, model.model_names, target_labels, camera_list_by_id[id])
            self.save_and_notify(id, annotated_image, timestamp, camera_list_by_id, model_type, notify_message, detection_flag, label)

        self.time_logger.info(f"Model {model_type} processing completed in {time.time() - start_time:.2f} seconds")
        return imagesid, images, all_data

    def annotate_image(self, image, data_lists, rectangles, model_names, target_labels, camera_info):
        annotated_image = image.copy()
        pil_img = Image.fromarray(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        font = ImageFont.truetype("simsun.ttc", 20)

        detection_flag = False
        label = ""

        for data_list, model_name in zip(data_lists, model_names):
            for inf in data_list:
                for boxe in inf.boxes:
                    for cls, conf in zip(boxe.cls, boxe.conf):
                        if conf < 0.5:
                            continue
                        class_name = model_name[int(cls)]
                        if class_name not in target_labels:
                            continue
                        detection_flag = True
                        x1, y1, x2, y2 = map(int, boxe.xyxy[0])
                        label = f'{class_name} {conf:.2f}'
                        self.draw_detection(draw, pil_img, label, x1, y1, x2, y2, font)

        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR), detection_flag, label

    def draw_detection(self, draw, pil_img, label, x1, y1, x2, y2, font):
        draw.rectangle([(x1, y1), (x2, y2)], outline="green", width=2)
        text_size = font.getbbox(label)
        text_background = Image.new('RGB', (text_size[2] - text_size[0], text_size[3] - text_size[1]), color='green')
        draw_text_background = ImageDraw.Draw(text_background)
        draw_text_background.text((0, 0), label, font=font, fill='white')
        pil_img.paste(text_background, (x1, y1 - (text_size[3] - text_size[1])))

    def save_and_notify(self, id, annotated_image, timestamp, camera_list_by_id, model_type, notify_message, detection_flag, label):
        start_time = time.time()
        annotated_img_path = os.path.join(self.ANNOTATED_SAVE_DIR, f'{id}_{timestamp}.jpg')
        cv2.imwrite(annotated_img_path, annotated_image)
        self.logger.info(f"Annotated image saved to {annotated_img_path}")

        # Save the latest image to stream directory
        stream_img_path = os.path.join(self.STREAM_SAVE_DIR, f'{id}.jpg')
        cv2.imwrite(stream_img_path, annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 70])
        self.logger.info(f"Latest image (with or without annotations) saved to {stream_img_path} for camera {id}")
        redis_key = f"camera_{id}_boxed_image"
        self.image_storage.save_image(redis_key, annotated_image)

        # 通報邏輯
        if detection_flag:
            current_time = datetime.datetime.now()
            camera_info = camera_list_by_id[id]
            account_uuid = camera_info['account_uuid']
            camera_name = camera_info['camera_name']

            # 找到相關聯的郵件和LINE tokens
            mail_recipients = [mail['email'] for mail in self.mail_service.mail_list if mail['account_uuid'] == account_uuid]
            line_tokens = [line['line_token'] for line in self.line_service.line_ids if line['account_uuid'] == account_uuid]

            utc_datetime = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
            adjusted_time = utc_datetime + datetime.timedelta(hours=8)
            detection_time = adjusted_time.strftime('%Y-%m-%d %H:%M:%S')

            title = notify_message[model_type]

            # 建立完整的訊息內容
            message_content = (
                f"title: {title}\n"
                f"Camera Name: {camera_name}\n"
                f"Event Detected: {label}\n"
                f"Detection Time: {detection_time}\n"
            )

            # 發送郵件和LINE通知
            if id not in self.last_sent_timestamps or (current_time - self.last_sent_timestamps[id]).total_seconds() >= 60:
                # 發送郵件
                for mail in mail_recipients:
                    self.mail_service.sendMailMessage(mail, message_content, annotated_img_path)

                # 發送LINE通知
                for token in line_tokens:
                    self.line_service.sendLineNotifyMessage(token, message_content, annotated_img_path)

                self.last_sent_timestamps[id] = current_time
            self.logger.info(f"Notification sent: {message_content}")

        self.time_logger.info(f"Save and notify completed in {time.time() - start_time:.2f} seconds")

    async def main_loop(self):
        async with aiohttp.ClientSession() as session:
            last_timestamps = {}
            show_image_list = {}
            while True:
                start_time = time.time()
                self.logger.info("Checking cameras...")
                images, imagesid, rectangles_list = [], [], []
                
                camera_list = self.api_service.get_camera_list()
                camera_list_by_id = {camera['id']: camera for camera in camera_list}
                model1_camera_ids, model2_camera_ids, model3_camera_ids = [], [], []
                for camera in camera_list:
                    if camera['recognition'] == "model1":
                        model1_camera_ids.append(camera['id'])
                    elif camera['recognition'] == "model2":
                        model2_camera_ids.append(camera['id'])
                    elif camera['recognition'] == "model3":
                        model3_camera_ids.append(camera['id'])
                camera_status = await self.fetch_camera_status(session)
                for camera_id, status in camera_status.items():
                    if status['alive'] == "True" and status['last_image_timestamp']:
                        img = await self.fetch_snapshot(session, camera_id)
                        rectangles = await self.fetch_rectangles(session, camera_id)
                        if img is not None:
                            images.append(img)
                            imagesid.append(int(camera_id))
                            rectangles_list.append(rectangles)
                            show_image_list[int(camera_id)] = img
                            self.logger.info(f"Image from camera {camera_id} ready for processing")
                            last_timestamps[camera_id] = status['last_image_timestamp']
                self.call_model(imagesid, images, rectangles_list, model1_camera_ids, "model1", camera_list_by_id)
                self.call_model(imagesid, images, rectangles_list, model2_camera_ids, "model2", camera_list_by_id)
                self.call_model(imagesid, images, rectangles_list, model3_camera_ids, "model3", camera_list_by_id)
                await asyncio.sleep(self.SLEEP_INTERVAL)
                if len(images)>0:
                   self.time_logger.info(f"Processing completed in {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    app = MainApp()
    asyncio.run(app.main_loop())
