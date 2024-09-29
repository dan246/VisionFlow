import jwt
import datetime
from flask import Blueprint, request, jsonify
from extensions import db
from models.camera import Camera
from models.user import User
from .auth_routes import token_required  # 確保引入了 token_required 裝飾器

SECRET_KEY = "your_secret_key"  # 確保這個密鑰與生成 token 的密鑰一致

camera_bp = Blueprint('camera_bp', __name__)

# 獲取當前用戶的攝影機
@camera_bp.route('/cameras', methods=['GET'])
@token_required
def get_cameras(current_user):
    print(f"Current user ID: {current_user.id}")  # 打印當前用戶 ID 調試
    cameras = Camera.query.filter_by(user_id=current_user.id).all()
    print(f"Number of cameras found: {len(cameras)}")  # 打印找到的攝影機數量
    return jsonify([{
        'id': camera.id,
        'name': camera.name,
        'stream_url': camera.stream_url,
        'location': camera.location
    } for camera in cameras]), 200

# 添加攝影機並與當前用戶關聯
@camera_bp.route('/cameras', methods=['POST'])
@token_required
def add_camera(current_user):
    data = request.json

    # 檢查必填字段
    if not data.get('name') or not data.get('stream_url'):
        return jsonify({'message': 'Name and stream_url are required.'}), 400

    # 檢查攝影機名稱是否已存在
    existing_camera = Camera.query.filter_by(user_id=current_user.id, name=data['name']).first()
    if existing_camera:
        return jsonify({'message': 'A camera with this name already exists.'}), 400

    new_camera = Camera(
        name=data['name'],
        stream_url=data['stream_url'],
        location=data.get('location'),
        user_id=current_user.id  # 將攝影機與當前用戶關聯
    )
    try:
        db.session.add(new_camera)
        db.session.commit()
        # 返回新增攝影機的詳細信息，包括 ID
        return jsonify({
            'message': 'Camera added successfully',
            'id': new_camera.id,
            'name': new_camera.name,
            'stream_url': new_camera.stream_url,
            'location': new_camera.location
        }), 201
    except Exception as e:
        db.session.rollback()
        # 檢查是否因為唯一約束違反導致的錯誤
        if 'UNIQUE constraint' in str(e):
            return jsonify({'message': 'A camera with this name already exists.'}), 400
        return jsonify({'message': 'An error occurred while adding the camera.'}), 500


# 新增的刪除攝影機路由
@camera_bp.route('/cameras/<int:camera_id>', methods=['DELETE'])
@token_required
def delete_camera(current_user, camera_id):
    camera = Camera.query.filter_by(id=camera_id, user_id=current_user.id).first()
    if not camera:
        return jsonify({'message': 'Camera not found or not authorized.'}), 404
    
    try:
        db.session.delete(camera)
        db.session.commit()
        return jsonify({'message': 'Camera deleted successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while deleting the camera.'}), 500

# 獲取所有攝影機（不分使用者，供 Redis 使用）
@camera_bp.route('/cameras/all', methods=['GET'])
def get_all_cameras():
    # 返回所有攝影機
    cameras = Camera.query.all()
    return jsonify([{
        'id': camera.id,
        'name': camera.name,
        'stream_url': camera.stream_url,
        'location': camera.location,
        'user_id': camera.user_id  # 包括 user_id 以便追蹤每個攝影機的擁有者
    } for camera in cameras]), 200

@camera_bp.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email
    } for user in users]), 200

