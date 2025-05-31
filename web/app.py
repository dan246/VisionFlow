# filepath: VisionFlow/web/app.py
"""
Enhanced Web Application with Factory Pattern and Centralized Logging
"""

import os
import sys
from flask import Flask, render_template
from flask_cors import CORS

# ------------- 加入 shared 目錄到 Python 路徑，方便匯入設定檔等 -------------
# 在容器內，shared 目錄被掛載到 /app/shared
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from config import config  # 導入配置字典
from extensions import db, migrate, login_manager  # 由 extensions.py 匯出

# 嘗試導入 shared logging，如果失敗則使用 Flask 默認的 logging
try:
    from shared.logging_config import setup_logging  # logging 設定
    SHARED_LOGGING_AVAILABLE = True
except ImportError:
    SHARED_LOGGING_AVAILABLE = False

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__, static_folder="static", template_folder="templates")
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    config_obj = config.get(config_name, config['default'])
    app.config.from_object(config_obj)
    
    # Setup logging - 嘗試使用 shared logging，失敗則使用 Flask 默認
    if SHARED_LOGGING_AVAILABLE:
        try:
            logger = setup_logging(
                service_name="web_service",
                log_level=app.config.get('LOG_LEVEL', 'INFO'),
                console_output=True,
                file_output=True
            )
            # 把 logger 綁到 flask app
            app.logger = logger
            app.logger.info("Using shared logging configuration")
        except Exception as e:
            app.logger.warning(f"Failed to setup shared logging: {e}, using Flask default logging")
    else:
        app.logger.info("Shared logging not available, using Flask default logging")
    
    # ---------------- 初始化擴充套件 ----------------
    # 1. 初始化 SQLAlchemy
    db.init_app(app)
    # 2. 初始化 Flask-Migrate (必須在 db.init_app(app) 之後)
    migrate.init_app(app, db)
    # 3. 初始化 Flask-Login
    login_manager.init_app(app)
    
    # Configure CORS (允許跨域)
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    # 註冊藍圖
    register_blueprints(app)
    
    # 設定登入頁面與訊息 (可依需求修改)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '請先登入以存取此頁面'
    
    @login_manager.user_loader
    def load_user(user_id):
        # 這段要在 models/user.py 定義 User 類別
        from models.user import User
        return User.query.get(int(user_id))
    
    # Import models in app context (確保在 app_context 下可以正確匯入 Model 類別)
    with app.app_context():
        from models.user import User
        from models.camera import Camera
        from models.line_token import LineToken
        from models.email_recipient import EmailRecipient
        from models.notification import Notification
    
    # ---------------- 定義主要路由 ----------------
    @app.route('/')
    def index():
        """首頁"""
        return render_template('index.html')
    
    @app.route('/snapshot_ui/<camera_id>')
    def snapshot_ui(camera_id):
        """攝影機快照介面"""
        return render_template('snapshot_ui.html', camera_id=camera_id)
    
    @app.route('/register')
    def register():
        """註冊頁面"""
        return render_template('register.html')
    
    @app.route('/draw_area')
    def draw_area():
        """繪製辨識區域頁面"""
        return render_template('draw_area.html')
    
    # ---------------- 錯誤處理 ----------------
    @app.errorhandler(404)
    def not_found_error(error):
        """404 錯誤處理"""
        app.logger.warning(f"404 error: {error}")
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 錯誤處理"""
        app.logger.error(f"500 error: {error}")
        db.session.rollback()  # 發生 500 時回滾資料庫連線
        return render_template('errors/500.html'), 500
    
    app.logger.info(f"Web service started with config: {config_name}")
    return app

def register_blueprints(app):
    """註冊應用程式藍圖 (Blueprints)"""
    from routes.auth_routes import auth_bp
    from routes.camera_routes import camera_bp
    from routes.notification_routes import notification_bp
    from routes.line_token_routes import line_token_bp
    from routes.email_recipient_routes import email_recipient_bp
    from routes.health_routes import health_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(camera_bp, url_prefix='/camera')
    app.register_blueprint(notification_bp, url_prefix='/notification')
    app.register_blueprint(line_token_bp, url_prefix='/line')
    app.register_blueprint(email_recipient_bp, url_prefix='/email')
    app.register_blueprint(health_bp, url_prefix='/health')

# Create app instance
app = create_app()

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0', 
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
