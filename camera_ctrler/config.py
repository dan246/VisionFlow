# -*- coding: utf-8 -*-
"""
Camera Controller Service Configuration
Handles environment variables and configuration settings for the camera controller service.
"""

import os
import logging
from typing import Dict, Any, Optional


class CameraControllerConfig:
    """Configuration class for camera controller service."""
    
    # Flask Configuration
    DEBUG: bool = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    HOST: str = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT: int = int(os.getenv('FLASK_PORT', '5001'))
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD')
    
    # Camera Configuration
    CAMERA_FETCH_INTERVAL: float = float(os.getenv('CAMERA_FETCH_INTERVAL', '0.1'))
    CAMERA_TIMEOUT: int = int(os.getenv('CAMERA_TIMEOUT', '30'))
    MAX_RETRIES: int = int(os.getenv('CAMERA_MAX_RETRIES', '3'))
    
    # Streaming Configuration
    STREAM_SLEEP_INTERVAL: float = float(os.getenv('STREAM_SLEEP_INTERVAL', '0.1'))
    
    # Image Processing
    IMAGE_QUALITY: int = int(os.getenv('IMAGE_QUALITY', '85'))
    IMAGE_FORMAT: str = os.getenv('IMAGE_FORMAT', 'JPEG')
    MAX_IMAGE_SIZE: tuple = (
        int(os.getenv('MAX_IMAGE_WIDTH', '1920')),
        int(os.getenv('MAX_IMAGE_HEIGHT', '1080'))
    )
    
    # Storage Configuration
    ENABLE_IMAGE_SAVING: bool = os.getenv('ENABLE_IMAGE_SAVING', 'false').lower() == 'true'
    SAVE_PATH: str = os.getenv('SAVE_PATH', '/app/images')
    RETENTION_HOURS: int = int(os.getenv('IMAGE_RETENTION_HOURS', '24'))
    
    # Security
    CORS_ORIGINS: list = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ENABLE_FILE_LOGGING: bool = os.getenv('ENABLE_FILE_LOGGING', 'true').lower() == 'true'
    LOG_FILE_PATH: str = os.getenv('LOG_FILE_PATH', 'logs/camera_controller.log')
    
    # Performance
    WORKER_THREADS: int = int(os.getenv('WORKER_THREADS', '4'))
    FRAME_BUFFER_SIZE: int = int(os.getenv('FRAME_BUFFER_SIZE', '5'))
    
    # Monitoring
    HEALTH_CHECK_INTERVAL: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
    STATUS_UPDATE_INTERVAL: int = int(os.getenv('STATUS_UPDATE_INTERVAL', '5'))
    
    @classmethod
    def validate_config(cls) -> list:
        """Validate configuration and return any errors."""
        errors = []
        
        # Validate port range
        if not (1 <= cls.PORT <= 65535):
            errors.append("PORT must be between 1 and 65535")
        
        # Validate intervals
        if cls.CAMERA_FETCH_INTERVAL <= 0:
            errors.append("CAMERA_FETCH_INTERVAL must be positive")
        
        if cls.CAMERA_TIMEOUT <= 0:
            errors.append("CAMERA_TIMEOUT must be positive")
        
        # Validate image quality
        if not (1 <= cls.IMAGE_QUALITY <= 100):
            errors.append("IMAGE_QUALITY must be between 1 and 100")
        
        # Validate worker threads
        if cls.WORKER_THREADS < 1:
            errors.append("WORKER_THREADS must be at least 1")
        
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
            # 'retry_on_timeout': True,
        }
        
        if cls.REDIS_PASSWORD:
            config['password'] = cls.REDIS_PASSWORD
        
        return config
    
    @classmethod
    def get_flask_config(cls) -> Dict[str, Any]:
        """Get Flask application configuration."""
        return {
            'DEBUG': cls.DEBUG,
            'HOST': cls.HOST,
            'PORT': cls.PORT,
        }
    
    @classmethod
    def setup_logging(cls) -> None:
        """Setup logging configuration."""
        # Create logs directory if it doesn't exist
        if cls.ENABLE_FILE_LOGGING:
            log_dir = os.path.dirname(cls.LOG_FILE_PATH)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
        
        # Configure logging
        handlers = [logging.StreamHandler()]
        
        if cls.ENABLE_FILE_LOGGING:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                cls.LOG_FILE_PATH,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            handlers.append(file_handler)
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format=cls.LOG_FORMAT,
            handlers=handlers
        )


# Create configuration instance
config = CameraControllerConfig()

# Validate configuration on import
config_errors = config.validate_config()
if config_errors:
    logger = logging.getLogger(__name__)
    for error in config_errors:
        logger.error(f"Configuration error: {error}")
    raise ValueError(f"Configuration validation failed: {', '.join(config_errors)}")
