import requests

class CameraService:
    def __init__(self):
        self.api_url = "https://api.example.com/v1"

    def get_cameras(self):
        url = f"{self.api_url}/cameras"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        return []
