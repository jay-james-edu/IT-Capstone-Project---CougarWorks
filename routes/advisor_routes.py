from flask import Blueprint, jsonify
from utils.db_utils import parse_json, get_db

advisor_bp = Blueprint('advisors', __name__)

@advisor_bp.route('/api/advisors', methods=['GET'])
def get_all_advisors():
    """Get all advisors with basic information"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database not connected'}), 500

        if 'advisors' not in db.list_collection_names():
            return jsonify({'error': 'Advisors collection not found'}), 404

        advisors = list(db.advisors.find(
            {},
            {
                'advisorId': 1,
                'personalInfo.firstName': 1,
                'personalInfo.lastName': 1,
                'personalInfo.email': 1,
                'department': 1,
                'title': 1
            }
        ))

        return jsonify(parse_json(advisors))
    except Exception as e:
        print(f"\n❌ Error in /api/advisors: {str(e)}")
        return jsonify({'error': str(e)}), 500

@advisor_bp.route('/api/advisors/<advisor_id>', methods=['GET'])
def get_advisor_details(advisor_id):
    """Get detailed information for a specific advisor"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database not connected'}), 500

        advisor = db.advisors.find_one({'advisorId': advisor_id})

        if not advisor:
            return jsonify({'error': 'Advisor not found'}), 404

        return jsonify(parse_json(advisor))
    except Exception as e:
        print(f"\n❌ Error in /api/advisors/{advisor_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@advisor_bp.route('/api/advisors/<advisor_id>/students', methods=['GET'])
def get_advisor_students(advisor_id):
    """Get all students assigned to a specific advisor"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database not connected'}), 500

        students = list(db.students.find(
            {'advisorId': advisor_id},
            {
                'studentId': 1,
                'personalInfo.firstName': 1,
                'personalInfo.lastName': 1,
                'personalInfo.email': 1,
                'academicInfo.major': 1,
                'academicInfo.standing': 1,
                'enrollmentStatus': 1
            }
        ))

        return jsonify(parse_json(students))
    except Exception as e:
        print(f"\n❌ Error in /api/advisors/{advisor_id}/students: {str(e)}")
        return jsonify({'error': str(e)}), 500
