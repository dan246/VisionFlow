import datetime
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.user import User
import uuid
import jwt
from functools import wraps

auth_bp = Blueprint('auth_bp', __name__)

def get_secret_key():
    """獲取密鑰，優先從配置中獲取"""
    return current_app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')

def token_required(f):
    """Token 驗證裝飾器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # 從 Authorization 標頭中提取 Bearer token
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            
            current_app.logger.debug(f"Token received: {token[:20]}...")  # 只記錄前20字符
            data = jwt.decode(token, get_secret_key(), algorithms=["HS256"])
            current_user = User.query.filter_by(account_uuid=data['account_uuid']).first()
            
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            current_app.logger.error(f"Token validation error: {str(e)}")
            return jsonify({'message': 'Token validation failed!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

def generate_access_token(user):
    """產生存取 token"""
    try:
        token = jwt.encode({
            'account_uuid': user.account_uuid,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        }, get_secret_key(), algorithm="HS256")
        return token
    except Exception as e:
        current_app.logger.error(f"Token generation error: {str(e)}")
        raise

def generate_refresh_token(user):
    """產生刷新 token"""
    try:
        refresh_token = jwt.encode({
            'account_uuid': user.account_uuid,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, get_secret_key(), algorithm="HS256")
        return refresh_token
    except Exception as e:
        current_app.logger.error(f"Refresh token generation error: {str(e)}")
        raise

@auth_bp.route('/register', methods=['POST'])
def register():
    """用戶註冊"""
    try:
        data = request.json
        
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'message': 'Missing required fields'}), 400
        
        # 檢查是否有相同的用戶名或電子郵件
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            if existing_user.username == data['username']:
                return jsonify({'message': 'Username already exists'}), 400
            else:
                return jsonify({'message': 'Email already exists'}), 400
        
        # 驗證密碼強度
        if len(data['password']) < 8:
            return jsonify({'message': 'Password must be at least 8 characters long'}), 400
        
        hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
        new_user = User(
            account_uuid=str(uuid.uuid4()),
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        current_app.logger.info(f"New user registered: {data['username']}")
        return jsonify({
            'message': 'User registered successfully', 
            'account_uuid': new_user.account_uuid
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'message': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用戶登入"""
    try:
        data = request.json
        
        if not data or not all(k in data for k in ('username', 'password')):
            return jsonify({'message': 'Missing username or password'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)
            
            current_app.logger.info(f"User logged in: {data['username']}")
            return jsonify({
                'message': 'Login successful',
                'account_uuid': user.account_uuid,
                'access_token': access_token,
                'refresh_token': refresh_token
            }), 200
        
        current_app.logger.warning(f"Failed login attempt for: {data.get('username', 'unknown')}")
        return jsonify({'message': 'Invalid username or password'}), 401
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'message': 'Login failed'}), 500

@auth_bp.route('/token/refresh', methods=['POST'])
def refresh_token():
    """刷新存取 token"""
    try:
        token = request.json.get('refresh_token')
        
        if not token:
            return jsonify({'message': 'Refresh token is required'}), 400
        
        data = jwt.decode(token, get_secret_key(), algorithms=["HS256"])
        user = User.query.filter_by(account_uuid=data['account_uuid']).first()
        
        if user:
            access_token = generate_access_token(user)
            current_app.logger.debug(f"Token refreshed for user: {user.username}")
            return jsonify({'access_token': access_token}), 200
        else:
            return jsonify({'message': 'User not found'}), 404
            
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Refresh token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid refresh token'}), 401
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'message': 'Token refresh failed'}), 500
        user = User.query.filter_by(account_uuid=data['account_uuid']).first()
        if user:
            access_token = generate_access_token(user)
            return jsonify({'access_token': access_token}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Refresh token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401
