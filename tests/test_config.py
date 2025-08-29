"""
VisionFlow Test Configuration
測試環境配置文件
"""

import os
from typing import Dict, Any

class TestConfig:
    """測試環境配置"""
    
    # API 基礎設定
    BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:5001')
    API_TIMEOUT = 30  # 秒
    
    # 測試用戶資訊
    TEST_USER = {
        'username': 'test',
        'password': 'test1234',
        'email': 'test@visionflow.com'
    }
    
    TEST_ADMIN = {
        'username': 'admin',
        'password': 'admin1234',
        'email': 'admin@visionflow.com'
    }
    
    # 測試攝影機資訊
    TEST_CAMERA = {
        'name': 'Test Camera 1',
        'rtsp_url': 'rtsp://test.camera:554/stream',
        'description': '測試用攝影機',
        'location': '測試區域',
        'is_active': True
    }
    
    # WebSocket 設定
    WEBSOCKET_URL = os.getenv('TEST_WS_URL', 'ws://localhost:5001')
    WS_TIMEOUT = 10  # 秒
    
    # 資料庫設定 (測試環境)
    TEST_DATABASE_URL = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql://user:password@localhost:5432/visionflow_test'
    )
    
    # Redis 設定 (測試環境)
    TEST_REDIS_URL = os.getenv(
        'TEST_REDIS_URL',
        'redis://localhost:6379/1'
    )
    
    # 效能測試閾值
    PERFORMANCE_THRESHOLDS = {
        'auth_login': 500,  # ms
        'dashboard_stats': 200,  # ms
        'camera_list': 300,  # ms
        'system_status': 100,  # ms
        'websocket_connect': 1000,  # ms
    }
    
    # 並發測試設定
    CONCURRENT_USERS = 10
    CONCURRENT_REQUESTS = 100
    
    # 測試檔案路徑
    TEST_IMAGE_PATH = 'tests/fixtures/test_image.jpg'
    TEST_VIDEO_PATH = 'tests/fixtures/test_video.mp4'
    
    # 日誌設定
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = 'tests/test_results.log'
    
    # 重試設定
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # 秒
    
    @classmethod
    def get_headers(cls, token: str = None) -> Dict[str, str]:
        """
        獲取 API 請求標頭
        
        Args:
            token: JWT token (可選)
            
        Returns:
            請求標頭字典
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        return headers
    
    @classmethod
    def get_test_payload(cls, test_type: str) -> Dict[str, Any]:
        """
        獲取測試用資料
        
        Args:
            test_type: 測試類型
            
        Returns:
            測試資料字典
        """
        payloads = {
            'register': {
                'username': f'testuser_{os.urandom(4).hex()}',
                'password': 'Test1234!',
                'email': f'test_{os.urandom(4).hex()}@example.com'
            },
            'camera_create': {
                'name': f'Camera_{os.urandom(4).hex()}',
                'rtsp_url': f'rtsp://camera_{os.urandom(4).hex()}.local/stream',
                'description': 'Auto-generated test camera',
                'is_active': True
            },
            'notification': {
                'type': 'motion_detected',
                'camera_id': 1,
                'message': 'Motion detected in test area',
                'severity': 'warning'
            }
        }
        
        return payloads.get(test_type, {})
    
    @classmethod
    def validate_response(cls, response, expected_status: int = 200) -> bool:
        """
        驗證 API 回應
        
        Args:
            response: API 回應物件
            expected_status: 預期狀態碼
            
        Returns:
            是否通過驗證
        """
        if response.status_code != expected_status:
            print(f"Status code mismatch: {response.status_code} != {expected_status}")
            return False
            
        try:
            response.json()
            return True
        except ValueError:
            print("Invalid JSON response")
            return False


# 測試環境標記
TEST_MARKERS = {
    'unit': 'Unit tests',
    'integration': 'Integration tests',
    'api': 'API tests',
    'websocket': 'WebSocket tests',
    'performance': 'Performance tests',
    'security': 'Security tests',
    'slow': 'Slow running tests',
    'critical': 'Critical path tests'
}

# 測試分組
TEST_SUITES = {
    'smoke': ['auth', 'dashboard'],
    'regression': ['auth', 'camera', 'dashboard', 'notification'],
    'full': ['*'],
    'performance': ['performance'],
    'security': ['security']
}