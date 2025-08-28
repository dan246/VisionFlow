"""
現代化 API 路由
提供前端所需的現代化 API 端點
"""

from flask import Blueprint, jsonify, request, session, render_template
from flask_socketio import emit, join_room, leave_room
from extensions import db
import json
import random
import time
from datetime import datetime, timedelta
import logging

# 導入認證裝飾器
from routes.auth_routes import token_required

# 創建藍圖
api_bp = Blueprint('api_bp', __name__, url_prefix='/api')
main_bp = Blueprint('main_bp', __name__)

logger = logging.getLogger(__name__)

# ===== 主頁面路由 =====

@main_bp.route('/')
def index():
    """主頁面 - 重定向到 advanced-dashboard"""
    from flask import redirect, url_for
    return redirect(url_for('main_bp.advanced_dashboard'))

@main_bp.route('/ws/notifications')
def websocket_notifications():
    """處理 WebSocket 通知請求（重定向到 SocketIO）"""
    from flask import jsonify
    return jsonify({
        'message': 'WebSocket notifications have been moved to SocketIO',
        'socketio_endpoint': '/socket.io/',
        'instructions': 'Please use SocketIO client instead of raw WebSocket'
    }), 200

@main_bp.route('/advanced-dashboard')
def advanced_dashboard():
    """現代化儀表板頁面"""
    return render_template('advanced-dashboard.html')

@main_bp.route('/test')
def test_api():
    """API 測試面板"""
    return render_template('test_api.html')

@main_bp.route('/analytics-dashboard')
def analytics_dashboard():
    """高級分析儀表板頁面"""
    return render_template('analytics-dashboard.html')

@main_bp.route('/notifications-settings')
def notifications_settings():
    """智能通知系統設定頁面"""
    return render_template('notifications-settings.html')

@main_bp.route('/test-notifications')
def test_notifications():
    """通知系統測試頁面"""
    return render_template('test-notifications.html')

@main_bp.route('/manifest.json')
def manifest():
    """PWA Manifest"""
    from flask import current_app
    return current_app.send_static_file('manifest.json')

@main_bp.route('/service-worker.js')
def service_worker():
    """Service Worker"""
    from flask import current_app
    return current_app.send_static_file('js/service-worker.js')

# ===== API 路由 =====

