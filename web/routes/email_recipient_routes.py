from flask import Blueprint, request, jsonify
from app import db
from models.email_recipient import EmailRecipient

email_recipient_bp = Blueprint('email_recipient_bp', __name__)

@email_recipient_bp.route('/email_recipients', methods=['GET'])
def get_email_recipients():
    recipients = EmailRecipient.query.all()
    return jsonify([{'id': e.id, 'account_uuid': e.account_uuid, 'email': e.email} for e in recipients]), 200

@email_recipient_bp.route('/email_recipients', methods=['POST'])
def add_email_recipient():
    data = request.json
    new_recipient = EmailRecipient(
        account_uuid=data['account_uuid'],
        email=data['email']
    )
    db.session.add(new_recipient)
    db.session.commit()
    return jsonify({'message': 'Email recipient added successfully'}), 201
