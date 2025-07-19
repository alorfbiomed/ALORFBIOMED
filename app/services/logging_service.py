"""
Enhanced Logging Service for Hospital Equipment Maintenance Management System

This service provides comprehensive logging capabilities for both backend and frontend errors,
with structured logging, log rotation, and centralized error management.
"""

import logging
import logging.handlers
import os
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, session, g
import sys


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output"""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'module': record.name,
            'message': record.getMessage(),
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add request context if available
        try:
            if request:
                log_entry['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'endpoint': request.endpoint,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'referrer': request.referrer
                }
                
                # Add user context if available
                if hasattr(g, 'current_user') and g.current_user:
                    log_entry['user'] = {
                        'id': getattr(g.current_user, 'id', None),
                        'username': getattr(g.current_user, 'username', None),
                        'role': getattr(g.current_user, 'role', None)
                    }
                elif 'user_id' in session:
                    log_entry['user'] = {
                        'id': session.get('user_id'),
                        'username': session.get('username'),
                        'role': session.get('role')
                    }
        except RuntimeError:
            # Outside of request context
            pass
        
        # Add custom fields from record
        for key, value in record.__dict__.items():
            if key.startswith('custom_'):
                log_entry[key[7:]] = value  # Remove 'custom_' prefix
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))


class LoggingService:
    """Centralized logging service for the application"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.setup_logging()
            self._initialized = True
    
    def setup_logging(self):
        """Initialize logging configuration"""
        # Ensure logs directory exists
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatters
        structured_formatter = StructuredFormatter()
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Error log handler (structured JSON format)
        error_log_path = os.path.join(log_dir, 'error.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(structured_formatter)
        
        # Application log handler (human-readable format)
        app_log_path = os.path.join(log_dir, 'app.log')
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(simple_formatter)
        
        # Debug log handler (development only)
        debug_log_path = os.path.join(log_dir, 'debug.log')
        debug_handler = logging.handlers.RotatingFileHandler(
            debug_log_path,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(structured_formatter)
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers to root logger
        root_logger.addHandler(error_handler)
        root_logger.addHandler(app_handler)
        root_logger.addHandler(debug_handler)
        root_logger.addHandler(console_handler)
        
        # Configure specific loggers
        self.setup_specific_loggers()
    
    def setup_specific_loggers(self):
        """Configure specific loggers for different components"""
        # Database operations logger
        db_logger = logging.getLogger('database')
        db_logger.setLevel(logging.INFO)
        
        # API operations logger
        api_logger = logging.getLogger('api')
        api_logger.setLevel(logging.INFO)
        
        # Email service logger
        email_logger = logging.getLogger('email')
        email_logger.setLevel(logging.INFO)
        
        # Authentication logger
        auth_logger = logging.getLogger('auth')
        auth_logger.setLevel(logging.INFO)
        
        # Frontend errors logger
        frontend_logger = logging.getLogger('frontend')
        frontend_logger.setLevel(logging.ERROR)
    
    @staticmethod
    def log_error(message: str, exception: Optional[Exception] = None, 
                  context: Optional[Dict[str, Any]] = None, logger_name: str = 'app'):
        """Log an error with optional context"""
        logger = logging.getLogger(logger_name)
        
        # Add context as custom fields
        if context:
            for key, value in context.items():
                setattr(logger, f'custom_{key}', value)
        
        if exception:
            logger.error(message, exc_info=exception)
        else:
            logger.error(message)
        
        # Clean up custom fields
        if context:
            for key in context.keys():
                if hasattr(logger, f'custom_{key}'):
                    delattr(logger, f'custom_{key}')
    
    @staticmethod
    def log_warning(message: str, context: Optional[Dict[str, Any]] = None, 
                   logger_name: str = 'app'):
        """Log a warning with optional context"""
        logger = logging.getLogger(logger_name)
        
        if context:
            for key, value in context.items():
                setattr(logger, f'custom_{key}', value)
        
        logger.warning(message)
        
        if context:
            for key in context.keys():
                if hasattr(logger, f'custom_{key}'):
                    delattr(logger, f'custom_{key}')
    
    @staticmethod
    def log_info(message: str, context: Optional[Dict[str, Any]] = None, 
                logger_name: str = 'app'):
        """Log an info message with optional context"""
        logger = logging.getLogger(logger_name)
        
        if context:
            for key, value in context.items():
                setattr(logger, f'custom_{key}', value)
        
        logger.info(message)
        
        if context:
            for key in context.keys():
                if hasattr(logger, f'custom_{key}'):
                    delattr(logger, f'custom_{key}')
    
    @staticmethod
    def log_debug(message: str, context: Optional[Dict[str, Any]] = None, 
                 logger_name: str = 'app'):
        """Log a debug message with optional context"""
        logger = logging.getLogger(logger_name)
        
        if context:
            for key, value in context.items():
                setattr(logger, f'custom_{key}', value)
        
        logger.debug(message)
        
        if context:
            for key in context.keys():
                if hasattr(logger, f'custom_{key}'):
                    delattr(logger, f'custom_{key}')


# Initialize logging service
logging_service = LoggingService()
