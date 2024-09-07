from flask import Blueprint, request, jsonify
from extensions import db  # 從 extensions 導入 db
from models.camera import Camera

camera_bp = Blueprint('camera_bp', __name__)

@camera_bp.route('/cameras', methods=['GET'])
def get_cameras():
    cameras = Camera.query.all()
    return jsonify([{'id': camera.id, 'name': camera.name, 'stream_url': camera.stream_url, 'location': camera.location} for camera in cameras]), 200

@camera_bp.route('/cameras', methods=['POST'])
def add_camera():
    data = request.json
    new_camera = Camera(
        name=data['name'],
        stream_url=data['stream_url'],
        location=data.get('location')
    )
    db.session.add(new_camera)
    db.session.commit()
    return jsonify({'message': 'Camera added successfully'}), 201
