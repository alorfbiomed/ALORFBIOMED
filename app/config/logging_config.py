"""
Logging Configuration for Hospital Equipment Maintenance Management System

This module provides centralized logging configuration with different settings
for development and production environments.
"""

import os
from pathlib import Path


class LoggingConfig:
    """Configuration class for logging settings"""
    
    # Base logging directory
    LOG_DIR = Path(__file__).parent.parent / 'logs'
    
    # Log file paths
    ERROR_LOG_PATH = LOG_DIR / 'error.log'
    APP_LOG_PATH = LOG_DIR / 'app.log'
    DEBUG_LOG_PATH = LOG_DIR / 'debug.log'
    ACCESS_LOG_PATH = LOG_DIR / 'access.log'
    
    # Log rotation settings
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    DEBUG_MAX_SIZE = 5 * 1024 * 1024  # 5MB for debug logs
    DEBUG_BACKUP_COUNT = 3
    
    # Log levels
    DEFAULT_LOG_LEVEL = 'INFO'
    DEBUG_LOG_LEVEL = 'DEBUG'
    ERROR_LOG_LEVEL = 'ERROR'
    
    # Environment-specific settings
    DEVELOPMENT_LOG_LEVEL = 'DEBUG'
    PRODUCTION_LOG_LEVEL = 'INFO'
    
    # Frontend logging settings
    FRONTEND_LOG_ENABLED = True
    FRONTEND_LOG_LEVEL = 'ERROR'
    FRONTEND_MAX_QUEUE_SIZE = 50
    FRONTEND_RETRY_ATTEMPTS = 3
    FRONTEND_RETRY_DELAY = 1000  # milliseconds
    
    # Sensitive data filtering
    SENSITIVE_FIELDS = [
        'password', 'token', 'secret', 'key', 'auth',
        'credential', 'session', 'cookie'
    ]
    
    # Log format settings
    STRUCTURED_LOG_FORMAT = True
    INCLUDE_REQUEST_CONTEXT = True
    INCLUDE_USER_CONTEXT = True
    INCLUDE_PERFORMANCE_METRICS = True
    
    # Component-specific logging
    COMPONENT_LOG_LEVELS = {
        'database': 'INFO',
        'api': 'INFO',
        'email': 'INFO',
        'auth': 'INFO',
        'frontend': 'ERROR',
        'scheduler': 'INFO',
        'backup': 'INFO'
    }
    
    @classmethod
    def get_log_level(cls, component: str = None) -> str:
        """Get log level for a specific component or default"""
        if component and component in cls.COMPONENT_LOG_LEVELS:
            return cls.COMPONENT_LOG_LEVELS[component]
        
        # Check environment
        env = os.getenv('FLASK_ENV', 'production').lower()
        if env == 'development':
            return cls.DEVELOPMENT_LOG_LEVEL
        else:
            return cls.PRODUCTION_LOG_LEVEL
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return os.getenv('FLASK_ENV', 'production').lower() == 'development'
    
    @classmethod
    def should_log_debug(cls) -> bool:
        """Check if debug logging should be enabled"""
        return cls.is_development() or os.getenv('DEBUG_LOGGING', 'false').lower() == 'true'
    
    @classmethod
    def get_log_retention_days(cls) -> int:
        """Get log retention period in days"""
        return int(os.getenv('LOG_RETENTION_DAYS', '30'))
    
    @classmethod
    def is_frontend_logging_enabled(cls) -> bool:
        """Check if frontend logging is enabled"""
        return cls.FRONTEND_LOG_ENABLED and os.getenv('FRONTEND_LOGGING', 'true').lower() == 'true'


# Export configuration instance
logging_config = LoggingConfig()
