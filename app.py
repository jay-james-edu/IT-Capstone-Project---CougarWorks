import os
from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv

from routes import system_bp, student_bp, advisor_bp, auth_bp
from utils.db_utils import connect_to_mongo

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

app.register_blueprint(system_bp)
app.register_blueprint(student_bp)
app.register_blueprint(advisor_bp)
app.register_blueprint(auth_bp)


@app.before_request
def before_request():
    if not connect_to_mongo():
        pass 

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Starting Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
