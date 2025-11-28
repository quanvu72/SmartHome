"""
Authentication Decorators - Decorator cho Flask routes
"""

from functools import wraps
from flask import request, jsonify, redirect, url_for, session


def login_required(f):
    """
    Decorator yeu cau dang nhap de truy cap route
    
    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return 'Protected content'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Kiem tra session token trong cookie hoac header
        session_token = request.cookies.get('session_token')
        
        if not session_token:
            # Kiem tra trong Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                session_token = auth_header[7:]
        
        if not session_token:
            # Neu la API request, tra ve JSON
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401
            # Neu la web request, redirect den trang login
            else:
                return redirect(url_for('login'))
        
        # Validate session token
        from flask import current_app
        auth_manager = current_app.config.get('AUTH_MANAGER')
        
        if not auth_manager:
            return jsonify({
                'success': False,
                'error': 'Authentication not configured'
            }), 500
        
        user_info = auth_manager.validate_session(session_token)
        
        if not user_info:
            # Session khong hop le hoac da het han
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired session'
                }), 401
            else:
                return redirect(url_for('login'))
        
        # Luu user_info vao request context
        request.user = user_info
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    Decorator yeu cau quyen admin de truy cap route
    
    Usage:
        @app.route('/admin')
        @admin_required
        def admin_route():
            return 'Admin only content'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Kiem tra login truoc
        session_token = request.cookies.get('session_token')
        
        if not session_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                session_token = auth_header[7:]
        
        if not session_token:
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401
            else:
                return redirect(url_for('login'))
        
        # Validate session va kiem tra role
        from flask import current_app
        auth_manager = current_app.config.get('AUTH_MANAGER')
        
        if not auth_manager:
            return jsonify({
                'success': False,
                'error': 'Authentication not configured'
            }), 500
        
        user_info = auth_manager.validate_session(session_token)
        
        if not user_info:
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired session'
                }), 401
            else:
                return redirect(url_for('login'))
        
        if user_info.get('role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Admin privileges required'
                }), 403
            else:
                return 'Access denied - Admin only', 403
        
        # Luu user_info vao request context
        request.user = user_info
        
        return f(*args, **kwargs)
    
    return decorated_function
