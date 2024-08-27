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

class MailService:
    def __init__(self):
        self.mail_list = self.get_mail_list()

    def get_mail_list(self):
        url = api_url + "/notifications/email_list"
        headers = {}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                return data['data']
        return []

    def send_mail_message(self, mail, message, filepath):
        url = "https://api.example.com/v1/notifications/send_email"
        payload = {
            "to": mail,
            "message": message,
            "Subject": "【Notification System】",
            "sec": 1
        }
        files = [
            ('file', (filepath, open(filepath, 'rb'), 'image/png'))
        ]
        headers = {}

        response = requests.post(url, headers=headers, data=payload, files=files)
        print(f"Mail sent to {mail}")
        return response
