from app import db

class EmailRecipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_uuid = db.Column(db.String(36), db.ForeignKey('user.account_uuid'), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
