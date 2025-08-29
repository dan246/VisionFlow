#!/usr/bin/env python3
"""
VisionFlow Test Runner
測試執行和報告生成腳本
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests(test_suite='all', generate_report=True):
    """
    執行測試套件
    
    Args:
        test_suite: 測試套件名稱 (all, smoke, regression, api, websocket)
        generate_report: 是否生成測試報告
    """
    import pytest
    
    # 測試檔案映射
    test_files = {
        'auth': 'tests/test_auth.py',
        'camera': 'tests/test_camera.py',
        'dashboard': 'tests/test_dashboard.py',
        'websocket': 'tests/test_websocket.py',
        'api': ['tests/test_auth.py', 'tests/test_camera.py', 'tests/test_dashboard.py'],
        'all': 'tests/',
        'smoke': ['tests/test_auth.py::TestAuthentication::test_user_login',
                  'tests/test_dashboard.py::TestDashboardAPI::test_dashboard_stats'],
        'regression': ['tests/test_auth.py', 'tests/test_camera.py', 
                      'tests/test_dashboard.py', 'tests/test_websocket.py']
    }
    
    # 取得測試檔案
    if test_suite in test_files:
        test_paths = test_files[test_suite]
        if isinstance(test_paths, str):
            test_paths = [test_paths]
    else:
        print(f"Unknown test suite: {test_suite}")
        return False
    
    # 準備 pytest 參數
    pytest_args = []
    pytest_args.extend(test_paths)
    pytest_args.extend(['-v', '--tb=short'])
    
    # 添加報告生成選項
    if generate_report:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = Path('test_reports')
        report_dir.mkdir(exist_ok=True)
        
        # HTML 報告
        pytest_args.extend([
            '--html', f'test_reports/report_{timestamp}.html',
            '--self-contained-html'
        ])
        
        # JSON 報告
        pytest_args.extend([
            '--json-report',
            '--json-report-file', f'test_reports/report_{timestamp}.json'
        ])
        
        # 覆蓋率報告
        pytest_args.extend([
            '--cov=web',
            '--cov=camera_ctrler',
            '--cov=object_recognition',
            '--cov-report=html:test_reports/coverage_{timestamp}',
            '--cov-report=term'
        ])
    
    # 執行測試
    print(f"Running {test_suite} tests...")
    print(f"Command: pytest {' '.join(pytest_args)}")
    
    result = pytest.main(pytest_args)
    
    return result == 0


def generate_summary_report():
    """生成測試摘要報告"""
    report_dir = Path('test_reports')
    if not report_dir.exists():
        print("No test reports found")
        return
    
    # 找到最新的 JSON 報告
    json_reports = list(report_dir.glob('report_*.json'))
    if not json_reports:
        print("No JSON reports found")
        return
    
    latest_report = max(json_reports, key=lambda p: p.stat().st_mtime)
    
    with open(latest_report, 'r') as f:
        data = json.load(f)
    
    # 生成摘要
    summary = {
        'timestamp': datetime.now().isoformat(),
        'duration': data.get('duration', 0),
        'summary': data.get('summary', {}),
        'environment': data.get('environment', {}),
        'tests': []
    }
    
    # 處理測試結果
    for test in data.get('tests', []):
        test_info = {
            'name': test.get('nodeid', ''),
            'outcome': test.get('outcome', ''),
            'duration': test.get('duration', 0)
        }
        
        if test.get('outcome') == 'failed':
            test_info['error'] = test.get('call', {}).get('longrepr', '')
        
        summary['tests'].append(test_info)
    
    # 寫入摘要文件
    summary_file = report_dir / 'test_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # 打印摘要
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {summary['summary'].get('total', 0)}")
    print(f"Passed: {summary['summary'].get('passed', 0)}")
    print(f"Failed: {summary['summary'].get('failed', 0)}")
    print(f"Skipped: {summary['summary'].get('skipped', 0)}")
    print(f"Duration: {summary['duration']:.2f} seconds")
    print("="*60)
    
    # 打印失敗的測試
    failed_tests = [t for t in summary['tests'] if t['outcome'] == 'failed']
    if failed_tests:
        print("\nFAILED TESTS:")
        for test in failed_tests:
            print(f"  - {test['name']}")
    
    return summary


def check_dependencies():
    """檢查測試依賴"""
    required_packages = [
        'pytest',
        'requests',
        'python-socketio'
    ]
    
    optional_packages = [
        'pytest-html',
        'pytest-cov',
        'pytest-json-report'
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_optional.append(package)
    
    if missing_required:
        print("Missing required packages:")
        for package in missing_required:
            print(f"  pip install {package}")
        return False
    
    if missing_optional:
        print("Missing optional packages (for better reporting):")
        for package in missing_optional:
            print(f"  pip install {package}")
        print("Continue without these packages? (y/n): ", end='')
        response = input().strip().lower()
        if response != 'y':
            return False
    
    return True


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='VisionFlow Test Runner')
    parser.add_argument(
        'suite',
        nargs='?',
        default='all',
        choices=['all', 'smoke', 'regression', 'api', 'websocket', 'auth', 'camera', 'dashboard'],
        help='Test suite to run'
    )
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip report generation'
    )
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check dependencies only'
    )
    
    args = parser.parse_args()
    
    # 檢查依賴
    if args.check_deps or not check_dependencies():
        return 1 if args.check_deps else 0
    
    # 確保測試目錄存在
    if not Path('tests').exists():
        print("Error: tests directory not found")
        return 1
    
    # 執行測試
    success = run_tests(args.suite, not args.no_report)
    
    # 生成摘要報告
    if not args.no_report:
        generate_summary_report()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())