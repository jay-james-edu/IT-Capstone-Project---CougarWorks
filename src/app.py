import os
from datetime import datetime
from flask import Flask, redirect, url_for, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from utils.db_utils import get_db

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

from routes import auth_bp, system_bp, student_bp, advisor_bp, admin_bp


@app.template_filter('datetimeformat')
def datetimeformat(value, fmt='%b %d, %Y %I:%M %p'):
    """Format datetimes safely in templates."""
    if not value:
        return 'N/A'
    if isinstance(value, datetime):
        return value.strftime(fmt)
    return str(value)


# Blueprint-style route layout. Prefixes live here, not inside route files.
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(advisor_bp, url_prefix='/advisor')
# Student API endpoints are served through system_bp to keep route behavior consistent.
app.register_blueprint(system_bp)


@app.route('/')
def index():
    return redirect(url_for('auth.login'))


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    print("\n🚀 Starting CougarWorks Server...")
    print("🐳 Environment: Docker (0.0.0.0)\n")

    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
