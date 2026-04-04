from werkzeug.security import check_password_hash
from utils.db_utils import get_db

def authenticate_user(role, identifier, password):

    db = get_db()
    if db is None:
        return False

    user = None

    if role == 'student':
        user = db.students.find_one({'studentId': identifier})
    elif role == 'advisor':
        user = db.advisors.find_one({'advisorId': identifier})
    elif role == 'admin':
        user = db.admins.find_one({'username': identifier})
    else:
        return False

    if not user:
        return False

    stored_hash = user.get('personalInfo', {}).get('password', None) or user.get('password', None)

    if stored_hash and check_password_hash(stored_hash, password):
        return {
            'role': role,
            'id': identifier,
            'name': user.get('personalInfo', {}).get('name') or user.get('name')
        }

    return False