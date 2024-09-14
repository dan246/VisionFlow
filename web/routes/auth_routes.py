import datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.user import User
import uuid
import jwt
from functools import wraps

auth_bp = Blueprint('auth_bp', __name__)

# 簽名密鑰 (應該存放於環境變數中)
SECRET_KEY = "your_secret_key"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # 從 Authorization 標頭中提取 Bearer token
            token = token.split(" ")[1]
            print(f"Token received: {token}")  # 調試 token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  # 確保使用了正確的算法
            current_user = User.query.filter_by(account_uuid=data['account_uuid']).first()
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# 產生 access token
def generate_access_token(user):
    token = jwt.encode({
        'account_uuid': user.account_uuid,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }, SECRET_KEY, algorithm="HS256")
    return token

# 產生 refresh token
def generate_refresh_token(user):
    refresh_token = jwt.encode({
        'account_uuid': user.account_uuid,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, SECRET_KEY, algorithm="HS256")
    return refresh_token

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    
    # 檢查是否有相同的用戶名
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify('Username already exists'), 400  # 返回400錯誤碼表示請求有誤
    
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(
        account_uuid=str(uuid.uuid4()),
        username=data['username'],
        email=data['email'],
        password_hash=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully', 'account_uuid': new_user.account_uuid}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    # 統一錯誤訊息，不管是用戶名還是密碼錯誤
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        return jsonify({
            'message': 'Login successful',
            'account_uuid': user.account_uuid,
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
    
    # 如果帳號或密碼錯誤，統一返回這條消息
    return jsonify({'message': 'Invalid username or password'}), 401


@auth_bp.route('/token/refresh', methods=['POST'])
def refresh_token():
    token = request.json.get('refresh_token')
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = User.query.filter_by(account_uuid=data['account_uuid']).first()
        if user:
            access_token = generate_access_token(user)
            return jsonify({'access_token': access_token}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Refresh token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401
