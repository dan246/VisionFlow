# models/camera.py
from extensions import db

class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stream_url = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # 新增 user_id，來關聯 User 模型
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 定義多對一的關係
    user = db.relationship('User', backref='cameras')