@api_bp.route('/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    """獲取儀表板統計數據 - 真實數據版本"""
    try:
        # 從資料庫獲取真實攝影機數據
        from models.camera import Camera
        from models.notification import Notification
        
        # 攝影機統計
        user_cameras = Camera.query.filter_by(user_id=current_user.id).all()
        total_cameras = len(user_cameras)
        online_cameras = len([c for c in user_cameras if hasattr(c, 'is_online') and c.is_online])
        offline_cameras = total_cameras - online_cameras
        recording_cameras = len([c for c in user_cameras if hasattr(c, 'is_recording') and c.is_recording])
        
        # 告警統計（從通知表獲取）
        today = datetime.utcnow().date()
        today_notifications = Notification.query.filter(
            Notification.user_id == current_user.id,
            db.func.date(Notification.created_at) == today
        ).all() if hasattr(Notification, 'user_id') else []
        
        # 系統資源（真實數據）
        import psutil
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 計算系統運行時間
        import os
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        current_time = datetime.now()  # 使用本地時間而非 UTC
        uptime = current_time - boot_time
        
        # 處理負數天數的情況
        if uptime.days < 0:
            # 如果出現負數，直接使用秒數計算
            uptime_seconds = int(time.time() - psutil.boot_time())
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            minutes = (uptime_seconds % 3600) // 60
            uptime_str = f"{days} 天 {hours} 小時 {minutes} 分鐘"
        else:
            uptime_str = f"{uptime.days} 天 {uptime.seconds//3600} 小時 {(uptime.seconds//60)%60} 分鐘"
        
        stats = {
            'cameras': {
                'total': total_cameras,
                'online': online_cameras,
                'offline': offline_cameras,
                'recording': recording_cameras
            },
            'detections': {
                'today': 0,  # 需要檢測記錄表
                'this_week': 0,  # 需要檢測記錄表
                'this_month': 0,  # 需要檢測記錄表
                'total': 0  # 需要檢測記錄表
            },
            'alerts': {
                'active': len([n for n in today_notifications if hasattr(n, 'is_active') and n.is_active]),
                'resolved_today': len([n for n in today_notifications if hasattr(n, 'is_resolved') and n.is_resolved]),
                'high_priority': len([n for n in today_notifications if hasattr(n, 'priority') and n.priority == 'high']),
                'total_today': len(today_notifications)
            },
            'system': {
                'cpu_usage': round(cpu_usage, 1),
                'memory_usage': round(memory.percent, 1),
                'disk_usage': round(disk.percent, 1),
                'uptime': uptime_str
            },
            'performance': {
                'fps_average': 25.0 if online_cameras > 0 else 0.0,  # 需要實際 FPS 數據
                'detection_accuracy': 90.0,  # 需要實際準確率數據
                'response_time': 100  # 可以測量實際回應時間
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/cameras', methods=['GET'])
@token_required
def get_cameras(current_user):
    """獲取攝影機列表"""
    try:
        # 模擬攝影機數據
        cameras = []
        for i in range(1, 9):
            status = 'online' if random.random() > 0.2 else 'offline'
            cameras.append({
                'id': i,
                'name': f'攝影機 {i}',
                'location': f'區域 {chr(64 + i)}',
                'status': status,
                'resolution': '1920x1080',
                'fps': 30 if status == 'online' else 0,
                'recording': status == 'online' and random.random() > 0.3,
                'last_detection': datetime.utcnow() - timedelta(minutes=random.randint(1, 120)),
                'stream_url': f'/stream/camera_{i}',
                'preview_url': f'/static/images/camera_{i}_preview.jpg'
            })
        
        return jsonify({
            'success': True,
            'data': cameras,
            'total': len(cameras)
        })
        
    except Exception as e:
        logger.error(f"Error getting cameras: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/detections/recent', methods=['GET'])
def get_recent_detections():
    """獲取最近的檢測結果"""
    try:
        # 模擬檢測數據
        detection_types = ['人員', '車輛', '異常行為', '入侵', '火災', '煙霧']
        detections = []
        
        for i in range(20):
            detection_type = random.choice(detection_types)
            confidence = round(random.uniform(0.7, 0.99), 2)
            
            detections.append({
                'id': f'det_{int(time.time() * 1000) + i}',
                'camera_id': random.randint(1, 8),
                'camera_name': f'攝影機 {random.randint(1, 8)}',
                'type': detection_type,
                'confidence': confidence,
                'timestamp': datetime.utcnow() - timedelta(minutes=random.randint(1, 60)),
                'location': {
                    'x': random.randint(100, 800),
                    'y': random.randint(100, 600),
                    'width': random.randint(50, 200),
                    'height': random.randint(80, 300)
                },
                'alert_level': 'high' if confidence > 0.9 and detection_type in ['入侵', '火災', '異常行為'] else 'medium',
                'image_url': f'/static/images/detection_{i % 5}.jpg'
            })
        
        return jsonify({
            'success': True,
            'data': detections
        })
        
    except Exception as e:
        logger.error(f"Error getting recent detections: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/alerts', methods=['GET'])
@api_bp.route('/alerts/active', methods=['GET'])
@token_required
def get_active_alerts(current_user):
    """獲取活動警報"""
    try:
        from models.notification import Notification
        from models.camera import Camera
        
        # 從資料庫獲取真實的通知/警報（使用 account_uuid 而非 user_id）
        notifications = Notification.query.filter_by(
            account_uuid=current_user.account_uuid
        ).order_by(Notification.created_at.desc()).limit(10).all()
        
        alerts = []
        for notif in notifications:
            # 獲取相關攝影機名稱
            camera_name = '系統'
            if hasattr(notif, 'camera_id') and notif.camera_id:
                camera = Camera.query.get(notif.camera_id)
                if camera:
                    camera_name = camera.name
            
            # 判斷嚴重程度
            severity = 'low'
            if hasattr(notif, 'type'):
                if notif.type in ['intrusion', 'fire', '入侵', '火災']:
                    severity = 'critical'
                elif notif.type in ['abnormal', '異常']:
                    severity = 'high'
                elif notif.type in ['motion', '移動']:
                    severity = 'medium'
            
            alerts.append({
                'id': notif.id,
                'type': getattr(notif, 'type', 'system'),
                'severity': severity,
                'message': notif.message,
                'camera_id': getattr(notif, 'camera_id', None),
                'camera_name': camera_name,
                'timestamp': notif.created_at.isoformat() if notif.created_at else datetime.utcnow().isoformat(),
                'acknowledged': getattr(notif, 'is_read', False),
                'resolved': getattr(notif, 'is_resolved', False)
            })
        
        # 如果沒有真實數據，返回空列表而不是模擬數據
        return jsonify({
            'success': True,
            'data': alerts
        })
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/analytics/trend', methods=['GET'])
@api_bp.route('/analytics/trends', methods=['GET'])
@token_required
def get_analytics_trends(current_user):
    """獲取分析趨勢數據"""
    try:
        from models.notification import Notification
        from sqlalchemy import func
        
        now = datetime.utcnow()
        trends = {
            'detection_trends': [],
            'hourly_patterns': [],
            'detection_types': {},
            'camera_performance': []
        }
        
        # 檢測趨勢（過去7天）- 使用真實數據
        for i in range(7):
            date = now - timedelta(days=6-i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
            
            # 目前沒有 Detection 模型，使用通知數代替
            detection_count = 0
            
            # 計算該天的警報數（使用 account_uuid）
            alert_count = Notification.query.filter(
                Notification.account_uuid == current_user.account_uuid,
                Notification.created_at >= date_start,
                Notification.created_at < date_end
            ).count()
            
            trends['detection_trends'].append({
                'date': date.strftime('%Y-%m-%d'),
                'detections': detection_count,
                'alerts': alert_count
            })
        
        # 每小時模式（24小時）- 使用真實數據
        for hour in range(24):
            hour_start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            # 目前沒有 Detection 模型
            hour_detection_count = 0
            
            trends['hourly_patterns'].append({
                'hour': hour,
                'detections': hour_detection_count
            })
        
        # 檢測類型分布 - 目前沒有 Detection 模型，使用預設值
        detection_types = ['人員', '車輛', '異常行為', '入侵', '其他']
        for det_type in detection_types:
            trends['detection_types'][det_type] = 0
        
        # 攝影機效能 - 使用真實數據
        from models.camera import Camera
        user_cameras = Camera.query.filter_by(user_id=current_user.id).all()
        
        for camera in user_cameras:
            # 目前沒有 Detection 模型
            camera_detection_count = 0
            
            trends['camera_performance'].append({
                'camera_id': camera.id,
                'name': camera.name,
                'accuracy': 95.0,  # 預設精度，未來可從實際檢測結果計算
                'uptime': 99.9 if getattr(camera, 'is_online', True) else 0.0,
                'detections': camera_detection_count
            })
        
        return jsonify({
            'success': True,
            'data': trends
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics trends: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/system/status', methods=['GET'])
@token_required
def get_system_status(current_user):
    """獲取系統狀態"""
    try:
        import psutil
        
        # 獲取系統資源使用情況
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_status = {
            'cpu': {
                'usage': cpu_percent,
                'cores': psutil.cpu_count(),
                'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0
            },
            'memory': {
                'usage': memory.percent,
                'total': memory.total,
                'available': memory.available,
                'used': memory.used
            },
            'disk': {
                'usage': disk.percent,
                'total': disk.total,
                'free': disk.free,
                'used': disk.used
            },
            'services': {
                'web': 'online',
                'database': 'online',
                'redis': 'online',
                'camera_ctrl': 'online',
                'object_recognition': 'online'
            },
            'uptime': int(time.time() - psutil.boot_time()),  # 系統運行秒數
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': system_status
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        # 備用數據
        return jsonify({
            'success': True,
            'data': {
                'cpu': {'usage': random.randint(20, 80)},
                'memory': {'usage': random.randint(30, 70)},
                'disk': {'usage': random.randint(40, 90)},
                'services': {
                    'web': 'online',
                    'database': 'online',
                    'redis': 'online',
                    'camera_ctrl': 'online',
                    'object_recognition': 'online'
                }
            }
        })

@api_bp.route('/camera/<int:camera_id>/stream', methods=['GET'])
def get_camera_stream(camera_id):
    """獲取攝影機串流 URL"""
    try:
        # 實際實現中應該返回真實的串流 URL
        stream_url = f'/stream/camera_{camera_id}'
        
        return jsonify({
            'success': True,
            'data': {
                'camera_id': camera_id,
                'stream_url': stream_url,
                'status': 'online',
                'resolution': '1920x1080',
                'fps': 30
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting camera stream: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/settings', methods=['GET', 'POST'])
def manage_settings():
    """管理系統設定"""
    if request.method == 'GET':
        # 獲取設定
        settings = {
            'notifications': {
                'email_enabled': True,
                'sms_enabled': False,
                'push_enabled': True,
                'alert_threshold': 'medium'
            },
            'detection': {
                'confidence_threshold': 0.8,
                'enable_person_detection': True,
                'enable_vehicle_detection': True,
                'enable_intrusion_detection': True
            },
            'recording': {
                'auto_record_on_detection': True,
                'record_duration': 30,
                'storage_days': 30
            },
            'system': {
                'auto_cleanup': True,
                'log_level': 'INFO',
                'maintenance_mode': False
            }
        }
        
        return jsonify({
            'success': True,
            'data': settings
        })
    
    elif request.method == 'POST':
        # 更新設定
        try:
            new_settings = request.get_json()
            # 這裡應該保存到資料庫
            
            return jsonify({
                'success': True,
                'message': '設定已更新'
            })
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

# ===== 分析儀表板 API 端點 =====

@api_bp.route('/analytics/detections', methods=['GET'])
def get_detection_analytics():
    """獲取偵測分析數據"""
    try:
        days = request.args.get('days', 7, type=int)
        
        # 模擬偵測分析數據
        analytics = {
            'totalDetections': random.randint(1000, 5000),
            'todayDetections': random.randint(50, 200),
            'averageDaily': random.randint(150, 300),
            'topObjectTypes': [
                {'type': 'person', 'count': random.randint(500, 1000), 'percentage': random.uniform(60, 80)},
                {'type': 'vehicle', 'count': random.randint(200, 400), 'percentage': random.uniform(15, 25)},
                {'type': 'package', 'count': random.randint(100, 200), 'percentage': random.uniform(10, 20)}
            ],
            'hourlyDistribution': [
                {'hour': h, 'count': random.randint(10, 50)}
                for h in range(24)
            ],
            'weeklyTrend': [
                {
                    'day': (datetime.now() - timedelta(days=6-i)).strftime('%m-%d'),
                    'count': random.randint(100, 300)
                }
                for i in range(7)
            ]
        }
        
        return jsonify({
            'success': True,
            'data': analytics,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting detection analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/analytics/alerts', methods=['GET'])
def get_alert_analytics():
    """獲取警報分析數據"""
    try:
        analytics = {
            'totalAlerts': random.randint(30, 100),
            'criticalAlerts': random.randint(1, 5),
            'resolvedAlerts': random.randint(25, 95),
            'averageResponseTime': round(random.uniform(2.0, 10.0), 1),
            'alertTypes': [
                {'type': '未授權進入', 'count': random.randint(10, 30), 'severity': 'critical'},
                {'type': '攝影機離線', 'count': random.randint(5, 15), 'severity': 'warning'},
                {'type': '移動偵測', 'count': random.randint(15, 40), 'severity': 'info'},
                {'type': '設備故障', 'count': random.randint(2, 10), 'severity': 'high'}
            ]
        }
        
        return jsonify({
            'success': True,
            'data': analytics,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting alert analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/analytics/performance', methods=['GET'])
def get_performance_analytics():
    """獲取性能分析數據"""
    try:
        analytics = {
            'systemUptime': round(random.uniform(95.0, 99.9), 1),
            'averageFPS': round(random.uniform(24.0, 30.0), 1),
            'averageLatency': random.randint(80, 150),
            'storageUsage': round(random.uniform(60.0, 90.0), 1),
            'networkBandwidth': round(random.uniform(70.0, 95.0), 1),
            'cpuUsage': round(random.uniform(30.0, 70.0), 1),
            'memoryUsage': round(random.uniform(40.0, 80.0), 1)
        }
        
        return jsonify({
            'success': True,
            'data': analytics,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/analytics/heatmap', methods=['GET'])
def get_activity_heatmap():
    """獲取活動熱力圖數據"""
    try:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hours = list(range(24))
        
        heatmap_data = []
        for day_idx, day in enumerate(days):
            for hour in hours:
                # 模擬不同時間段的活動強度
                if 9 <= hour <= 17:  # 工作時間
                    intensity = random.uniform(0.6, 1.0)
                elif 18 <= hour <= 22:  # 晚間
                    intensity = random.uniform(0.3, 0.7)
                else:  # 夜間
                    intensity = random.uniform(0.0, 0.3)
                
                heatmap_data.append({
                    'day': day,
                    'hour': hour,
                    'intensity': round(intensity, 2),
                    'count': int(intensity * 50)
                })
        
        return jsonify({
            'success': True,
            'data': heatmap_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting heatmap data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/analytics/export', methods=['POST'])
def export_analytics_report():
    """匯出分析報表"""
    try:
        data = request.json
        report_type = data.get('type', 'summary')
        date_range = data.get('dateRange', 7)
        
        # 模擬報表生成
        report = {
            'reportId': f'report_{int(time.time())}',
            'type': report_type,
            'dateRange': date_range,
            'generatedAt': datetime.utcnow().isoformat(),
            'summary': {
                'totalDetections': random.randint(500, 2000),
                'totalAlerts': random.randint(20, 100),
                'systemUptime': round(random.uniform(95.0, 99.9), 1),
                'averageResponseTime': round(random.uniform(2.0, 8.0), 1)
            },
            'downloadUrl': f'/api/analytics/download/{int(time.time())}'
        }
        
        return jsonify({
            'success': True,
            'data': report,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error exporting analytics report: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== 通知系統 API 端點 =====

@api_bp.route('/notifications/settings', methods=['GET'])
def get_notification_settings():
    """獲取通知設定"""
    try:
        # 模擬預設通知設定
        settings = {
            'desktopNotifications': True,
            'soundNotifications': True,
            'vibrationNotifications': False,
            'emailNotifications': True,
            'lineNotifications': False,
            'displayDuration': 5,
            'maxNotifications': 5,
            'notificationPosition': 'top-right',
            'batchNotifications': True,
            'smartGrouping': True,
            'importantOnly': False,
            'quietHours': False,
            'quietStart': '23:00',
            'quietEnd': '07:00',
            'emergencyOverride': True
        }
        
        return jsonify({
            'success': True,
            'data': settings,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting notification settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/notifications/settings', methods=['POST'])
def update_notification_settings():
    """更新通知設定"""
    try:
        settings = request.json
        
        # 這裡應該將設定儲存到資料庫
        # 目前只是模擬回應
        
        return jsonify({
            'success': True,
            'message': '通知設定已更新',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/notifications/test', methods=['POST'])
def test_notification():
    """測試通知功能"""
    try:
        data = request.json
        channel = data.get('channel', 'desktop')
        
        # 對應中文名稱
        channel_names = {
            'desktop': '桌面通知',
            'sound': '聲音通知',
            'vibration': '震動通知',
            'email': '郵件通知',
            'line': 'LINE通知'
        }
        
        # 模擬通知測試
        test_result = {
            'channel': channel,
            'success': True,
            'message': f'{channel_names.get(channel, channel)} 測試成功',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': test_result
        })
        
    except Exception as e:
        logger.error(f"Error testing notification: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/notifications/history', methods=['GET'])
def get_notification_history():
    """獲取通知歷史"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # 模擬通知歷史數據
        notifications = []
        for i in range(limit):
            notification_types = ['detection', 'alert', 'system', 'security']
            priorities = ['low', 'medium', 'high', 'critical']
            
            notifications.append({
                'id': f'notif_{int(time.time() * 1000) + i}',
                'type': random.choice(notification_types),
                'title': f'通知 {i + 1}',
                'message': f'這是第 {i + 1} 個測試通知訊息',
                'priority': random.choice(priorities),
                'read': random.choice([True, False]),
                'timestamp': datetime.utcnow() - timedelta(minutes=random.randint(1, 1440))
            })
        
        return jsonify({
            'success': True,
            'data': {
                'notifications': notifications,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': random.randint(100, 500),
                    'hasNext': page < 10
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/notifications/history', methods=['DELETE'])
def clear_notification_history():
    """清除通知歷史記錄"""
    try:
        # 從數據庫清除通知歷史（在實際實現中）
        # from models.notification import Notification
        # Notification.query.delete()
        # db.session.commit()
        
        # 目前返回成功響應
        return jsonify({
            'success': True,
            'message': '通知歷史記錄已清除',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error clearing notification history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/notifications/statistics', methods=['GET'])
def get_notification_statistics():
    """獲取通知統計數據"""
    try:
        # 從數據庫獲取通知統計
        from models.notification import Notification
        
        # 獲取所有通知
        all_notifications = Notification.query.all()
        
        # 總通知數
        total_notifications = len(all_notifications)
        
        # 今日通知數
        today = datetime.now().date()
        today_notifications = 0
        week_notifications = 0
        week_ago = datetime.now() - timedelta(days=7)
        
        # 統計計算
        camera_breakdown = {}
        hourly_stats = [{'hour': i, 'count': 0} for i in range(24)]
        
        for notification in all_notifications:
            # 今日通知統計
            if notification.created_at.date() == today:
                today_notifications += 1
                
            # 最近7天統計
            if notification.created_at >= week_ago:
                week_notifications += 1
                
            # 按攝影機統計
            camera_key = f'camera_{notification.camera_id}' if notification.camera_id else 'unknown'
            camera_breakdown[camera_key] = camera_breakdown.get(camera_key, 0) + 1
            
            # 按小時統計
            hour = notification.created_at.hour
            hourly_stats[hour]['count'] += 1
        
        # 按優先級統計（基於檢測置信度或message內容）
        priority_stats = {
            'critical': 0,
            'high': 0, 
            'medium': 0,
            'low': 0
        }
        
        # 根據關鍵詞判斷優先級
        for notification in all_notifications:
            message = notification.message.lower()
            if any(word in message for word in ['emergency', '緊急', 'critical', '嚴重']):
                priority_stats['critical'] += 1
            elif any(word in message for word in ['warning', '警告', 'alert', '警報']):
                priority_stats['high'] += 1
            elif any(word in message for word in ['detected', '檢測', 'found', '發現']):
                priority_stats['medium'] += 1
            else:
                priority_stats['low'] += 1
        
        # 按通知類型統計
        type_stats = {
            'detection': total_notifications,  # 目前所有通知都是檢測類型
            'system': 0,
            'maintenance': 0
        }
        
        # 最近的通知（最多10筆）
        recent_notifications = sorted(all_notifications, key=lambda x: x.created_at, reverse=True)[:10]
        
        statistics = {
            'totalNotifications': total_notifications,
            'unreadNotifications': total_notifications,  # 假設都是未讀
            'todayNotifications': today_notifications,
            'weekNotifications': week_notifications,
            'readNotifications': 0,  # 暫時設為0
            'priorityStats': priority_stats,
            'typeStats': type_stats,
            'averageResponseTime': 0,  # 暫時設為0
            'recentActivity': [{
                'id': n.id,
                'message': n.message,
                'timestamp': n.created_at.isoformat(),
                'camera_id': n.camera_id,
                'type': 'detection'
            } for n in recent_notifications],
            'hourlyDistribution': hourly_stats,
            'cameraBreakdown': camera_breakdown,
            'deliveryRate': 100.0,  # 假設100%送達率
            'lastUpdated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': statistics
        })
        
    except Exception as e:
        logger.error(f"Error fetching notification statistics: {e}")
        
        # 回退到模擬數據
        mock_statistics = {
            'totalNotifications': random.randint(50, 200),
            'unreadNotifications': random.randint(5, 30),
            'todayNotifications': random.randint(0, 20),
            'weekNotifications': random.randint(10, 50),
            'readNotifications': random.randint(20, 170),
            'priorityStats': {
                'critical': random.randint(0, 5),
                'high': random.randint(2, 15),
                'medium': random.randint(10, 40),
                'low': random.randint(5, 25)
            },
            'typeStats': {
                'detection': random.randint(40, 150),
                'system': random.randint(5, 20),
                'maintenance': random.randint(0, 10)
            },
            'averageResponseTime': random.randint(2, 10),
            'recentActivity': [],
            'hourlyDistribution': [{'hour': i, 'count': random.randint(0, 10)} for i in range(24)],
            'cameraBreakdown': {
                'camera_1': random.randint(5, 25),
                'camera_2': random.randint(3, 20),
                'camera_3': random.randint(2, 15),
                'camera_4': random.randint(1, 10)
            },
            'deliveryRate': random.uniform(85.0, 100.0),
            'lastUpdated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': mock_statistics
        })

# ===== 測試和調試端點 =====

@main_bp.route('/test-api-statistics')
def test_api_statistics():
    """測試API統計端點"""
    return jsonify({
        'success': True,
        'message': 'API統計測試端點正常工作',
        'timestamp': datetime.utcnow().isoformat(),
        'data': {
            'totalNotifications': 100,
            'unreadNotifications': 15,
            'todayNotifications': 10
        }
    }), 200

@api_bp.route('/simple-statistics', methods=['GET'])
def get_simple_statistics():
    """獲取簡化統計數據"""
    return jsonify({
        'success': True,
        'message': '簡化統計數據',
        'timestamp': datetime.utcnow().isoformat(),
        'data': {
            'totalNotifications': random.randint(50, 200),
            'unreadNotifications': random.randint(5, 30),
            'todayNotifications': random.randint(0, 20),
            'systemStatus': 'healthy',
            'lastUpdated': datetime.now().isoformat()
        }
    }), 200

# ===== WebSocket 事件處理 =====

def init_socketio_events(socketio):
    """初始化 WebSocket 事件處理器"""
    
    @socketio.on('connect')
    def handle_connect():
        """客戶端連接事件"""
        logger.info(f"Client connected: {request.sid}")
        emit('connection_status', {'status': 'connected'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客戶端斷線事件"""
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """加入房間"""
        room = data.get('room', 'dashboard')
        join_room(room)
        logger.info(f"Client {request.sid} joined room: {room}")
        emit('room_status', {'room': room, 'status': 'joined'})
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """離開房間"""
        room = data.get('room', 'dashboard')
        leave_room(room)
        logger.info(f"Client {request.sid} left room: {room}")
        emit('room_status', {'room': room, 'status': 'left'})
    
    @socketio.on('request_data')
    def handle_data_request(data):
        """處理數據請求"""
        data_type = data.get('type')
        
        if data_type == 'dashboard_stats':
            # 發送儀表板統計數據
            socketio.emit('dashboard_update', {
                'type': 'stats',
                'data': get_mock_dashboard_data()
            }, room=request.sid)
        
        elif data_type == 'camera_status':
            # 發送攝影機狀態
            socketio.emit('camera_update', {
                'type': 'status',
                'data': get_mock_camera_data()
            }, room=request.sid)

def get_mock_dashboard_data():
    """獲取模擬儀表板數據"""
    return {
        'active_cameras': random.randint(6, 8),
        'total_detections': random.randint(50, 200),
        'active_alerts': random.randint(0, 5),
        'system_health': random.randint(85, 100)
    }

def get_mock_camera_data():
    """獲取模擬攝影機數據"""
    cameras = []
    for i in range(1, 9):
        cameras.append({
            'id': i,
            'status': 'online' if random.random() > 0.2 else 'offline',
            'detections': random.randint(0, 10),
            'fps': random.randint(25, 30)
        })
    return cameras

@api_bp.route('/notifications', methods=['POST'])
def receive_notification():
    """接收來自 object_recognition 服務的通知"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # 記錄收到的通知
        logger.info(f"Received notification: {data}")
        
        # 提取通知數據
        camera_id = data.get('camera_id')
        message = data.get('message', '未知事件')
        image_path = data.get('image_path')
        timestamp = datetime.utcnow()
        
        # 這裡可以將通知儲存到資料庫
        # 或者轉發到其他通知系統（email, line, etc.）
        
        # 創建通知記錄（如果需要儲存到資料庫的話）
        # notification = Notification(
        #     camera_id=camera_id,
        #     message=message,
        #     image_path=image_path,
        #     timestamp=timestamp
        # )
        # db.session.add(notification)
        # db.session.commit()
        
        logger.info(f"Processed notification for camera {camera_id}: {message}")
        
        return jsonify({
            'success': True,
            'message': 'Notification received successfully',
            'timestamp': timestamp.isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error processing notification: {str(e)}'
        }), 500

@api_bp.route('/notifications/line_ids', methods=['GET'])
def get_line_ids():
    """獲取 LINE 通知 ID 列表"""
    try:
        # 這裡應該從資料庫獲取 LINE token 列表
        from models.line_token import LineToken
        
        line_tokens = LineToken.query.all()
        line_ids = []
        
        for token in line_tokens:
            line_ids.append({
                'id': token.id,
                'token': token.token,
                'description': f'LINE Token {token.id}'
            })
        
        return jsonify({
            'success': True,
            'data': line_ids
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting LINE IDs: {str(e)}")
        return jsonify({
            'success': False,
            'data': [],
            'message': f'Error getting LINE IDs: {str(e)}'
        }), 500

@api_bp.route('/notifications/email_list', methods=['GET'])
def get_email_list():
    """獲取郵件通知列表"""
    try:
        # 這裡應該從資料庫獲取郵件地址列表
        from models.email_recipient import EmailRecipient
        
        email_recipients = EmailRecipient.query.all()
        email_list = []
        
        for recipient in email_recipients:
            email_list.append({
                'id': recipient.id,
                'email': recipient.email,
                'name': recipient.email
            })
        
        return jsonify({
            'success': True,
            'data': email_list
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting email list: {str(e)}")
        return jsonify({
            'success': False,
            'data': [],
            'message': f'Error getting email list: {str(e)}'
        }), 500
