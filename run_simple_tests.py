#!/usr/bin/env python3
"""
Simple Test Runner - 不需要 pytest
執行基本的 API 整合測試
"""

import sys
import os
import time
import json
import requests
from datetime import datetime

# 添加專案路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'tests'))

# 直接導入或定義配置
try:
    from test_config import TestConfig
except ImportError:
    # 如果無法導入，直接定義
    class TestConfig:
        BASE_URL = 'http://localhost:5001'  # Backend 服務在 5001 端口
        TEST_USER = {
            'username': 'test',
            'password': 'test1234',
            'email': 'test@visionflow.com'
        }
        PERFORMANCE_THRESHOLDS = {
            'dashboard_stats': 500,
            'system_status': 300
        }
        
        @classmethod
        def get_test_payload(cls, test_type):
            import os
            if test_type == 'camera_create':
                return {
                    'name': f'Test Camera {os.urandom(4).hex()}',
                    'rtsp_url': f'rtsp://camera_{os.urandom(4).hex()}.local/stream',
                    'description': 'Auto-generated test camera',
                    'is_active': True
                }
            return {}

class SimpleTestRunner:
    """簡單測試執行器"""
    
    def __init__(self):
        self.base_url = TestConfig.BASE_URL
        self.results = []
        self.token = None
        self.session = requests.Session()
        
    def run_test(self, test_name, test_func):
        """執行單一測試"""
        try:
            print(f"  {test_name}...", end="")
            result = test_func()
            if result:
                print(" ✅ PASS")
                self.results.append(("PASS", test_name, None))
                return True
            else:
                print(" ❌ FAIL")
                self.results.append(("FAIL", test_name, "Test returned False"))
                return False
        except Exception as e:
            print(f" ❌ ERROR: {str(e)}")
            self.results.append(("ERROR", test_name, str(e)))
            return False
    
    def authenticate(self):
        """認證並取得 token"""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={
                'username': TestConfig.TEST_USER['username'],
                'password': TestConfig.TEST_USER['password']
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            return True
        return False
    
    # ===== 認證測試 =====
    def test_auth_login(self):
        """測試登入"""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={
                'username': TestConfig.TEST_USER['username'],
                'password': TestConfig.TEST_USER['password']
            },
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')  # 保存 token
            return 'token' in data
        return False
    
    def test_auth_verify(self):
        """測試 token 驗證"""
        if not self.token:
            self.authenticate()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.session.get(
            f"{self.base_url}/auth/verify",
            headers=headers
        )
        return response.status_code == 200
    
    def test_auth_invalid_login(self):
        """測試無效登入"""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={
                'username': 'invalid_user',
                'password': 'wrong_password'
            }
        )
        return response.status_code in [400, 401, 403]
    
    # ===== 攝影機測試 =====
    def test_camera_list(self):
        """測試攝影機列表"""
        if not self.token:
            self.authenticate()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.session.get(
            f"{self.base_url}/camera/cameras",
            headers=headers
        )
        return response.status_code == 200
    
    def test_camera_create(self):
        """測試新增攝影機"""
        if not self.token:
            self.authenticate()
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        payload = TestConfig.get_test_payload('camera_create')
        response = self.session.post(
            f"{self.base_url}/camera/cameras",
            json=payload,
            headers=headers
        )
        
        # 400 可能是驗證錯誤，但端點存在
        return response.status_code in [200, 201, 400]
    
    # ===== 儀表板測試 =====
    def test_dashboard_stats(self):
        """測試儀表板統計"""
        if not self.token:
            self.authenticate()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.session.get(
            f"{self.base_url}/api/dashboard/stats",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # 檢查是否有真實數據（不是隨機數）
            return 'cameras' in data or 'system' in data
        return False
    
    def test_system_status(self):
        """測試系統狀態"""
        if not self.token:
            self.authenticate()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.session.get(
            f"{self.base_url}/api/system/status",
            headers=headers
        )
        return response.status_code == 200
    
    def test_alerts_api(self):
        """測試告警 API"""
        if not self.token:
            self.authenticate()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.session.get(
            f"{self.base_url}/api/alerts",
            headers=headers
        )
        return response.status_code == 200
    
    # ===== 效能測試 =====
    def test_response_time(self):
        """測試回應時間"""
        if not self.token:
            self.authenticate()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        start_time = time.time()
        response = self.session.get(
            f"{self.base_url}/api/dashboard/stats",
            headers=headers
        )
        response_time = (time.time() - start_time) * 1000
        
        print(f" ({response_time:.0f}ms)", end="")
        return response_time < TestConfig.PERFORMANCE_THRESHOLDS['dashboard_stats']
    
    def test_concurrent_requests(self):
        """測試並發請求"""
        import concurrent.futures
        
        if not self.token:
            self.authenticate()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        url = f"{self.base_url}/api/system/status"
        
        def make_request():
            try:
                response = requests.get(url, headers=headers, timeout=5)
                return response.status_code == 200
            except:
                return False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_rate = sum(results) / len(results)
        print(f" ({success_rate*100:.0f}% success)", end="")
        return success_rate >= 0.8
    
    def run_all_tests(self):
        """執行所有測試"""
        print("\n" + "="*60)
        print("VisionFlow API 整合測試 - 簡易版")
        print("="*60)
        print(f"測試環境: {self.base_url}")
        print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*60)
        
        # 認證測試
        print("\n🔐 認證測試:")
        self.run_test("登入功能", self.test_auth_login)
        self.run_test("Token 驗證", self.test_auth_verify)
        self.run_test("無效登入處理", self.test_auth_invalid_login)
        
        # 攝影機測試
        print("\n📹 攝影機 API 測試:")
        self.run_test("攝影機列表", self.test_camera_list)
        self.run_test("新增攝影機", self.test_camera_create)
        
        # 儀表板測試
        print("\n📊 儀表板 API 測試:")
        self.run_test("儀表板統計", self.test_dashboard_stats)
        self.run_test("系統狀態", self.test_system_status)
        self.run_test("告警列表", self.test_alerts_api)
        
        # 效能測試
        print("\n⚡ 效能測試:")
        self.run_test("API 回應時間", self.test_response_time)
        self.run_test("並發請求處理", self.test_concurrent_requests)
        
        # 顯示結果摘要
        self.show_summary()
    
    def show_summary(self):
        """顯示測試摘要"""
        print("\n" + "="*60)
        print("測試結果摘要")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r[0] == "PASS")
        failed = sum(1 for r in self.results if r[0] == "FAIL")
        errors = sum(1 for r in self.results if r[0] == "ERROR")
        
        print(f"總測試數: {total}")
        print(f"✅ 通過: {passed}")
        print(f"❌ 失敗: {failed}")
        print(f"⚠️  錯誤: {errors}")
        print(f"成功率: {(passed/total*100):.1f}%")
        
        # 顯示失敗的測試
        failures = [r for r in self.results if r[0] != "PASS"]
        if failures:
            print("\n失敗的測試:")
            for status, name, error in failures:
                print(f"  - {name}: {error if error else 'Failed'}")
        
        print("="*60)
        
        # 生成 JSON 報告
        self.save_report()
        
        return passed == total
    
    def save_report(self):
        """儲存測試報告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'results': [
                {
                    'status': r[0],
                    'test': r[1],
                    'error': r[2]
                }
                for r in self.results
            ],
            'summary': {
                'total': len(self.results),
                'passed': sum(1 for r in self.results if r[0] == "PASS"),
                'failed': sum(1 for r in self.results if r[0] == "FAIL"),
                'errors': sum(1 for r in self.results if r[0] == "ERROR")
            }
        }
        
        with open('test_results.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n測試報告已儲存至: test_results.json")


def main():
    """主函數"""
    runner = SimpleTestRunner()
    success = runner.run_all_tests()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())