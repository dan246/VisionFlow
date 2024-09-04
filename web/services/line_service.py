import requests

class LineService:
    def __init__(self):
        self.api_url = "https://api.example.com/v1"

    def get_line_ids(self):
        url = f"{self.api_url}/notifications/line_ids"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        return []

    def send_line_notify_message(self, key, message, filepath):
        url = f"{self.api_url}/line/notify"
        payload = {'message': message, "token": key, "sec": 1}
        files = [
            ('file', ('filepath', open(filepath, 'rb'), 'image/jpeg'))
        ]
        response = requests.post(url, data=payload, files=files)
        print(response.text)
