from app import db

class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stream_url = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
