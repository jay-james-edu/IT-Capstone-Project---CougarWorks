from flask import Blueprint, render_template, redirect, url_for, session
from functools import wraps

system_bp = Blueprint('system', __name__)

def login_required(roles=None):
    """
    Decorator to check if a user is logged in.
    'roles' can be a single string (e.g., 'student') or a list (e.g., ['admin', 'advisor']).
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            if 'user_id' not in session:
                print(f"DEBUG: No session user_id. Redirect to login.")
                return redirect(url_for('system.login'))


            allowed_roles = [roles] if isinstance(roles, str) else roles


            if allowed_roles:
                if session.get('role') not in allowed_roles:
                    print(f"DEBUG: Access Denied. User Role: {session.get('role')}, Allowed: {allowed_roles}")
                    return redirect(url_for('system.login'))

            print(f"DEBUG: Access Granted for Role: {session.get('role')}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@system_bp.route('/')
def index():
    """Redirect to login page"""
    return redirect(url_for('system.login'))

@system_bp.route('/login')
def login():
    """Serves the login HTML page"""
    return render_template('login.html')



@system_bp.route('/student/dashboard')
@login_required('student')
def student_dashboard():
    """Main student dashboard. Passes student_id to template."""
    return render_template('student_dashboard.html', student_id=session.get('user_id'))

@system_bp.route('/degree-progress')
@login_required('student')
def degree_progress():
    """Degree progress tracker page."""
    return render_template('degree_progress.html', student_id=session.get('user_id'))

@system_bp.route('/remaining-courses')
@login_required('student')
def remaining_courses():
    """View remaining required courses."""
    return render_template('remaining_courses.html', student_id=session.get('user_id'))

@system_bp.route('/gpa-standing')
@login_required('student')
def gpa_standing():
    """View GPA and academic standing."""
    return render_template('gpa_standing.html', student_id=session.get('user_id'))

@system_bp.route('/profile')
@login_required('student')
def profile():
    """Student profile page."""
    return render_template('profile.html', student_id=session.get('user_id'))


@system_bp.route('/admin')
@login_required(['admin', 'advisor'])  
def admin():
    """Main admin portal landing."""
    return render_template('admin.html')

@system_bp.route('/admin/dashboard')
@login_required(['admin', 'advisor'])  
def admin_dashboard():
    """Admin statistics dashboard."""

    return render_template('admin_dashboard.html', user_role=session.get('role'))

@system_bp.route('/search-students')
@login_required(['admin', 'advisor'])
def search_students():
    """Admin page to search/manage students."""
    return render_template('search_students.html')

@system_bp.route('/add-student')
@login_required(['admin']) 
def add_student():
    """Admin page to add a new student."""
    return render_template('add_student.html')

# --- Logout Action --- 

@system_bp.route('/logout')
def logout():
    """Clears session and redirects to login"""
    session.clear()
    return redirect(url_for('system.login'))
