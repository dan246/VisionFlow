from extensions import db  # 從 extensions 導入 db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_uuid = db.Column(db.String(36), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
