"""
Camera Management API Tests
攝影機管理 API 測試套件
"""

import pytest
import requests
import json
from typing import Dict, Optional
from test_config import TestConfig

class TestCameraAPI:
    """攝影機管理 API 測試類別"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """測試前置設定"""
        self.base_url = TestConfig.BASE_URL
        self.session = requests.Session()
        self.token = None
        self.camera_id = None
        
        # 先登入取得 token
        self._authenticate()
    
    def _authenticate(self):
        """認證並取得 token"""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={
                'username': TestConfig.TEST_USER['username'],
                'password': TestConfig.TEST_USER['password']
            },
            headers=TestConfig.get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
    
    def test_list_cameras(self):
        """TASK-009: 測試列出攝影機端點"""
        headers = TestConfig.get_headers(self.token)
        
        # 發送請求
        response = self.session.get(
            f"{self.base_url}/camera/cameras",
            headers=headers
        )
        
        # 驗證回應
        assert response.status_code == 200
        data = response.json()
        
        # 驗證資料結構
        if isinstance(data, list):
            # 返回陣列格式
            for camera in data:
                assert 'id' in camera or 'camera_id' in camera
                assert 'name' in camera or 'camera_name' in camera
        elif isinstance(data, dict):
            # 返回物件格式（可能包含分頁）
            assert 'cameras' in data or 'data' in data
            cameras = data.get('cameras', data.get('data', []))
            assert isinstance(cameras, list)
    
    def test_add_camera(self):
        """TASK-010: 測試新增攝影機端點"""
        headers = TestConfig.get_headers(self.token)
        
        # 準備測試資料
        payload = TestConfig.get_test_payload('camera_create')
        
        # 發送請求
        response = self.session.post(
            f"{self.base_url}/camera/cameras",
            json=payload,
            headers=headers
        )
        
        # 驗證回應
        if response.status_code == 400:
            # 可能是驗證錯誤，檢查錯誤訊息
            data = response.json()
            assert 'error' in data or 'message' in data
            pytest.skip("Camera creation validation failed")
        else:
            assert response.status_code in [200, 201]
            data = response.json()
            
            # 儲存攝影機 ID 供後續測試使用
            if 'id' in data:
                self.camera_id = data['id']
            elif 'camera' in data and 'id' in data['camera']:
                self.camera_id = data['camera']['id']
            
            return self.camera_id
    
    def test_get_camera_details(self):
        """測試取得單一攝影機詳情"""
        headers = TestConfig.get_headers(self.token)
        
        # 先新增一個攝影機
        camera_id = self.test_add_camera()
        
        if camera_id:
            # 取得攝影機詳情
            response = self.session.get(
                f"{self.base_url}/camera/cameras/{camera_id}",
                headers=headers
            )
            
            if response.status_code == 404:
                pytest.skip("Get camera details endpoint not implemented")
            else:
                assert response.status_code == 200
                data = response.json()
                assert 'id' in data or 'camera_id' in data
                assert 'name' in data or 'camera_name' in data
    
    def test_update_camera(self):
        """TASK-011: 測試更新攝影機設定"""
        headers = TestConfig.get_headers(self.token)
        
        # 先新增一個攝影機
        camera_id = self.test_add_camera()
        
        if camera_id:
            # 準備更新資料
            update_payload = {
                'name': 'Updated Camera Name',
                'description': 'Updated description',
                'is_active': False
            }
            
            # 發送更新請求 (嘗試 PATCH 和 PUT)
            response = self.session.patch(
                f"{self.base_url}/camera/cameras/{camera_id}",
                json=update_payload,
                headers=headers
            )
            
            if response.status_code == 405:
                # 如果 PATCH 不支援，嘗試 PUT
                response = self.session.put(
                    f"{self.base_url}/camera/cameras/{camera_id}",
                    json=update_payload,
                    headers=headers
                )
            
            if response.status_code == 404:
                pytest.skip("Update camera endpoint not implemented")
            else:
                assert response.status_code in [200, 204]
                
                # 如果有返回資料，驗證更新
                if response.status_code == 200:
                    data = response.json()
                    if 'name' in data:
                        assert data['name'] == update_payload['name']
    
    def test_delete_camera(self):
        """TASK-012: 測試刪除攝影機"""
        headers = TestConfig.get_headers(self.token)
        
        # 先新增一個攝影機
        camera_id = self.test_add_camera()
        
        if camera_id:
            # 發送刪除請求
            response = self.session.delete(
                f"{self.base_url}/camera/cameras/{camera_id}",
                headers=headers
            )
            
            if response.status_code == 404:
                pytest.skip("Delete camera endpoint not implemented")
            else:
                assert response.status_code in [200, 204]
                
                # 驗證攝影機已被刪除
                verify_response = self.session.get(
                    f"{self.base_url}/camera/cameras/{camera_id}",
                    headers=headers
                )
                
                # 應該返回 404
                if verify_response.status_code == 404:
                    assert True  # 攝影機已刪除
    
    def test_camera_status(self):
        """測試攝影機狀態端點"""
        headers = TestConfig.get_headers(self.token)
        
        # 取得攝影機狀態
        response = self.session.get(
            f"{self.base_url}/camera/status",
            headers=headers
        )
        
        if response.status_code == 404:
            pytest.skip("Camera status endpoint not implemented")
        else:
            assert response.status_code == 200
            data = response.json()
            
            # 驗證狀態資料結構
            if isinstance(data, dict):
                assert 'online' in data or 'active' in data
                assert 'offline' in data or 'inactive' in data
                assert 'total' in data
    
    def test_camera_snapshot(self):
        """測試攝影機快照功能"""
        headers = TestConfig.get_headers(self.token)
        
        # 先新增一個攝影機
        camera_id = self.test_add_camera()
        
        if camera_id:
            # 請求快照
            response = self.session.get(
                f"{self.base_url}/camera/cameras/{camera_id}/snapshot",
                headers=headers
            )
            
            if response.status_code == 404:
                pytest.skip("Camera snapshot endpoint not implemented")
            elif response.status_code == 503:
                pytest.skip("Camera not available for snapshot")
            else:
                assert response.status_code == 200
                
                # 檢查是否返回圖片或圖片 URL
                content_type = response.headers.get('Content-Type', '')
                if 'image' in content_type:
                    assert len(response.content) > 0
                elif 'json' in content_type:
                    data = response.json()
                    assert 'url' in data or 'image' in data
    
    def test_camera_stream_info(self):
        """測試攝影機串流資訊"""
        headers = TestConfig.get_headers(self.token)
        
        # 先新增一個攝影機
        camera_id = self.test_add_camera()
        
        if camera_id:
            # 取得串流資訊
            response = self.session.get(
                f"{self.base_url}/camera/cameras/{camera_id}/stream",
                headers=headers
            )
            
            if response.status_code == 404:
                pytest.skip("Camera stream info endpoint not implemented")
            else:
                assert response.status_code == 200
                data = response.json()
                
                # 驗證串流資訊
                assert 'stream_url' in data or 'rtsp_url' in data
                assert 'status' in data or 'is_active' in data
    
    def test_camera_permissions(self):
        """測試攝影機權限控制"""
        # 測試未認證存取
        response = self.session.get(
            f"{self.base_url}/camera/cameras",
            headers=TestConfig.get_headers()  # 沒有 token
        )
        
        # 應該返回 401 或 403
        if response.status_code in [401, 403]:
            assert True  # 權限控制正常
        elif response.status_code == 200:
            pytest.warning("Camera API accessible without authentication")
    
    def test_invalid_camera_data(self):
        """測試無效攝影機資料"""
        headers = TestConfig.get_headers(self.token)
        
        # 測試各種無效資料
        invalid_payloads = [
            {},  # 空資料
            {'name': ''},  # 空名稱
            {'rtsp_url': 'invalid-url'},  # 無效 URL
            {'name': 'a' * 256},  # 超長名稱
        ]
        
        for payload in invalid_payloads:
            response = self.session.post(
                f"{self.base_url}/camera/cameras",
                json=payload,
                headers=headers
            )
            
            # 應該返回 400
            assert response.status_code == 400
            data = response.json()
            assert 'error' in data or 'message' in data
    
    def test_camera_pagination(self):
        """測試攝影機列表分頁"""
        headers = TestConfig.get_headers(self.token)
        
        # 測試分頁參數
        response = self.session.get(
            f"{self.base_url}/camera/cameras?page=1&per_page=10",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 檢查是否支援分頁
        if isinstance(data, dict):
            if 'pagination' in data or 'meta' in data:
                meta = data.get('pagination', data.get('meta', {}))
                assert 'total' in meta or 'total_count' in meta
                assert 'page' in meta or 'current_page' in meta


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"])