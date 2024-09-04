from flask import Blueprint, request, jsonify
from app import db
from models.notification import Notification

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
