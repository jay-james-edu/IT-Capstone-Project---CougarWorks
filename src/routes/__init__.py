
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.advisor_routes import advisor_bp
from routes.admin_routes import admin_bp
from routes.system_routes import system_bp

__all__ = ['auth_bp', 'student_bp', 'advisor_bp', 'admin_bp', 'system_bp']
