from flask import Blueprint, request, jsonify
from app import db
from models.line_token import LineToken

line_token_bp = Blueprint('line_token_bp', __name__)

@line_token_bp.route('/line_tokens', methods=['GET'])
def get_line_tokens():
    tokens = LineToken.query.all()
    return jsonify([{'id': t.id, 'account_uuid': t.account_uuid, 'token': t.token} for t in tokens]), 200

@line_token_bp.route('/line_tokens', methods=['POST'])
def add_line_token():
    data = request.json
    new_token = LineToken(
        account_uuid=data['account_uuid'],
        token=data['token']
    )
    db.session.add(new_token)
    db.session.commit()
    return jsonify({'message': 'Line token added successfully'}), 201
