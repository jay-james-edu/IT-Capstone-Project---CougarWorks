from flask import Blueprint, request, redirect, url_for, session, render_template
from utils.auth_utils import verify_credentials

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        print(f"[LOGIN] Form submitted - Email: {email}")

        if email and password:
            user_id, role, user_email, user_data = verify_credentials(email, password)

            if user_data:
                session.clear()
                session['user_id'] = user_id
                session['role'] = role
                session['email'] = user_email
                session.permanent = True
                print(f"[LOGIN] Session set - user_id: {user_id}, role: {role}")
                return redirect(url_for('system.dashboard'))
            else:
                error = "Invalid email or password"
                print("[LOGIN] Authentication failed")
        else:
            error = "Please enter both email and password"

    return render_template('login.html', error=error)


@auth_bp.route('/logout')
def logout():
    session.clear()
    print("[LOGIN] Session cleared, redirecting to login")
    return redirect(url_for('auth.login'))
