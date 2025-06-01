from flask import Blueprint, request, jsonify
from extensions import db  # 從 extensions 導入 db
from models.notification import Notification
from datetime import datetime, timedelta

notification_bp = Blueprint('notification_bp', __name__)

@notification_bp.route('/notifications', methods=['GET'])
def get_notifications():
    notifications = Notification.query.all()
    return jsonify([{
        'id': n.id,
        'account_uuid': n.account_uuid,
        'camera_id': n.camera_id,
        'message': n.message,
        'image_path': n.image_path,
        'created_at': n.created_at
    } for n in notifications]), 200

@notification_bp.route('/notifications', methods=['POST'])
def add_notification():
    data = request.json
    new_notification = Notification(
        account_uuid=data['account_uuid'],
        camera_id=data.get('camera_id'),
        message=data['message'],
        image_path=data.get('image_path')
    )
    db.session.add(new_notification)
    db.session.commit()
    return jsonify({'message': 'Notification created successfully'}), 201

@notification_bp.route('/api/notifications/statistics', methods=['GET'])
def get_notification_statistics():
    """獲取通知統計數據"""
    try:
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
        }), 200
        
    except Exception as e:
        print(f"Error fetching notification statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notification_bp.route('/api/notifications/settings', methods=['GET'])
def get_notification_settings():
    """獲取通知設定"""
    # 返回預設設定，後續可以從數據庫讀取用戶設定
    default_settings = {
        'enabled': True,
        'sound': True,
        'desktop': True,
        'vibration': True,
        'email': False,
        'line': False,
        'priority': {
            'critical': True,
            'high': True,
            'medium': True,
            'low': False
        },
        'schedule': {
            'enabled': False,
            'startTime': '09:00',
            'endTime': '18:00'
        },
        'cooldown': 300  # 5分鐘冷卻
    }
    
    return jsonify({
        'success': True,
        'data': default_settings
    }), 200

@notification_bp.route('/api/notifications/settings', methods=['POST'])
def update_notification_settings():
    """更新通知設定"""
    try:
        settings = request.json
        # 這裡可以將設定保存到數據庫
        # 暫時只返回成功回應
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'data': settings
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
