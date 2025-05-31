# -*- coding: utf-8 -*-
"""
Redis Worker Configuration
Enhanced configuration management for Redis workers.
"""

import os
import logging
from typing import Dict, Any, Optional


class RedisWorkerConfig:
    """Configuration class for Redis workers."""
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD')
    
    # Worker Configuration
    WORKER_ID: int = int(os.getenv('WORKER_ID', '1'))
    NUM_WORKERS: int = int(os.getenv('NUM_WORKERS', '3'))
    WORKER_TIMEOUT: int = int(os.getenv('WORKER_TIMEOUT', '30'))
    
    # Camera Configuration
    RECONNECT_INTERVAL: int = int(os.getenv('RECONNECT_INTERVAL', '30'))
    FRAME_FETCH_INTERVAL: float = float(os.getenv('FRAME_FETCH_INTERVAL', '0.1'))
    STATUS_UPDATE_INTERVAL: int = int(os.getenv('STATUS_UPDATE_INTERVAL', '5'))
    
    # Video Processing
    VIDEO_TIMEOUT: int = int(os.getenv('VIDEO_TIMEOUT', '30'))
    FRAME_BUFFER_SIZE: int = int(os.getenv('FRAME_BUFFER_SIZE', '5'))
    MAX_FRAME_WIDTH: int = int(os.getenv('MAX_FRAME_WIDTH', '1920'))
    MAX_FRAME_HEIGHT: int = int(os.getenv('MAX_FRAME_HEIGHT', '1080'))
    
    # File Storage
    ENABLE_FILE_STORAGE: bool = os.getenv('ENABLE_FILE_STORAGE', 'false').lower() == 'true'
    STORAGE_PATH: str = os.getenv('STORAGE_PATH', '/app/storage')
    RETENTION_HOURS: int = int(os.getenv('RETENTION_HOURS', '24'))
    
    # Performance
    MAX_CONCURRENT_CAMERAS: int = int(os.getenv('MAX_CONCURRENT_CAMERAS', '10'))
    MEMORY_LIMIT_MB: int = int(os.getenv('MEMORY_LIMIT_MB', '512'))
    
    # Error Handling
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY: int = int(os.getenv('RETRY_DELAY', '5'))
    ERROR_THRESHOLD: int = int(os.getenv('ERROR_THRESHOLD', '10'))
    MAX_CONSECUTIVE_FAILURES: int = int(os.getenv('MAX_CONSECUTIVE_FAILURES', '10'))
    
    # Monitoring
    HEALTH_CHECK_INTERVAL: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))
    METRICS_ENABLED: bool = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
    PERFORMANCE_LOGGING: bool = os.getenv('PERFORMANCE_LOGGING', 'false').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - Worker%(worker_id)s - %(levelname)s - %(message)s')
    ENABLE_FILE_LOGGING: bool = os.getenv('ENABLE_FILE_LOGGING', 'true').lower() == 'true'
    LOG_FILE_PATH: str = os.getenv('LOG_FILE_PATH', 'logs/redis_worker.log')
    LOG_FILE_MAX_BYTES: int = int(os.getenv('LOG_FILE_MAX_BYTES', '10485760'))  # 10MB
    LOG_FILE_BACKUP_COUNT: int = int(os.getenv('LOG_FILE_BACKUP_COUNT', '5'))
    
    @classmethod
    def validate_config(cls) -> list:
        """Validate configuration and return any errors."""
        errors = []
        
        # Validate worker configuration
        if cls.WORKER_ID < 1:
            errors.append("WORKER_ID must be at least 1")
        
        if cls.NUM_WORKERS < 1:
            errors.append("NUM_WORKERS must be at least 1")
        
        if cls.WORKER_ID > cls.NUM_WORKERS:
            errors.append("WORKER_ID cannot be greater than NUM_WORKERS")
        
        # Validate intervals
        if cls.RECONNECT_INTERVAL <= 0:
            errors.append("RECONNECT_INTERVAL must be positive")
        
        if cls.FRAME_FETCH_INTERVAL <= 0:
            errors.append("FRAME_FETCH_INTERVAL must be positive")
        
        # Validate performance limits
        if cls.MAX_CONCURRENT_CAMERAS < 1:
            errors.append("MAX_CONCURRENT_CAMERAS must be at least 1")
        
        if cls.MEMORY_LIMIT_MB < 64:
            errors.append("MEMORY_LIMIT_MB must be at least 64")
        
        # Validate frame dimensions
        if cls.MAX_FRAME_WIDTH < 320 or cls.MAX_FRAME_HEIGHT < 240:
            errors.append("Frame dimensions must be at least 320x240")
        
        return errors
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Get Redis connection configuration."""
        config = {
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'db': cls.REDIS_DB,
            'decode_responses': False,  # Keep as bytes for image data
            'socket_keepalive': True,
            'socket_keepalive_options': {},
            # 'retry_on_timeout': True,
            'socket_timeout': cls.WORKER_TIMEOUT,
        }
        
        if cls.REDIS_PASSWORD:
            config['password'] = cls.REDIS_PASSWORD
        
        return config
    
    @classmethod
    def get_opencv_config(cls) -> Dict[str, Any]:
        """Get OpenCV configuration."""
        return {
            'buffer_size': cls.FRAME_BUFFER_SIZE,
            'timeout': cls.VIDEO_TIMEOUT,
            'max_width': cls.MAX_FRAME_WIDTH,
            'max_height': cls.MAX_FRAME_HEIGHT,
        }
    
    @classmethod
    def setup_logging(cls) -> logging.Logger:
        """Setup logging configuration for worker."""
        # Create logs directory if it doesn't exist
        if cls.ENABLE_FILE_LOGGING:
            log_dir = os.path.dirname(cls.LOG_FILE_PATH)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
        
        # Configure logging
        logger = logging.getLogger(f'RedisWorker{cls.WORKER_ID}')
        logger.setLevel(getattr(logging, cls.LOG_LEVEL.upper()))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            cls.LOG_FORMAT % {'worker_id': cls.WORKER_ID}
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        if cls.ENABLE_FILE_LOGGING:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                cls.LOG_FILE_PATH,
                maxBytes=cls.LOG_FILE_MAX_BYTES,
                backupCount=cls.LOG_FILE_BACKUP_COUNT
            )
            file_formatter = logging.Formatter(
                cls.LOG_FORMAT % {'worker_id': cls.WORKER_ID}
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    @classmethod
    def get_worker_name(cls) -> str:
        """Get formatted worker name."""
        return f"Worker{cls.WORKER_ID:02d}"
    
    @classmethod
    def get_storage_paths(cls) -> Dict[str, str]:
        """Get storage directory paths."""
        base_path = cls.STORAGE_PATH
        return {
            'base': base_path,
            'frames': os.path.join(base_path, 'frames'),
            'logs': os.path.join(base_path, 'logs'),
            'temp': os.path.join(base_path, 'temp'),
        }


# Create configuration instance
config = RedisWorkerConfig()

# Validate configuration on import
config_errors = config.validate_config()
if config_errors:
    print(f"Configuration validation failed: {', '.join(config_errors)}")
    # Don't exit here as this might be imported in different contexts
