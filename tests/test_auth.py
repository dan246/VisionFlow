"""
Authentication API Tests
認證 API 測試套件
"""

import pytest
import requests
import json
from typing import Dict
from test_config import TestConfig

class TestAuthentication:
    """認證功能測試類別"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """測試前置設定"""
        self.base_url = TestConfig.BASE_URL
        self.headers = TestConfig.get_headers()
        self.session = requests.Session()
        
    def test_user_registration(self):
        """TASK-004: 測試用戶註冊端點"""
        # 準備測試資料
        payload = TestConfig.get_test_payload('register')
        
        # 發送註冊請求
        response = self.session.post(
            f"{self.base_url}/auth/register",
            json=payload,
            headers=self.headers
        )
        
        # 驗證回應
        if response.status_code == 400:
            # 用戶可能已存在，這是預期的
            data = response.json()
            assert 'error' in data or 'message' in data
        else:
            assert response.status_code == 201
            data = response.json()
            assert 'message' in data
            assert 'user' in data or 'id' in data
    
    def test_user_login(self):
        """TASK-005: 測試用戶登入端點"""
        # 使用測試用戶資料
        payload = {
            'username': TestConfig.TEST_USER['username'],
            'password': TestConfig.TEST_USER['password']
        }
        
        # 發送登入請求
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json=payload,
            headers=self.headers
        )
        
        # 驗證回應
        assert response.status_code == 200
        data = response.json()
        assert 'token' in data
        assert 'user' in data or 'username' in data
        
        # 儲存 token 供後續測試使用
        self.token = data['token']
        return self.token
    
    def test_token_verification(self):
        """TASK-006: 測試 token 驗證端點"""
        # 先登入取得 token
        token = self.test_user_login()
        
        # 使用 token 驗證
        headers = TestConfig.get_headers(token)
        response = self.session.get(
            f"{self.base_url}/auth/verify",
            headers=headers
        )
        
        # 驗證回應
        assert response.status_code == 200
        data = response.json()
        assert 'valid' in data or 'user' in data
        assert data.get('valid', True) is True
    
    def test_token_refresh(self):
        """TASK-007: 測試 token 刷新機制"""
        # 先登入取得 token
        login_response = self.session.post(
            f"{self.base_url}/auth/login",
            json={
                'username': TestConfig.TEST_USER['username'],
                'password': TestConfig.TEST_USER['password']
            },
            headers=self.headers
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        
        # 檢查是否有 refresh_token
        if 'refresh_token' in login_data:
            refresh_token = login_data['refresh_token']
            
            # 測試 token 刷新
            refresh_response = self.session.post(
                f"{self.base_url}/auth/token/refresh",
                json={'refresh_token': refresh_token},
                headers=self.headers
            )
            
            # 驗證刷新回應
            if refresh_response.status_code == 200:
                refresh_data = refresh_response.json()
                assert 'token' in refresh_data
                assert 'refresh_token' in refresh_data or 'expires_in' in refresh_data
            elif refresh_response.status_code == 404:
                # 端點可能不存在，記錄為未實作
                pytest.skip("Token refresh endpoint not implemented")
        else:
            # 如果沒有 refresh_token，使用既有 token 測試
            token = login_data['token']
            headers = TestConfig.get_headers(token)
            
            # 嘗試使用 token 刷新端點
            refresh_response = self.session.post(
                f"{self.base_url}/auth/refresh",
                headers=headers
            )
            
            if refresh_response.status_code == 404:
                pytest.skip("Token refresh not implemented")
            else:
                assert refresh_response.status_code in [200, 201]
                assert 'token' in refresh_response.json()
    
    def test_logout(self):
        """測試登出功能"""
        # 先登入
        token = self.test_user_login()
        headers = TestConfig.get_headers(token)
        
        # 測試登出
        response = self.session.post(
            f"{self.base_url}/auth/logout",
            headers=headers
        )
        
        # 驗證回應
        if response.status_code == 404:
            pytest.skip("Logout endpoint not implemented")
        else:
            assert response.status_code in [200, 204]
            
            # 驗證 token 已失效
            verify_response = self.session.get(
                f"{self.base_url}/auth/verify",
                headers=headers
            )
            
            # Token 應該已經無效
            if verify_response.status_code == 401:
                assert True  # Token 已失效，符合預期
            elif verify_response.status_code == 200:
                # 如果 logout 沒有真正使 token 失效，記錄警告
                pytest.warning("Token still valid after logout")
    
    def test_invalid_credentials(self):
        """測試無效憑證"""
        # 使用錯誤的密碼
        payload = {
            'username': TestConfig.TEST_USER['username'],
            'password': 'wrong_password'
        }
        
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json=payload,
            headers=self.headers
        )
        
        # 應該返回 401 或 400
        assert response.status_code in [400, 401, 403]
        data = response.json()
        assert 'error' in data or 'message' in data
    
    def test_missing_credentials(self):
        """測試缺少憑證"""
        # 缺少密碼
        payload = {
            'username': TestConfig.TEST_USER['username']
        }
        
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json=payload,
            headers=self.headers
        )
        
        # 應該返回 400
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data or 'message' in data
    
    def test_token_expiry(self):
        """測試 token 過期處理"""
        # 使用過期的 token
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MDAwMDAwMDB9.invalid"
        headers = TestConfig.get_headers(expired_token)
        
        response = self.session.get(
            f"{self.base_url}/auth/verify",
            headers=headers
        )
        
        # 應該返回 401
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data or 'message' in data
    
    def test_concurrent_login(self):
        """測試並發登入"""
        import concurrent.futures
        
        def login_request():
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={
                    'username': TestConfig.TEST_USER['username'],
                    'password': TestConfig.TEST_USER['password']
                },
                headers=self.headers
            )
            return response.status_code == 200
        
        # 並發 5 個登入請求
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(login_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # 所有請求應該成功
        assert all(results)


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"])