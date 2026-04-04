from flask import Blueprint, jsonify, request, session
from utils.auth_utils import authenticate_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json

    role = data.get('role')         # 'student', 'advisor', 'admin'
    identifier = data.get('id')     # studentId, advisorId, or username
    password = data.get('password')

    if not all([role, identifier, password]):
        return jsonify({'error': 'Missing required fields'}), 400

    user_data = authenticate_user(role, identifier, password)

    if user_data:
        session['user_id'] = identifier
        session['role'] = role

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user_data,
            'redirect': get_redirect_page(role)
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

def get_redirect_page(role):
    if role == 'student':
        return '/student/dashboard'
    elif role == 'advisor':
        return '/admin/dashboard' 
    elif role == 'admin':
        return '/admin/dashboard'
    return '/'
