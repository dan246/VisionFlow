# -*- coding: utf-8 -*-
"""
Object Recognition Service Configuration
Handles environment variables and configuration settings for the object recognition service.
"""

import os
from typing import Dict, Any, Optional
import logging


class Config:
    """Base configuration class with common settings."""
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD')
    
    # API Service Configuration
    API_SERVICE_URL: str = os.getenv('API_SERVICE_URL', 'http://backend:5000')
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT', '30'))
    
    # Model Configuration
    MODEL_PATH_BASE: str = os.getenv('MODEL_PATH_BASE', '/app/models')
    DEFAULT_MODEL_CONFIDENCE: float = float(os.getenv('DEFAULT_MODEL_CONFIDENCE', '0.5'))
    
    # Processing Configuration
    SLEEP_INTERVAL: float = float(os.getenv('PROCESSING_SLEEP_INTERVAL', '0.1'))
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '4'))
    
    # Storage Configuration
    BASE_SAVE_DIR: str = os.getenv('BASE_SAVE_DIR', 'saved_images')
    ENABLE_IMAGE_SAVING: bool = os.getenv('ENABLE_IMAGE_SAVING', 'true').lower() == 'true'
    IMAGE_RETENTION_DAYS: int = int(os.getenv('IMAGE_RETENTION_DAYS', '7'))
    
    # Notification Configuration
    NOTIFICATION_COOLDOWN: int = int(os.getenv('NOTIFICATION_COOLDOWN', '60'))  # seconds
    ENABLE_EMAIL_NOTIFICATIONS: bool = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
    ENABLE_LINE_NOTIFICATIONS: bool = os.getenv('ENABLE_LINE_NOTIFICATIONS', 'false').lower() == 'true'
    
    # Email Configuration
    SMTP_SERVER: str = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME: str = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD', '')
    EMAIL_FROM: str = os.getenv('EMAIL_FROM', '')
    
    # LINE Notify Configuration
    LINE_NOTIFY_TOKEN: str = os.getenv('LINE_NOTIFY_TOKEN', '')
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ENABLE_FILE_LOGGING: bool = os.getenv('ENABLE_FILE_LOGGING', 'true').lower() == 'true'
    LOG_FILE_PATH: str = os.getenv('LOG_FILE_PATH', 'logs/object_recognition.log')
    LOG_FILE_MAX_BYTES: int = int(os.getenv('LOG_FILE_MAX_BYTES', '10485760'))  # 10MB
    LOG_FILE_BACKUP_COUNT: int = int(os.getenv('LOG_FILE_BACKUP_COUNT', '5'))
    
    # Performance Configuration
    GPU_ENABLED: bool = os.getenv('GPU_ENABLED', 'false').lower() == 'true'
    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', '1'))
    
    @classmethod
    def validate_config(cls) -> Dict[str, str]:
        """Validate configuration and return any errors."""
        errors = []
        
        # Validate required fields
        if not cls.API_SERVICE_URL:
            errors.append("API_SERVICE_URL is required")
        
        if cls.ENABLE_EMAIL_NOTIFICATIONS and not all([
            cls.SMTP_USERNAME, cls.SMTP_PASSWORD, cls.EMAIL_FROM
        ]):
            errors.append("Email configuration incomplete when email notifications are enabled")
        
        if cls.ENABLE_LINE_NOTIFICATIONS and not cls.LINE_NOTIFY_TOKEN:
            errors.append("LINE_NOTIFY_TOKEN is required when LINE notifications are enabled")
        
        # Validate numeric ranges
        if cls.DEFAULT_MODEL_CONFIDENCE < 0 or cls.DEFAULT_MODEL_CONFIDENCE > 1:
            errors.append("DEFAULT_MODEL_CONFIDENCE must be between 0 and 1")
        
        if cls.SLEEP_INTERVAL < 0:
            errors.append("PROCESSING_SLEEP_INTERVAL must be positive")
        
        if cls.MAX_WORKERS < 1:
            errors.append("MAX_WORKERS must be at least 1")
        
        return errors
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Get Redis connection configuration."""
        config = {
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'db': cls.REDIS_DB,
            'decode_responses': True,
            'socket_keepalive': True,
            'socket_keepalive_options': {},
        }
        
        if cls.REDIS_PASSWORD:
            config['password'] = cls.REDIS_PASSWORD
        
        return config
    
    @classmethod
    def get_storage_paths(cls) -> Dict[str, str]:
        """Get all storage directory paths."""
        return {
            'base': cls.BASE_SAVE_DIR,
            'raw': os.path.join(cls.BASE_SAVE_DIR, 'raw_images'),
            'annotated': os.path.join(cls.BASE_SAVE_DIR, 'annotated_images'),
            'stream': os.path.join(cls.BASE_SAVE_DIR, 'stream'),
        }


class DevelopmentConfig(Config):
    """Development configuration with debug settings."""
    LOG_LEVEL = 'DEBUG'
    ENABLE_FILE_LOGGING = True


class ProductionConfig(Config):
    """Production configuration with optimized settings."""
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ENABLE_FILE_LOGGING = True
    # Override with production-specific optimizations
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '4'))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '8'))


class TestingConfig(Config):
    """Testing configuration."""
    LOG_LEVEL = 'WARNING'
    ENABLE_FILE_LOGGING = False
    ENABLE_IMAGE_SAVING = False
    ENABLE_EMAIL_NOTIFICATIONS = False
    ENABLE_LINE_NOTIFICATIONS = False


# Configuration mapping
config_mapping = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': Config
}


def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'default').lower()
    config_class = config_mapping.get(env, Config)
    
    # Validate configuration
    errors = config_class.validate_config()
    if errors:
        logger = logging.getLogger(__name__)
        for error in errors:
            logger.error(f"Configuration error: {error}")
        raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
    
    return config_class()
