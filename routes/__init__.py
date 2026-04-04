from flask import Blueprint
from routes.system_routes import system_bp
from routes.student_routes import student_bp
from routes.advisor_routes import advisor_bp
from routes.auth_routes import auth_bp

__all__ = ['system_bp', 'student_bp', 'advisor_bp', 'auth_bp']
