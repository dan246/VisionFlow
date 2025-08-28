#!/usr/bin/env python3
"""
VisionFlow 系統診斷工具
用於檢查系統各組件狀態並提供優化建議
"""

import requests
import json
import time
import sys
import subprocess
from colorama import init, Fore, Back, Style

init(autoreset=True)

class SystemDiagnostics:
    def __init__(self):
        self.backend_url = "http://localhost:5000"
        self.camera_ctrl_url = "http://localhost:15440"
        self.results = {
            "docker_services": {},
            "api_endpoints": {},
            "database": {},
            "recommendations": []
        }
        
    def print_header(self, text):
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{text.center(60)}")
        print(f"{Fore.CYAN}{'='*60}\n")
        
    def check_docker_services(self):
        """檢查 Docker 服務狀態"""
        self.print_header("檢查 Docker 服務狀態")
        
        try:
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.optimized.yaml", "ps"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[2:]:  # 跳過標題
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            service_name = parts[0]
                            # 檢查是否有 "Up" 在輸出中
                            is_running = "Up" in line
                            self.results["docker_services"][service_name] = is_running
                            
                            if is_running:
                                print(f"{Fore.GREEN}✓ {service_name}: 運行中")
                            else:
                                print(f"{Fore.RED}✗ {service_name}: 停止")
            else:
                print(f"{Fore.RED}無法執行 docker-compose ps")
                
        except Exception as e:
            print(f"{Fore.RED}Docker 檢查失敗: {e}")
            
    def test_api_connection(self):
        """測試 API 連接"""
        self.print_header("測試 API 端點")
        
        endpoints_to_test = [
            (self.backend_url + "/health/health", "後端健康檢查"),
            (self.backend_url + "/api/auth/test", "認證 API"),
            (self.camera_ctrl_url + "/", "攝影機控制器"),
        ]
        
        for url, name in endpoints_to_test:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"{Fore.GREEN}✓ {name}: 正常 (狀態碼: {response.status_code})")
                    self.results["api_endpoints"][name] = True
                else:
                    print(f"{Fore.YELLOW}⚠ {name}: 回應但狀態碼異常 ({response.status_code})")
                    self.results["api_endpoints"][name] = False
            except requests.exceptions.ConnectionError:
                print(f"{Fore.RED}✗ {name}: 無法連接")
                self.results["api_endpoints"][name] = False
            except Exception as e:
                print(f"{Fore.RED}✗ {name}: 錯誤 - {e}")
                self.results["api_endpoints"][name] = False
                
    def test_database_connection(self):
        """測試資料庫連接"""
        self.print_header("測試資料庫連接")
        
        try:
            # 透過後端 API 測試資料庫
            response = requests.get(f"{self.backend_url}/health/db", timeout=5)
            if response.status_code == 200:
                print(f"{Fore.GREEN}✓ PostgreSQL 資料庫: 連接正常")
                self.results["database"]["postgresql"] = True
            else:
                print(f"{Fore.RED}✗ PostgreSQL 資料庫: 連接失敗")
                self.results["database"]["postgresql"] = False
        except:
            print(f"{Fore.YELLOW}⚠ 無法透過 API 測試資料庫連接")
            self.results["database"]["postgresql"] = None
            
    def test_single_camera(self):
        """測試單一攝影機功能"""
        self.print_header("測試攝影機功能")
        
        # 測試用的 RTSP URL
        test_cameras = [
            ("rtsp://localhost:8554/test", "本地測試串流"),
            ("rtsp://admin:admin@192.168.1.100:554/stream", "IP 攝影機範例"),
        ]
        
        print(f"{Fore.YELLOW}攝影機測試需要實際的 RTSP 串流源")
        print(f"以下是一些測試建議：\n")
        
        for url, desc in test_cameras:
            print(f"  • {desc}")
            print(f"    URL: {url}")
            
        print(f"\n{Fore.CYAN}您可以使用以下方法建立測試串流：")
        print("1. 使用 FFmpeg 建立本地測試串流：")
        print("   ffmpeg -re -f lavfi -i testsrc=size=640x480:rate=30 -f rtsp rtsp://localhost:8554/test")
        print("2. 使用實際的 IP 攝影機")
        print("3. 使用 OBS Studio 的虛擬攝影機功能")
        
    def analyze_and_recommend(self):
        """分析結果並提供建議"""
        self.print_header("系統分析與建議")
        
        # 檢查 Docker 服務
        if not all(self.results["docker_services"].values()):
            self.results["recommendations"].append({
                "level": "critical",
                "issue": "部分 Docker 服務未運行",
                "solution": "執行: docker-compose -f docker-compose.optimized.yaml up -d"
            })
            
        # 檢查 API 連接
        if not self.results["api_endpoints"].get("後端健康檢查", False):
            self.results["recommendations"].append({
                "level": "critical",
                "issue": "後端 API 無法訪問",
                "solution": "檢查後端服務日誌: docker-compose logs backend"
            })
            
        # 提供優化建議
        self.results["recommendations"].extend([
            {
                "level": "info",
                "issue": "多攝影機性能優化",
                "solution": """
                1. 限制同時處理的攝影機數量（建議 2-4 路）
                2. 降低處理幀率到 10-15 FPS
                3. 使用更輕量的 YOLO 模型（如 yolo11n）
                4. 增加 Redis 緩存大小
                """
            },
            {
                "level": "info",
                "issue": "前後端連接問題",
                "solution": """
                1. 確認 CORS 設定正確
                2. 檢查 JWT Token 配置
                3. 確認 API URL 在前端正確設定
                4. 使用瀏覽器開發工具檢查網路請求
                """
            }
        ])
        
        # 輸出建議
        for rec in self.results["recommendations"]:
            if rec["level"] == "critical":
                print(f"{Fore.RED}[嚴重] {rec['issue']}")
            elif rec["level"] == "warning":
                print(f"{Fore.YELLOW}[警告] {rec['issue']}")
            else:
                print(f"{Fore.CYAN}[建議] {rec['issue']}")
            print(f"  解決方案: {rec['solution']}\n")
            
    def generate_test_script(self):
        """生成簡單的測試腳本"""
        self.print_header("生成測試腳本")
        
        test_script = '''#!/bin/bash
# VisionFlow 簡單測試腳本

echo "開始 VisionFlow 系統測試..."

# 1. 啟動服務
echo "步驟 1: 啟動 Docker 服務..."
docker-compose -f docker-compose.optimized.yaml up -d

# 等待服務啟動
echo "等待服務啟動 (30秒)..."
sleep 30

# 2. 檢查服務狀態
echo "步驟 2: 檢查服務狀態..."
docker-compose -f docker-compose.optimized.yaml ps

# 3. 測試後端 API
echo "步驟 3: 測試後端 API..."
curl -s http://localhost:5000/health/health || echo "後端 API 無回應"

# 4. 建立測試使用者
echo "步驟 4: 建立測試使用者..."
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123","email":"test@example.com"}'

# 5. 登入測試
echo "步驟 5: 測試登入..."
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}' | jq -r '.access_token')

echo "Token: ${TOKEN:0:20}..."

# 6. 開啟瀏覽器
echo "步驟 6: 開啟瀏覽器..."
echo "請訪問: http://localhost:5000"

echo "測試完成！"
'''
        
        with open("test_system.sh", "w") as f:
            f.write(test_script)
            
        print(f"{Fore.GREEN}✓ 已生成測試腳本: test_system.sh")
        print(f"  執行: chmod +x test_system.sh && ./test_system.sh")
        
    def run(self):
        """執行完整診斷"""
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("╔═══════════════════════════════════════════════════════╗")
        print("║         VisionFlow 系統診斷工具 v1.0                 ║")
        print("╚═══════════════════════════════════════════════════════╝")
        
        self.check_docker_services()
        self.test_api_connection()
        self.test_database_connection()
        self.test_single_camera()
        self.analyze_and_recommend()
        self.generate_test_script()
        
        # 儲存診斷報告
        with open("diagnosis_report.json", "w") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
            
        print(f"\n{Fore.GREEN}診斷完成！詳細報告已儲存至 diagnosis_report.json")

if __name__ == "__main__":
    diag = SystemDiagnostics()
    diag.run()