import requests
import os
import cv2
import numpy as np
import json
import threading
from datetime import datetime, timedelta
import requests
from urllib.parse import urlparse

api_url = "https://api.example.com/v1"  # 替換為通用的 API URL

class LineService:
    def __init__(self):
        self.line_ids = self.get_line_ids()

    def get_line_ids(self):
        url = api_url + "/notifications/line_ids"
        headers = {}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                return data['data']
        return []

    def send_line_notify_message(self, key, message, filepath):
        url = "https://api.example.com/v1/line/notify"
        payload = {'message': message, "token": key, "sec": 1}
        files = [
            ('file', ('filepath', open(filepath, 'rb'), 'image/jpeg'))
        ]
        headers = {}

        response = requests.post(url, headers=headers, data=payload, files=files)
        print(response.text)

    # def send_line_notify_message(self, key, message, filepath):
    #     url = "https://api.example.com/v1/line/notify"
    #     headers = {'Authorization': 'Bearer ' + key}  # Line的Token通常在Headers中以Authorization形式發送
    #     files = {'file': open(filepath, 'rb')} if filepath else None
    #     data = {'message': message}
    #     try:
    #         response = requests.post(url, headers=headers, files=files, data=data)
    #         if response.status_code == 200:
    #             print(f"Message successfully sent: {response.text}")
    #         else:
    #             print(f"Error sending message: {response.text}")
    #     except Exception as e:
    #         print(f"Exception occurred while sending message: {str(e)}")
    #     finally:
    #         if files:
    #             files['file'].close()  # 確保文件被正確關閉
