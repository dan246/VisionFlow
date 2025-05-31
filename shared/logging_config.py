"""
Centralized Logging Configuration
Provides consistent logging setup across all VisionFlow services.
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if hasattr(record, 'color') and record.color:
            log_color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{log_color}{record.levelname}{self.RESET}"
            record.msg = f"{log_color}{record.msg}{self.RESET}"
        return super().format(record)


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_dir: str = "logs",
    console_output: bool = True,
    file_output: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup comprehensive logging configuration for a service
    
    Args:
        service_name: Name of the service (used in log filename)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        console_output: Whether to output to console
        file_output: Whether to output to file
        max_file_size: Maximum size per log file in bytes
        backup_count: Number of backup log files to keep
    
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    if file_output and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Get or create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    colored_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Use colored formatter for console if terminal supports it
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            console_handler.setFormatter(colored_formatter)
        else:
            console_handler.setFormatter(simple_formatter)
            
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output:
        log_filename = os.path.join(log_dir, f"{service_name}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_filename,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File gets all levels
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Error file handler (separate file for errors and above)
    if file_output:
        error_filename = os.path.join(log_dir, f"{service_name}_error.log")
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_filename,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info(f"Logging configured for service: {service_name}")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Console output: {console_output}")
    logger.info(f"File output: {file_output}")
    
    return logger


def get_performance_logger(service_name: str) -> logging.Logger:
    """Get a dedicated logger for performance metrics"""
    perf_logger = logging.getLogger(f"{service_name}.performance")
    
    if not perf_logger.handlers:
        # Performance log formatter
        perf_formatter = logging.Formatter(
            fmt='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Performance file handler
        perf_filename = os.path.join("logs", f"{service_name}_performance.log")
        perf_handler = logging.handlers.RotatingFileHandler(
            filename=perf_filename,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        perf_handler.setFormatter(perf_formatter)
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        perf_logger.propagate = False
    
    return perf_logger


class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, logger: logging.Logger, operation_name: str):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.logger.info(f"{self.operation_name}: {duration:.3f}s")


# Convenience function for backward compatibility
def configure_logging(service_name: str = "VisionFlow", **kwargs) -> logging.Logger:
    """Backward compatible logging configuration"""
    return setup_logging(service_name, **kwargs)


# Example usage patterns
if __name__ == "__main__":
    # Test the logging configuration
    logger = setup_logging("test_service", log_level="DEBUG")
    perf_logger = get_performance_logger("test_service")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test performance timing
    with PerformanceTimer(perf_logger, "test_operation"):
        import time
        time.sleep(0.1)
    
    print("Logging test completed. Check logs/ directory for output files.")
