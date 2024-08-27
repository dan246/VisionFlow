import requests

class ApiService:
    def __init__(self, base_url):
        self.base_url = base_url
        self.access_token = ""
        self.refresh_token = ""

    # def login(self, account, password):
    #     url = f'{self.base_url}/api/v1/user/login'
    #     payload = {
    #         "account": account,
    #         "password": password
    #     }
    #     headers = {
    #         'accept': 'application/json',
    #         'Content-Type': 'application/json'
    #     }
    #     response = requests.post(url, json=payload, headers=headers)
    #     if response.status_code == 200:
    #         data = response.json()
    #         self.access_token = data.get('access_token')
    #         self.refresh_token = data.get('refresh_token')
    #         return True
    #     return False

    def get_camera_list(self):
        url = f'{self.base_url}/api/v1/cameras'
        headers = {}
        response = requests.get(url, headers=headers)
        data = response.json()
        cameralist = []
        if 'data' in data:
            for camera in data['data']:
                if camera.get('stream_url') is not None:
                    cameralist.append(camera)
        return cameralist
