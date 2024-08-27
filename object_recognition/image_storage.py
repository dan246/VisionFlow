import cv2
import numpy as np
import logging

class ImageStorage:
    def __init__(self, redis_instance):
        self.r = redis_instance

    def save_image(self, key, image):
        """將圖片保存到 Redis。"""
        is_success, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if is_success:
            try:
                self.r.set(key, buffer.tobytes())
                logging.info(f"Image saved to Redis under key {key}.")
            except Exception as e:
                logging.error(f"Failed to save image to Redis: {str(e)}")
        else:
            logging.error("Failed to encode image to buffer.")

    def fetch_image(self, key):
        """從 Redis 中獲取圖片。"""
        try:
            image_data = self.r.get(key)
            if image_data:
                logging.info(f"Fetched image data from Redis for key {key}")
                np_arr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                return img
            else:
                logging.error(f"No image data found in Redis for key {key}")
                return None
        except Exception as e:
            logging.error(f"Error fetching image from Redis for key {key}: {str(e)}")
            return None
