"""
Performance Tests
效能測試套件
"""

import pytest
import requests
import time
import concurrent.futures
import statistics
from typing import List, Dict
from test_config import TestConfig

class TestPerformance:
    """效能測試類別"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """測試前置設定"""
        self.base_url = TestConfig.BASE_URL
        self.session = requests.Session()
        self.token = None
        
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
    
    def _measure_response_time(self, url: str, method: str = 'GET', 
                              data: Dict = None, headers: Dict = None) -> float:
        """
        測量 API 回應時間
        
        Returns:
            回應時間（毫秒）
        """
        start_time = time.perf_counter()
        
        if method == 'GET':
            response = self.session.get(url, headers=headers)
        elif method == 'POST':
            response = self.session.post(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000
        
        return response_time_ms if response.status_code < 500 else None
    
    def test_auth_login_performance(self):
        """TASK-031: 測試認證登入回應時間"""
        url = f"{self.base_url}/auth/login"
        data = {
            'username': TestConfig.TEST_USER['username'],
            'password': TestConfig.TEST_USER['password']
        }
        
        # 執行多次測試
        response_times = []
        for _ in range(10):
            response_time = self._measure_response_time(
                url, 'POST', data, TestConfig.get_headers()
            )
            if response_time:
                response_times.append(response_time)
            time.sleep(0.1)  # 避免過度請求
        
        # 計算統計資料
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"\nAuth Login Performance:")
            print(f"  Average: {avg_time:.2f}ms")
            print(f"  Min: {min_time:.2f}ms")
            print(f"  Max: {max_time:.2f}ms")
            
            # 驗證效能閾值
            assert avg_time < TestConfig.PERFORMANCE_THRESHOLDS['auth_login']
            assert max_time < TestConfig.PERFORMANCE_THRESHOLDS['auth_login'] * 1.5
    
    def test_dashboard_stats_performance(self):
        """TASK-031: 測試儀表板統計回應時間"""
        url = f"{self.base_url}/api/dashboard/stats"
        headers = TestConfig.get_headers(self.token)
        
        # 執行多次測試
        response_times = []
        for _ in range(10):
            response_time = self._measure_response_time(url, 'GET', headers=headers)
            if response_time:
                response_times.append(response_time)
            time.sleep(0.1)
        
        # 計算統計資料
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"\nDashboard Stats Performance:")
            print(f"  Average: {avg_time:.2f}ms")
            print(f"  Min: {min_time:.2f}ms")
            print(f"  Max: {max_time:.2f}ms")
            
            # 驗證效能閾值
            assert avg_time < TestConfig.PERFORMANCE_THRESHOLDS['dashboard_stats']
    
    def test_camera_list_performance(self):
        """測試攝影機列表回應時間"""
        url = f"{self.base_url}/camera/cameras"
        headers = TestConfig.get_headers(self.token)
        
        # 執行多次測試
        response_times = []
        for _ in range(10):
            response_time = self._measure_response_time(url, 'GET', headers=headers)
            if response_time:
                response_times.append(response_time)
            time.sleep(0.1)
        
        # 計算統計資料
        if response_times:
            avg_time = statistics.mean(response_times)
            
            print(f"\nCamera List Performance:")
            print(f"  Average: {avg_time:.2f}ms")
            
            # 驗證效能閾值
            assert avg_time < TestConfig.PERFORMANCE_THRESHOLDS['camera_list']
    
    def test_concurrent_requests(self):
        """TASK-032: 測試並發請求處理"""
        url = f"{self.base_url}/api/dashboard/stats"
        headers = TestConfig.get_headers(self.token)
        
        def make_request():
            """發送單一請求"""
            try:
                start_time = time.perf_counter()
                response = requests.get(url, headers=headers, timeout=5)
                end_time = time.perf_counter()
                
                if response.status_code == 200:
                    return (end_time - start_time) * 1000
                return None
            except Exception as e:
                print(f"Request failed: {e}")
                return None
        
        # 發送並發請求
        concurrent_count = TestConfig.CONCURRENT_USERS
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_count) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_count)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # 過濾有效結果
        valid_results = [r for r in results if r is not None]
        
        if valid_results:
            # 計算統計資料
            avg_time = statistics.mean(valid_results)
            max_time = max(valid_results)
            success_rate = (len(valid_results) / concurrent_count) * 100
            
            print(f"\nConcurrent Requests Performance ({concurrent_count} users):")
            print(f"  Average Response Time: {avg_time:.2f}ms")
            print(f"  Max Response Time: {max_time:.2f}ms")
            print(f"  Success Rate: {success_rate:.1f}%")
            
            # 驗證並發處理能力
            assert success_rate >= 80  # 至少 80% 成功率
            assert avg_time < 1000  # 平均回應時間小於 1 秒
    
    def test_load_testing(self):
        """負載測試"""
        url = f"{self.base_url}/api/system/status"
        headers = TestConfig.get_headers(self.token)
        
        # 逐步增加負載
        load_levels = [1, 5, 10, 20]
        results = []
        
        for load in load_levels:
            response_times = []
            errors = 0
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=load) as executor:
                futures = []
                for _ in range(load * 5):  # 每個等級發送 5 倍請求
                    futures.append(executor.submit(
                        self._measure_response_time, url, 'GET', None, headers
                    ))
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        response_times.append(result)
                    else:
                        errors += 1
            
            if response_times:
                avg_time = statistics.mean(response_times)
                p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                
                results.append({
                    'load': load,
                    'avg_response_time': avg_time,
                    'p95_response_time': p95_time,
                    'error_rate': (errors / (load * 5)) * 100
                })
                
                print(f"\nLoad Level {load}:")
                print(f"  Avg Response Time: {avg_time:.2f}ms")
                print(f"  P95 Response Time: {p95_time:.2f}ms")
                print(f"  Error Rate: {results[-1]['error_rate']:.1f}%")
        
        # 驗證系統在負載下的表現
        for result in results:
            assert result['error_rate'] < 20  # 錯誤率小於 20%
            assert result['avg_response_time'] < 2000  # 平均回應時間小於 2 秒
    
    def test_stress_testing(self):
        """壓力測試 - 找出系統極限"""
        url = f"{self.base_url}/api/dashboard/stats"
        headers = TestConfig.get_headers(self.token)
        
        max_concurrent = 50
        step = 10
        breaking_point = None
        
        for concurrent_users in range(10, max_concurrent + 1, step):
            success_count = 0
            total_requests = concurrent_users
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = []
                for _ in range(total_requests):
                    futures.append(executor.submit(
                        lambda: requests.get(url, headers=headers, timeout=5)
                    ))
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        response = future.result()
                        if response.status_code == 200:
                            success_count += 1
                    except:
                        pass
            
            success_rate = (success_count / total_requests) * 100
            
            print(f"\nStress Test - {concurrent_users} concurrent users:")
            print(f"  Success Rate: {success_rate:.1f}%")
            
            # 如果成功率低於 50%，找到了系統極限
            if success_rate < 50:
                breaking_point = concurrent_users
                print(f"  ⚠️ System breaking point reached at {concurrent_users} users")
                break
        
        # 系統應該能處理至少 10 個並發用戶
        assert breaking_point is None or breaking_point > 10
    
    def test_memory_leak_detection(self):
        """記憶體洩漏檢測"""
        url = f"{self.base_url}/api/system/status"
        headers = TestConfig.get_headers(self.token)
        
        # 取得初始記憶體使用
        initial_response = self.session.get(url, headers=headers)
        if initial_response.status_code != 200:
            pytest.skip("System status endpoint not available")
        
        initial_data = initial_response.json()
        initial_memory = float(str(initial_data.get('memory_percent', '0')).rstrip('%'))
        
        # 執行大量請求
        for _ in range(100):
            self.session.get(f"{self.base_url}/api/dashboard/stats", headers=headers)
            time.sleep(0.01)
        
        # 等待並檢查記憶體
        time.sleep(2)
        
        # 取得最終記憶體使用
        final_response = self.session.get(url, headers=headers)
        final_data = final_response.json()
        final_memory = float(str(final_data.get('memory_percent', '0')).rstrip('%'))
        
        memory_increase = final_memory - initial_memory
        
        print(f"\nMemory Leak Detection:")
        print(f"  Initial Memory: {initial_memory:.1f}%")
        print(f"  Final Memory: {final_memory:.1f}%")
        print(f"  Memory Increase: {memory_increase:.1f}%")
        
        # 記憶體增長不應超過 10%
        assert memory_increase < 10
    
    def test_api_throughput(self):
        """測試 API 吞吐量"""
        url = f"{self.base_url}/api/dashboard/stats"
        headers = TestConfig.get_headers(self.token)
        
        # 測試持續時間（秒）
        test_duration = 10
        request_count = 0
        successful_requests = 0
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            try:
                response = self.session.get(url, headers=headers, timeout=1)
                request_count += 1
                if response.status_code == 200:
                    successful_requests += 1
            except:
                request_count += 1
        
        elapsed_time = time.time() - start_time
        throughput = successful_requests / elapsed_time
        
        print(f"\nAPI Throughput Test:")
        print(f"  Duration: {elapsed_time:.1f} seconds")
        print(f"  Total Requests: {request_count}")
        print(f"  Successful Requests: {successful_requests}")
        print(f"  Throughput: {throughput:.1f} requests/second")
        
        # 系統應該能達到至少 10 requests/second
        assert throughput >= 10


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"])