#!/usr/bin/env python3
"""
VisionFlow 系統監控腳本
實時監控系統狀態和性能指標
"""

import time
import requests
import json
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

class VisionFlowMonitor:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.services = {
            'web': {'url': f'{self.base_url}/health/health', 'port': 5000},
            'database': {'url': f'{self.base_url}/health/detailed', 'port': 5432},
            'redis': {'url': f'{self.base_url}/health/detailed', 'port': 6379},
            'camera_ctrl': {'url': 'http://localhost:15440/camera_status', 'port': 15440}
        }
        
    def check_docker_services(self) -> Dict[str, str]:
        """檢查 Docker 服務狀態"""
        try:
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.optimized.yaml', 'ps', '--format', 'json'],
                capture_output=True,
                text=True,
                cwd='/Users/litaicheng/Desktop/VisionFlow'
            )
            
            if result.returncode != 0:
                return {"error": "Docker Compose 未運行"}
            
            services_status = {}
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if line.strip():
                    try:
                        service_info = json.loads(line)
                        name = service_info.get('Service', 'unknown')
                        state = service_info.get('State', 'unknown')
                        health = service_info.get('Health', 'no_health_check')
                        
                        if health == 'healthy' or (health == 'no_health_check' and state == 'running'):
                            services_status[name] = '✅ 正常'
                        elif state == 'running' and health == 'starting':
                            services_status[name] = '🟡 啟動中'
                        else:
                            services_status[name] = f'❌ {state}'
                    except json.JSONDecodeError:
                        continue
            
            return services_status
            
        except FileNotFoundError:
            return {"error": "Docker 或 Docker Compose 未安裝"}
        except Exception as e:
            return {"error": f"檢查服務時發生錯誤: {str(e)}"}
    
    def check_service_health(self, service_name: str, config: Dict) -> Dict:
        """檢查單個服務健康狀態"""
        try:
            response = requests.get(config['url'], timeout=5)
            
            if response.status_code == 200:
                return {
                    'status': '✅ 正常',
                    'response_time': f"{response.elapsed.total_seconds():.3f}s",
                    'details': response.json() if 'json' in response.headers.get('content-type', '') else None
                }
            else:
                return {
                    'status': f'❌ HTTP {response.status_code}',
                    'response_time': f"{response.elapsed.total_seconds():.3f}s"
                }
                
        except requests.exceptions.ConnectionError:
            return {'status': '❌ 無法連接', 'response_time': 'N/A'}
        except requests.exceptions.Timeout:
            return {'status': '❌ 請求超時', 'response_time': '> 5s'}
        except Exception as e:
            return {'status': f'❌ 錯誤: {str(e)}', 'response_time': 'N/A'}
    
    def get_system_resources(self) -> Dict:
        """獲取系統資源使用情況"""
        try:
            # 獲取 Docker 容器資源使用情況
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', 
                 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳過標題行
                containers = []
                
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 5:
                            containers.append({
                                'container': parts[0],
                                'cpu': parts[1],
                                'memory': parts[2],
                                'network': parts[3],
                                'disk': parts[4]
                            })
                
                return {'containers': containers}
            else:
                return {'error': '無法獲取 Docker 統計信息'}
                
        except Exception as e:
            return {'error': f'獲取系統資源時發生錯誤: {str(e)}'}
    
    def print_status_report(self):
        """印出完整的狀態報告"""
        print("\n" + "="*80)
        print(f"🎯 VisionFlow 系統監控報告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Docker 服務狀態
        print("\n📦 Docker 服務狀態:")
        docker_status = self.check_docker_services()
        
        if 'error' in docker_status:
            print(f"   ❌ {docker_status['error']}")
        else:
            for service, status in docker_status.items():
                print(f"   {service:<20} {status}")
        
        # API 服務健康檢查
        print("\n🌐 API 服務健康檢查:")
        for service_name, config in self.services.items():
            health = self.check_service_health(service_name, config)
            print(f"   {service_name:<20} {health['status']:<15} {health['response_time']}")
        
        # 系統資源
        print("\n💻 系統資源使用:")
        resources = self.get_system_resources()
        
        if 'error' in resources:
            print(f"   ❌ {resources['error']}")
        elif 'containers' in resources:
            print(f"   {'容器名稱':<25} {'CPU':<10} {'記憶體':<20} {'網路 I/O':<15} {'磁碟 I/O'}")
            print("   " + "-"*75)
            for container in resources['containers']:
                print(f"   {container['container']:<25} {container['cpu']:<10} "
                      f"{container['memory']:<20} {container['network']:<15} {container['disk']}")
        
        print("\n" + "="*80)
    
    def run_continuous_monitoring(self, interval: int = 30):
        """持續監控模式"""
        print(f"🔄 開始持續監控 (每 {interval} 秒更新一次)")
        print("按 Ctrl+C 停止監控\n")
        
        try:
            while True:
                # 清除螢幕 (跨平台)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                self.print_status_report()
                
                # 倒數計時
                for i in range(interval, 0, -1):
                    print(f"\r⏱️  下次更新時間: {i:2d} 秒", end='', flush=True)
                    time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n👋 監控已停止")
    
    def check_logs(self, service: str = None, lines: int = 50):
        """檢查服務日誌"""
        try:
            cmd = ['docker-compose', '-f', 'docker-compose.optimized.yaml', 'logs', '--tail', str(lines)]
            
            if service:
                cmd.append(service)
            
            result = subprocess.run(
                cmd,
                cwd='/Users/litaicheng/Desktop/VisionFlow',
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"\n📜 {'所有服務' if not service else service} 日誌 (最近 {lines} 行):")
                print("-" * 80)
                print(result.stdout)
            else:
                print(f"❌ 無法獲取日誌: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 檢查日誌時發生錯誤: {str(e)}")
    
    def quick_test(self):
        """快速測試所有核心功能"""
        print("🚀 執行快速系統測試...")
        
        tests = [
            ("檢查 Docker 服務", lambda: len(self.check_docker_services()) > 0),
            ("測試 Web API", lambda: self.check_service_health('web', self.services['web'])['status'].startswith('✅')),
            ("測試攝影機控制器", lambda: self.check_service_health('camera_ctrl', self.services['camera_ctrl'])['status'].startswith('✅')),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                status = "✅ 通過" if result else "❌ 失敗"
                results.append((test_name, status))
                print(f"   {test_name:<30} {status}")
            except Exception as e:
                results.append((test_name, f"❌ 錯誤: {str(e)}"))
                print(f"   {test_name:<30} ❌ 錯誤: {str(e)}")
        
        passed = sum(1 for _, status in results if status.startswith('✅'))
        total = len(results)
        
        print(f"\n📊 測試結果: {passed}/{total} 通過")
        
        if passed == total:
            print("🎉 所有測試通過！系統運行正常")
        else:
            print("⚠️  部分測試失敗，請檢查系統狀態")

def main():
    """主函數"""
    monitor = VisionFlowMonitor()
    
    if len(sys.argv) < 2:
        print("VisionFlow 系統監控工具")
        print("\n用法:")
        print("  python3 monitor.py status     - 顯示當前狀態")
        print("  python3 monitor.py monitor    - 持續監控模式")
        print("  python3 monitor.py test       - 快速系統測試")
        print("  python3 monitor.py logs [服務名] [行數] - 查看日誌")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        monitor.print_status_report()
    
    elif command == 'monitor':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        monitor.run_continuous_monitoring(interval)
    
    elif command == 'test':
        monitor.quick_test()
    
    elif command == 'logs':
        service = sys.argv[2] if len(sys.argv) > 2 else None
        lines = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        monitor.check_logs(service, lines)
    
    else:
        print(f"❌ 未知指令: {command}")

if __name__ == "__main__":
    main()
