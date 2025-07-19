"""
Logging Routes for Frontend Error Reporting

This module provides endpoints for frontend JavaScript errors to be sent to the backend
for centralized logging and monitoring.
"""

from flask import Blueprint, request, jsonify, session, g
from app.services.logging_service import LoggingService
import json
from datetime import datetime

logging_bp = Blueprint('logging', __name__, url_prefix='/api/logging')


@logging_bp.route('/frontend-error', methods=['POST'])
def log_frontend_error():
    """
    Endpoint to receive frontend JavaScript errors and log them centrally
    
    Expected payload:
    {
        "message": "Error message",
        "source": "script.js",
        "line": 123,
        "column": 45,
        "error": "TypeError: Cannot read property...",
        "stack": "Error stack trace",
        "url": "current page URL",
        "userAgent": "browser user agent",
        "timestamp": "ISO timestamp",
        "context": {
            "action": "bulk_delete",
            "component": "equipment_list",
            "additional_data": {}
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract error information
        error_message = data.get('message', 'Unknown frontend error')
        source = data.get('source', 'unknown')
        line = data.get('line', 0)
        column = data.get('column', 0)
        error_type = data.get('error', 'Unknown Error')
        stack_trace = data.get('stack', '')
        page_url = data.get('url', '')
        user_agent = data.get('userAgent', '')
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        context = data.get('context', {})
        
        # Build comprehensive error context
        error_context = {
            'source_file': source,
            'line_number': line,
            'column_number': column,
            'error_type': error_type,
            'stack_trace': stack_trace,
            'page_url': page_url,
            'user_agent': user_agent,
            'client_timestamp': timestamp,
            'server_timestamp': datetime.utcnow().isoformat(),
            'session_id': session.get('session_id', 'anonymous'),
            'user_context': context
        }
        
        # Add user information if available
        if hasattr(g, 'current_user') and g.current_user:
            error_context['user_id'] = getattr(g.current_user, 'id', None)
            error_context['username'] = getattr(g.current_user, 'username', None)
        elif 'user_id' in session:
            error_context['user_id'] = session.get('user_id')
            error_context['username'] = session.get('username')
        
        # Log the frontend error
        LoggingService.log_error(
            f"Frontend Error: {error_message}",
            context=error_context,
            logger_name='frontend'
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Error logged successfully'
        }), 200
        
    except Exception as e:
        # Log the logging error (meta-logging)
        LoggingService.log_error(
            f"Failed to log frontend error: {str(e)}",
            exception=e,
            context={'original_request_data': request.get_json()},
            logger_name='logging_system'
        )
        
        return jsonify({
            'status': 'error',
            'message': 'Failed to log error'
        }), 500


@logging_bp.route('/frontend-warning', methods=['POST'])
def log_frontend_warning():
    """
    Endpoint to receive frontend warnings and log them
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        warning_message = data.get('message', 'Unknown frontend warning')
        context = data.get('context', {})
        
        # Build warning context
        warning_context = {
            'page_url': data.get('url', ''),
            'user_agent': data.get('userAgent', ''),
            'timestamp': data.get('timestamp', datetime.utcnow().isoformat()),
            'user_context': context
        }
        
        # Add user information if available
        if hasattr(g, 'current_user') and g.current_user:
            warning_context['user_id'] = getattr(g.current_user, 'id', None)
            warning_context['username'] = getattr(g.current_user, 'username', None)
        elif 'user_id' in session:
            warning_context['user_id'] = session.get('user_id')
            warning_context['username'] = session.get('username')
        
        # Log the frontend warning
        LoggingService.log_warning(
            f"Frontend Warning: {warning_message}",
            context=warning_context,
            logger_name='frontend'
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Warning logged successfully'
        }), 200
        
    except Exception as e:
        LoggingService.log_error(
            f"Failed to log frontend warning: {str(e)}",
            exception=e,
            logger_name='logging_system'
        )
        
        return jsonify({
            'status': 'error',
            'message': 'Failed to log warning'
        }), 500


@logging_bp.route('/frontend-info', methods=['POST'])
def log_frontend_info():
    """
    Endpoint to receive frontend info messages and log them
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        info_message = data.get('message', 'Frontend info')
        context = data.get('context', {})
        
        # Build info context
        info_context = {
            'page_url': data.get('url', ''),
            'user_agent': data.get('userAgent', ''),
            'timestamp': data.get('timestamp', datetime.utcnow().isoformat()),
            'user_context': context
        }
        
        # Add user information if available
        if hasattr(g, 'current_user') and g.current_user:
            info_context['user_id'] = getattr(g.current_user, 'id', None)
            info_context['username'] = getattr(g.current_user, 'username', None)
        elif 'user_id' in session:
            info_context['user_id'] = session.get('user_id')
            info_context['username'] = session.get('username')
        
        # Log the frontend info
        LoggingService.log_info(
            f"Frontend Info: {info_message}",
            context=info_context,
            logger_name='frontend'
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Info logged successfully'
        }), 200
        
    except Exception as e:
        LoggingService.log_error(
            f"Failed to log frontend info: {str(e)}",
            exception=e,
            logger_name='logging_system'
        )
        
        return jsonify({
            'status': 'error',
            'message': 'Failed to log info'
        }), 500


@logging_bp.route('/health', methods=['GET'])
def logging_health():
    """Health check endpoint for logging service"""
    try:
        # Test logging functionality
        LoggingService.log_info("Logging service health check", logger_name='health')
        
        return jsonify({
            'status': 'healthy',
            'service': 'logging',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'logging',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
