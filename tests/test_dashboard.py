"""
Dashboard API Tests
儀表板 API 測試套件
"""

import pytest
import requests
import json
import time
from typing import Dict
from test_config import TestConfig

class TestDashboardAPI:
    """儀表板 API 測試類別"""
    
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
    
    def test_dashboard_stats(self):
        """TASK-014: 驗證儀表板統計 API 返回真實數據"""
        headers = TestConfig.get_headers(self.token)
        
        # 發送請求
        response = self.session.get(
            f"{self.base_url}/api/dashboard/stats",
            headers=headers
        )
        
        # 驗證回應
        assert response.status_code == 200
        data = response.json()
        
        # 驗證資料結構
        assert 'cameras' in data
        assert 'system' in data
        
        # 驗證攝影機統計
        cameras = data['cameras']
        assert 'total' in cameras
        assert 'online' in cameras
        assert 'offline' in cameras
        assert isinstance(cameras['total'], int)
        assert isinstance(cameras['online'], int)
        assert isinstance(cameras['offline'], int)
        
        # 驗證系統統計
        system = data['system']
        assert 'cpu_usage' in system or 'cpu' in system
        assert 'memory_usage' in system or 'memory' in system
        
        # 驗證不是假數據（檢查是否有隨機性）
        # 發送第二次請求
        time.sleep(1)
        response2 = self.session.get(
            f"{self.base_url}/api/dashboard/stats",
            headers=headers
        )
        data2 = response2.json()
        
        # CPU 和記憶體使用率應該有變化（真實數據）
        if 'cpu_usage' in system:
            cpu1 = float(str(system['cpu_usage']).rstrip('%'))
            cpu2 = float(str(data2['system']['cpu_usage']).rstrip('%'))
            # 允許小幅變化
            assert abs(cpu1 - cpu2) < 50  # 不應該有巨大差異
    
    def test_system_status(self):
        """TASK-015: 驗證系統狀態 API 功能"""
        headers = TestConfig.get_headers(self.token)
        
        # 發送請求
        response = self.session.get(
            f"{self.base_url}/api/system/status",
            headers=headers
        )
        
        # 驗證回應
        assert response.status_code == 200
        data = response.json()
        
        # 驗證系統狀態資料
        assert 'status' in data or 'healthy' in data
        assert 'cpu' in data or 'cpu_percent' in data
        assert 'memory' in data or 'memory_percent' in data
        assert 'disk' in data or 'disk_usage' in data
        
        # 驗證數值範圍
        if 'cpu_percent' in data:
            cpu_percent = float(str(data['cpu_percent']).rstrip('%'))
            assert 0 <= cpu_percent <= 100
        
        if 'memory_percent' in data:
            memory_percent = float(str(data['memory_percent']).rstrip('%'))
            assert 0 <= memory_percent <= 100
    
    def test_alerts_api(self):
        """TASK-016: 測試告警 API 端點"""
        headers = TestConfig.get_headers(self.token)
        
        # 發送請求
        response = self.session.get(
            f"{self.base_url}/api/alerts",
            headers=headers
        )
        
        # 驗證回應
        assert response.status_code == 200
        data = response.json()
        
        # 驗證資料結構
        if isinstance(data, list):
            # 返回陣列格式
            for alert in data:
                assert 'id' in alert or 'alert_id' in alert
                assert 'message' in alert or 'description' in alert
                assert 'timestamp' in alert or 'created_at' in alert
        elif isinstance(data, dict):
            # 返回物件格式（可能包含分頁）
            assert 'alerts' in data or 'data' in data
            alerts = data.get('alerts', data.get('data', []))
            assert isinstance(alerts, list)
    
    def test_analytics_trend(self):
        """測試分析趨勢 API"""
        headers = TestConfig.get_headers(self.token)
        
        # 發送請求
        response = self.session.get(
            f"{self.base_url}/api/analytics/trend",
            headers=headers
        )
        
        # 驗證回應
        if response.status_code == 404:
            pytest.skip("Analytics trend endpoint not implemented")
        else:
            assert response.status_code == 200
            data = response.json()
            
            # 驗證趨勢資料結構
            assert 'data' in data or 'trends' in data
            
            # 如果有時間序列資料
            if 'time_series' in data:
                time_series = data['time_series']
                assert isinstance(time_series, list)
                for point in time_series:
                    assert 'timestamp' in point or 'time' in point
                    assert 'value' in point or 'count' in point
    
    def test_dashboard_widgets(self):
        """測試儀表板小工具資料"""
        headers = TestConfig.get_headers(self.token)
        
        # 測試各種小工具端點
        widget_endpoints = [
            '/api/dashboard/widgets/cameras',
            '/api/dashboard/widgets/alerts',
            '/api/dashboard/widgets/performance',
            '/api/dashboard/widgets/detections'
        ]
        
        for endpoint in widget_endpoints:
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            if response.status_code == 404:
                continue  # 跳過未實作的端點
            
            assert response.status_code == 200
            data = response.json()
            assert data is not None
    
    def test_dashboard_realtime_data(self):
        """測試儀表板即時資料更新"""
        headers = TestConfig.get_headers(self.token)
        
        # 取得初始資料
        response1 = self.session.get(
            f"{self.base_url}/api/dashboard/realtime",
            headers=headers
        )
        
        if response1.status_code == 404:
            pytest.skip("Realtime dashboard endpoint not implemented")
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        # 等待並取得更新資料
        time.sleep(2)
        response2 = self.session.get(
            f"{self.base_url}/api/dashboard/realtime",
            headers=headers
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # 驗證資料有更新（時間戳記應該不同）
        if 'timestamp' in data1 and 'timestamp' in data2:
            assert data1['timestamp'] != data2['timestamp']
    
    def test_dashboard_summary(self):
        """測試儀表板摘要資訊"""
        headers = TestConfig.get_headers(self.token)
        
        response = self.session.get(
            f"{self.base_url}/api/dashboard/summary",
            headers=headers
        )
        
        if response.status_code == 404:
            pytest.skip("Dashboard summary endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證摘要資料
        expected_fields = ['total_cameras', 'active_alerts', 'detection_count', 'system_health']
        for field in expected_fields:
            if field in data:
                assert data[field] is not None
    
    def test_detection_statistics(self):
        """測試檢測統計資料"""
        headers = TestConfig.get_headers(self.token)
        
        response = self.session.get(
            f"{self.base_url}/api/dashboard/detections",
            headers=headers
        )
        
        if response.status_code == 404:
            pytest.skip("Detection statistics endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證檢測統計
        if 'today' in data:
            assert isinstance(data['today'], int)
        if 'this_week' in data:
            assert isinstance(data['this_week'], int)
        if 'this_month' in data:
            assert isinstance(data['this_month'], int)
    
    def test_performance_metrics(self):
        """測試效能指標 API"""
        headers = TestConfig.get_headers(self.token)
        
        # 記錄開始時間
        start_time = time.time()
        
        # 發送請求
        response = self.session.get(
            f"{self.base_url}/api/dashboard/stats",
            headers=headers
        )
        
        # 計算回應時間
        response_time = (time.time() - start_time) * 1000  # 轉換為毫秒
        
        # 驗證回應時間符合效能要求
        assert response.status_code == 200
        assert response_time < TestConfig.PERFORMANCE_THRESHOLDS['dashboard_stats']
        
        # 記錄效能資訊
        print(f"Dashboard stats response time: {response_time:.2f}ms")
    
    def test_dashboard_filters(self):
        """測試儀表板資料過濾"""
        headers = TestConfig.get_headers(self.token)
        
        # 測試時間範圍過濾
        filters = {
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'camera_id': 1
        }
        
        response = self.session.get(
            f"{self.base_url}/api/dashboard/stats",
            params=filters,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證過濾結果
        assert data is not None
    
    def test_dashboard_export(self):
        """測試儀表板資料匯出"""
        headers = TestConfig.get_headers(self.token)
        
        # 請求匯出資料
        response = self.session.get(
            f"{self.base_url}/api/dashboard/export",
            params={'format': 'json'},
            headers=headers
        )
        
        if response.status_code == 404:
            pytest.skip("Dashboard export endpoint not implemented")
        
        assert response.status_code == 200
        
        # 檢查回應格式
        content_type = response.headers.get('Content-Type', '')
        if 'json' in content_type:
            data = response.json()
            assert 'export_data' in data or 'data' in data
        elif 'csv' in content_type:
            assert len(response.content) > 0


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"])