from flask import Blueprint, jsonify, request
from utils.db_utils import get_db
from utils.degree_utils import calculate_degree_progress

student_bp = Blueprint('student', __name__)

@student_bp.route('/api/students/<student_id>/degree-progress-summary')
def degree_progress_summary(student_id):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database error"}), 500

    student = db.students.find_one({"studentId": student_id})
    if not student:
        return jsonify({"error": "Student not found"}), 404

    major = student.get("academicInfo", {}).get("major", "Unknown")
    data = calculate_degree_progress(student_id, major)

    if not data or not isinstance(data, dict):
        data = {}

    if 'overallProgress' not in data:
        data['overallProgress'] = {
            "percentage": 0,
            "completedCredits": 0,
            "requiredCredits": 120,
            "programName": major
        }
    elif 'requiredCredits' not in data['overallProgress']:
        data['overallProgress']['requiredCredits'] = 120

    if 'categoryProgress' not in data:
        data['categoryProgress'] = []

    return jsonify(data)


@student_bp.route('/api/students/<student_id>/what-if')
def what_if_analysis(student_id):
    major_alias = request.args.get('major')

    if not major_alias:
        return jsonify({"error": "Major required"}), 400

    data = calculate_degree_progress(student_id, major_alias)

    if data is None:
        return jsonify({
            "overallProgress": {
                "percentage": 0,
                "completedCredits": 0,
                "requiredCredits": 120,
                "programName": "Unknown Major"
            },
            "categoryProgress": []
        })

    if 'overallProgress' in data and 'requiredCredits' not in data['overallProgress']:
        data['overallProgress']['requiredCredits'] = 120

    return jsonify(data)
