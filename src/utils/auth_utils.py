import bcrypt
import functools
from flask import session, redirect, url_for
from utils.db_utils import get_db


def verify_credentials(email, password):
    """
    Authenticates user using bcrypt password verification.
    Returns: (user_id, role, email, user_data) or (None, None, None, None)
    """
    db = get_db()
    if db is None:
        print("[AUTH] Database connection failed")
        return None, None, None, None

    password_bytes = password.encode('utf-8')
    print(f"[AUTH] Attempting login for: {email}")

    # 1. Check Admin
    admin = db.admins.find_one({"email": email})
    if admin and admin.get("password"):
        stored_hash = admin["password"]
        print(f"[AUTH] Admin found, hash: {stored_hash[:20]}...")
        if stored_hash.startswith('$2b$'):
            if bcrypt.checkpw(password_bytes, stored_hash.encode('utf-8')):
                uid = admin.get("adminId") or str(admin.get("_id"))
                print(f"[AUTH] ? Admin authenticated: {uid}")
                return uid, "admin", email, admin

    # 2. Check Advisor
    advisor = db.advisors.find_one({"email": email})
    if advisor and advisor.get("password"):
        stored_hash = advisor["password"]
        print(f"[AUTH] Advisor found, hash: {stored_hash[:20]}...")
        if stored_hash.startswith('$2b$'):
            if bcrypt.checkpw(password_bytes, stored_hash.encode('utf-8')):
                uid = advisor.get("advisorId") or str(advisor.get("_id"))
                print(f"[AUTH] ? Advisor authenticated: {uid}")
                return uid, "advisor", email, advisor

    # 3. Check Student
    student = db.students.find_one({"email": email})
    if student and student.get("password"):
        stored_hash = student["password"]
        print(f"[AUTH] Student found, hash: {stored_hash[:20]}...")
        if stored_hash.startswith('$2b$'):
            if bcrypt.checkpw(password_bytes, stored_hash.encode('utf-8')):
                uid = student.get("studentId") or str(student.get("_id"))
                print(f"[AUTH] ? Student authenticated: {uid}")
                return uid, "student", email, student

    print("[AUTH] ? Authentication failed - no match found")
    return None, None, None, None


def verify_password(email, password):
    """Alternative authentication function for backward compatibility."""
    user_id, role, user_email, user_data = verify_credentials(email, password)
    return user_id, role, user_data


def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# ============== DECORATORS ==============

def login_required(f):
    """Decorator to require user to be logged in."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            print("[AUTH] No user_id in session. Redirecting to login.")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Decorator to require student role."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'student':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def advisor_required(f):
    """Decorator to require advisor role."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'advisor':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
