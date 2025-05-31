import jwt
import datetime
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models.camera import Camera
from models.user import User
from .auth_routes import token_required

camera_bp = Blueprint('camera_bp', __name__)

@camera_bp.route('/cameras', methods=['GET'])
@token_required
def get_cameras(current_user):
    """獲取當前用戶的攝影機列表"""
    try:
        cameras = Camera.query.filter_by(user_id=current_user.id).all()
        camera_list = []
        
        for camera in cameras:
            camera_data = {
                'id': camera.id,
                'name': camera.name,
                'stream_url': camera.stream_url,
                'recognition': camera.recognition,
                'created_at': camera.created_at.isoformat() if hasattr(camera, 'created_at') and camera.created_at else None,
                'updated_at': camera.updated_at.isoformat() if hasattr(camera, 'updated_at') and camera.updated_at else None
            }
            camera_list.append(camera_data)
        
        current_app.logger.debug(f"User {current_user.username} requested {len(camera_list)} cameras")
        return jsonify(camera_list), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching cameras for user {current_user.username}: {str(e)}")
        return jsonify({'message': 'Failed to fetch cameras'}), 500

@camera_bp.route('/cameras/<int:camera_id>', methods=['PATCH'])
@token_required
def update_camera(current_user, camera_id):
    """更新攝影機資訊（部分更新）"""
    try:
        camera = Camera.query.filter_by(id=camera_id, user_id=current_user.id).first()
        
        if not camera:
            return jsonify({'message': 'Camera not found or access denied'}), 404
        
        data = request.json
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # 更新允許的欄位
        allowed_fields = ['name', 'stream_url', '']
        updated_fields = []
        
        for field in allowed_fields:
            if field in data:
                if field == 'name':
                    # 檢查名稱是否重複
                    existing_camera = Camera.query.filter(
                        Camera.user_id == current_user.id,
                        Camera.name == data[field],
                        Camera.id != camera_id
                    ).first()
                    if existing_camera:
                        return jsonify({'message': 'Camera name already exists'}), 400
                
                if hasattr(camera, field):
                    setattr(camera, field, data[field])
                    updated_fields.append(field)
        
        if not updated_fields:
            return jsonify({'message': 'No valid fields to update'}), 400
        
        # 更新修改時間（如果模型有這個欄位）
        if hasattr(camera, 'updated_at'):
            camera.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"Camera {camera_id} updated by user {current_user.username}: {updated_fields}")
        return jsonify({
            'message': 'Camera updated successfully',
            'updated_fields': updated_fields,
            'camera': {
                'id': camera.id,
                'name': camera.name,
                'stream_url': camera.stream_url,
                'recognition': camera.recognition
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating camera {camera_id}: {str(e)}")
        return jsonify({'message': 'Failed to update camera'}), 500

@camera_bp.route('/cameras', methods=['POST'])
@token_required
def add_camera(current_user):
    """新增攝影機"""
    try:
        data = request.json
        
        if not data or not all(k in data for k in ('name', 'stream_url')):
            return jsonify({'message': 'Missing required fields: name, stream_url'}), 400
        
        # 驗證輸入
        if not data['name'].strip():
            return jsonify({'message': 'Camera name cannot be empty'}), 400
        
        if not data['stream_url'].strip():
            return jsonify({'message': 'Stream URL cannot be empty'}), 400
        
        # 檢查是否已存在相同名稱的攝影機
        existing_camera = Camera.query.filter_by(
            name=data['name'].strip(), 
            user_id=current_user.id
        ).first()
        
        if existing_camera:
            return jsonify({'message': 'Camera with this name already exists'}), 400
        
        new_camera = Camera(
            name=data['name'].strip(),
            stream_url=data['stream_url'].strip(),
            recognition=data.get('recognition', 'default'),
            user_id=current_user.id
        )
        
        db.session.add(new_camera)
        db.session.commit()
        
        current_app.logger.info(f"New camera '{data['name']}' added by user {current_user.username}")
        return jsonify({
            'message': 'Camera added successfully',
            'camera': {
                'id': new_camera.id,
                'name': new_camera.name,
                'stream_url': new_camera.stream_url,
                'recognition': new_camera.recognition
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding camera: {str(e)}")
        return jsonify({'message': 'Failed to add camera'}), 500

@camera_bp.route('/cameras/<int:camera_id>', methods=['DELETE'])
@token_required
def delete_camera(current_user, camera_id):
    """刪除攝影機"""
    try:
        camera = Camera.query.filter_by(id=camera_id, user_id=current_user.id).first()
        
        if not camera:
            return jsonify({'message': 'Camera not found or access denied'}), 404
        
        camera_name = camera.name
        db.session.delete(camera)
        db.session.commit()
        
        current_app.logger.info(f"Camera '{camera_name}' deleted by user {current_user.username}")
        return jsonify({'message': 'Camera deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting camera {camera_id}: {str(e)}")
        return jsonify({'message': 'Failed to delete camera'}), 500

@camera_bp.route('/cameras/all', methods=['GET'])
def get_all_cameras():
    """獲取所有攝影機（供系統內部使用）"""
    try:
        cameras = Camera.query.all()
        camera_list = []
        
        for camera in cameras:
            camera_data = {
                'id': camera.id,
                'name': camera.name,
                'stream_url': camera.stream_url,
                'recognition': camera.recognition,
                'user_id': camera.user_id
            }
            camera_list.append(camera_data)
        
        current_app.logger.debug(f"All cameras requested: {len(camera_list)} cameras")
        return jsonify(camera_list), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching all cameras: {str(e)}")
        return jsonify({'message': 'Failed to fetch cameras'}), 500

@camera_bp.route('/users', methods=['GET'])
def get_all_users():
    """獲取所有用戶（供系統內部使用）"""
    try:
        users = User.query.all()
        user_list = []
        
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
            user_list.append(user_data)
        
        current_app.logger.debug(f"All users requested: {len(user_list)} users")
        return jsonify(user_list), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching all users: {str(e)}")
        return jsonify({'message': 'Failed to fetch users'}), 500
