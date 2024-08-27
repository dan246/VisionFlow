import requests

class MailService:
    def __init__(self):
        self.api_url = "https://api.example.com/v1"

    def get_mail_list(self):
        url = f"{self.api_url}/notifications/email_list"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        return []

    def send_mail_message(self, mail, message, filepath):
        url = f"{self.api_url}/notifications/send_email"
        payload = {
            "to": mail,
            "message": message,
            "Subject": "【Notification System】",
            "sec": 1
        }
        files = [
            ('file', (filepath, open(filepath, 'rb'), 'image/png'))
        ]
        response = requests.post(url, data=payload, files=files)
        print(f"Mail sent to {mail}")
        return response
