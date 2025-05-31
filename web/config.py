import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class Config:
    """應用程式配置類別"""
    
    # 資料庫配置
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'postgresql://user:password@db:5432/vision_notify'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Flask 配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Redis 配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # API 服務配置
    API_SERVICE_URL = os.getenv('API_SERVICE_URL', 'http://backend:5000')
    CAMERA_SERVICE_URL = os.getenv('CAMERA_SERVICE_URL', 'http://camera_ctrl:5000')
    
    # 日誌配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', '/app/logs')
    
    @staticmethod
    def init_app(app):
        """初始化應用程式配置"""
        pass

class DevelopmentConfig(Config):
    """開發環境配置"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """生產環境配置"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 生產環境特定配置
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                '/app/logs/visionflow.log',
                maxBytes=10240,
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('VisionFlow startup')

class TestingConfig(Config):
    """測試環境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
