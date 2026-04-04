from flask import Blueprint, jsonify, request
from utils.db_utils import parse_json, get_db
from utils.simulation_utils import WhatIfSimulationService
from utils.gpa_utils import GPAService, determine_standing

student_bp = Blueprint('students', __name__)

@student_bp.route('/api/students', methods=['GET'])
def get_all_students():
    """Returns list of all students"""
    try:
        db = get_db()
        if db is None: return jsonify({'error': 'Database Connection Error'}), 500

        students = list(db.students.find({}, {
            'studentId': 1, 'personalInfo.firstName': 1, 
            'personalInfo.lastName': 1, 'academicInfo.major': 1,
            'academicInfo.gpa': 1, 'academicInfo.creditsEarned': 1
        }))
        return jsonify(parse_json(students))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/api/students/<student_id>')
def get_student_details(student_id):
    """Get full details for a specific student ID"""
    try:
        db = get_db()
        student = db.students.find_one({'studentId': student_id})
        if not student: return jsonify({'error': 'Student not found'}), 404

        progress = db.academicprogress.find_one({'studentId': student_id})
        student['progress'] = progress

        return jsonify(parse_json(student))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_bp.route('/api/students/<student_id>/simulate', methods=['GET'])
def simulate_major_change(student_id):
    """
    What-If Analysis: Check progress if student changes major.
    Usage: /api/students/123/simulate?major=Biology
    """
    try:
        new_major = request.args.get('major')
        if not new_major: return jsonify({'error': 'Major parameter required'}), 400

        db = get_db()
        student = db.students.find_one({'studentId': student_id})
        progress = db.academicprogress.find_one({'studentId': student_id})

        data = {**student, **progress} if progress else student

        result = WhatIfSimulationService.simulate(data, new_major)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/api/students/<student_id>/gpa-check', methods=['POST'])
def gpa_simulation_check(student_id):
    """
    Post a hypothetical grade to check GPA and Standing change.
    JSON Body: { "course_code": "CS101", "grade": "A", "credits": 3 }
    """
    try:
        data = request.json
        grade = data.get('grade')
        credits = data.get('credits')

        if not grade or not credits: return jsonify({'error': 'Missing grade or credits'}), 400

        db = get_db()
        student = db.students.find_one({'studentId': student_id})

        hypothetical_courses = student.get('academicInfo', {}).get('completed_courses', [])
        hypothetical_courses.append({'grade': grade, 'credits': credits})

        new_gpa = GPAService.calculate_gpa(hypothetical_courses)
        new_standing = determine_standing(new_gpa)

        return jsonify({
            'current_gpa': student.get('academicInfo', {}).get('gpa'),
            'projected_gpa': new_gpa,
            'imported_grade': grade,
            'projected_standing': new_standing
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
