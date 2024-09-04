from app import db

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_uuid = db.Column(db.String(36), db.ForeignKey('user.account_uuid'), nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
