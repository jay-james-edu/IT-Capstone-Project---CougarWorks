import logging
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify

from utils.auth_utils import login_required, admin_required, hash_password
from utils.db_utils import get_db
from utils.notification_utils import notification_service
from utils.degree_utils import calculate_degree_progress

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


def _require_admin():
    return session.get('role') == 'admin'


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard showing students and advisors."""
    db = get_db()
    if db is None:
        return render_template('error_page.html', error='Database disconnected')

    students = list(db.students.find())
    advisors = list(db.advisors.find())
    stats = {
        'totalStudents': len(students),
        'totalAdvisors': len(advisors),
        'totalAdmins': db.admins.count_documents({}) if 'admins' in db.list_collection_names() else 0
    }

    return render_template('admin/dashboard.html', students=students, advisors=advisors, stats=stats)


@admin_bp.route('/add-student', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_student():
    db = get_db()
    if db is None:
        return render_template('error_page.html', error='Database disconnected')

    if request.method == 'POST':
        form_data = request.form
        student_id = form_data.get('studentId')

        if db.students.find_one({'studentId': student_id}):
            advisors = list(db.advisors.find())
            majors = ['Computer Science', 'Information Technology', 'Cybersecurity', 'Management Information Systems']
            return render_template('admin/add_student.html', advisors=advisors, majors=majors, error='Student ID already exists')

        new_student = {
            'studentId': student_id,
            'personalInfo': {
                'firstName': form_data.get('firstName'),
                'lastName': form_data.get('lastName'),
                'phone': form_data.get('phone') or None,
                'address': {
                    'street': form_data.get('address_street') or None,
                    'city': form_data.get('address_city') or None,
                    'state': form_data.get('address_state') or None,
                    'zip': form_data.get('address_zip') or None
                } if form_data.get('address_street') else None
            },
            'email': form_data.get('email'),
            'password': hash_password(form_data.get('password')),
            'academicInfo': {
                'major': form_data.get('major'),
                'advisor': None,
                'catalogYear': form_data.get('catalogYear'),
                'enrollmentStatus': form_data.get('enrollmentStatus'),
                'completedCourses': [],
                'currentCourses': [],
                'creditsEarned': 0,
                'totalCredits': 0,
                'gpa': 0.0
            },
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }

        db.students.insert_one(new_student)
        flash('Student created successfully.', 'success')
        return redirect(url_for('admin.dashboard'))

    advisors = list(db.advisors.find())
    majors = ['Computer Science', 'Information Technology', 'Cybersecurity', 'Management Information Systems']
    return render_template('admin/add_student.html', advisors=advisors, majors=majors)


@admin_bp.route('/add-advisor', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_advisor():
    db = get_db()
    if db is None:
        return render_template('error_page.html', error='Database disconnected')

    if request.method == 'POST':
        form_data = request.form
        advisor_id = form_data.get('advisorId')

        if db.advisors.find_one({'advisorId': advisor_id}):
            return render_template('admin/add_advisor.html', error='Advisor ID already exists')

        new_advisor = {
            'advisorId': advisor_id,
            'personalInfo': {
                'firstName': form_data.get('firstName'),
                'lastName': form_data.get('lastName')
            },
            'email': form_data.get('email'),
            'password': hash_password(form_data.get('password')),
            'phone': form_data.get('phone') or None,
            'department': form_data.get('department'),
            'office': form_data.get('office'),
            'officeHours': {
                'monday': form_data.get('hours_monday'),
                'tuesday': form_data.get('hours_tuesday'),
                'wednesday': form_data.get('hours_wednesday'),
                'thursday': form_data.get('hours_thursday'),
                'friday': form_data.get('hours_friday')
            },
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }

        db.advisors.insert_one(new_advisor)
        flash('Advisor created successfully.', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/add_advisor.html')


@admin_bp.route('/edit-student/<student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_student(student_id):
    db = get_db()
    if db is None:
        return render_template('error_page.html', error='Database disconnected')

    student = db.students.find_one({'studentId': student_id})
    if not student:
        return render_template('error_page.html', error='Student not found')

    if request.method == 'POST':
        form_data = request.form
        db.students.update_one(
            {'studentId': student_id},
            {'$set': {
                'personalInfo.firstName': form_data.get('firstName'),
                'personalInfo.lastName': form_data.get('lastName'),
                'personalInfo.phone': form_data.get('phone') or None,
                'email': form_data.get('email'),
                'academicInfo.major': form_data.get('major'),
                'academicInfo.catalogYear': form_data.get('catalogYear'),
                'academicInfo.enrollmentStatus': form_data.get('enrollmentStatus'),
                'updatedAt': datetime.utcnow()
            }}
        )
        flash('Student updated successfully.', 'success')
        return redirect(url_for('admin.dashboard'))

    majors = ['Computer Science', 'Information Technology', 'Cybersecurity', 'Management Information Systems']
    return render_template('admin/edit_student.html', student=student, majors=majors)


@admin_bp.route('/delete-student/<student_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_student(student_id):
    db = get_db()
    if db is None:
        return jsonify({'success': False, 'error': 'Database disconnected'}), 500
    db.students.delete_one({'studentId': student_id})
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/edit-advisor/<advisor_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_advisor(advisor_id):
    db = get_db()
    if db is None:
        return render_template('error_page.html', error='Database disconnected')

    advisor = db.advisors.find_one({'advisorId': advisor_id})
    if not advisor:
        return render_template('error_page.html', error='Advisor not found')

    if request.method == 'POST':
        form_data = request.form
        db.advisors.update_one(
            {'advisorId': advisor_id},
            {'$set': {
                'personalInfo.firstName': form_data.get('firstName'),
                'personalInfo.lastName': form_data.get('lastName'),
                'email': form_data.get('email'),
                'phone': form_data.get('phone') or None,
                'department': form_data.get('department'),
                'office': form_data.get('office'),
                'officeHours': {
                    'monday': form_data.get('hours_monday'),
                    'tuesday': form_data.get('hours_tuesday'),
                    'wednesday': form_data.get('hours_wednesday'),
                    'thursday': form_data.get('hours_thursday'),
                    'friday': form_data.get('hours_friday')
                },
                'updatedAt': datetime.utcnow()
            }}
        )
        flash('Advisor updated successfully.', 'success')
        return redirect(url_for('admin.admin_manage_advisor', advisor_id=advisor_id))

    return render_template('admin/edit_advisor.html', advisor=advisor)


@admin_bp.route('/delete-advisor/<advisor_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_advisor(advisor_id):
    db = get_db()
    if db is None:
        return jsonify({'success': False, 'error': 'Database disconnected'}), 500
    db.advisors.delete_one({'advisorId': advisor_id})
    db.students.update_many({'academicInfo.advisor': advisor_id}, {'$set': {'academicInfo.advisor': None}})
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/manage-advisor/<advisor_id>')
@login_required
@admin_required
def admin_manage_advisor(advisor_id):
    db = get_db()
    if db is None:
        return render_template('error_page.html', error='Database disconnected')

    advisor = db.advisors.find_one({'advisorId': advisor_id})
    if not advisor:
        return render_template('error_page.html', error='Advisor not found')

    advisees = list(db.students.find({'academicInfo.advisor': advisor_id}))
    all_students = list(db.students.find())

    return render_template('admin/manage_advisor.html', advisor=advisor, advisees=advisees, all_students=all_students)


@admin_bp.route('/view-student/<student_id>')
@login_required
@admin_required
def admin_view_student(student_id):
    db = get_db()
    if db is None:
        return render_template('error_page.html', error='Database disconnected')

    student = db.students.find_one({'studentId': student_id})
    if not student:
        return render_template('error_page.html', error='Student not found')

    student.setdefault('academicInfo', {})
    student.setdefault('personalInfo', {})
    progress = db.academicprogress.find_one({'studentId': student_id})

    return render_template('admin/view_student.html', student=student, student_id=student_id, progress=progress)


@admin_bp.route('/assign-advisor', methods=['POST'])
@login_required
@admin_required
def admin_assign_advisor():
    db = get_db()
    if db is None:
        return jsonify({'success': False, 'error': 'Database error'}), 500

    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id')
    advisor_id = data.get('advisor_id')

    if not student_id or not advisor_id:
        return jsonify({'success': False, 'error': 'Missing student_id or advisor_id'}), 400

    result = db.students.update_one(
        {'studentId': student_id},
        {'$set': {'academicInfo.advisor': advisor_id, 'updatedAt': datetime.utcnow()}}
    )

    if result.matched_count:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Student not found'}), 404


@admin_bp.route('/remove-advisee', methods=['POST'])
@login_required
@admin_required
def admin_remove_advisee():
    db = get_db()
    if db is None:
        return jsonify({'success': False, 'error': 'Database error'}), 500

    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id')

    if not student_id:
        return jsonify({'success': False, 'error': 'Missing student_id'}), 400

    result = db.students.update_one(
        {'studentId': student_id},
        {'$set': {'academicInfo.advisor': None, 'updatedAt': datetime.utcnow()}}
    )

    if result.matched_count:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Student not found'}), 404


@admin_bp.route('/api/students')
@login_required
@admin_required
def api_students():
    db = get_db()
    if db is None:
        return jsonify([])

    students = list(db.students.find({}, {
        'studentId': 1,
        'email': 1,
        'personalInfo': 1,
        'academicInfo': 1
    }))

    for student in students:
        student['_id'] = str(student['_id'])

    return jsonify(students)


@admin_bp.route('/send-emails', methods=['POST'])
@login_required
@admin_required
def send_emails():
    data = request.get_json(silent=True) or {}
    student_ids = data.get('studentIds', [])
    email_type = data.get('emailType', 'progress')
    custom_message = data.get('message') or data.get('body', '')

    if not student_ids:
        return jsonify({'success': False, 'error': 'No students selected'}), 400

    db = get_db()
    sent = 0
    failed = 0

    for sid in student_ids:
        student = db.students.find_one({'studentId': sid})
        if not student:
            failed += 1
            continue

        email = student.get('email')
        name = f"{student.get('personalInfo', {}).get('firstName', '')} {student.get('personalInfo', {}).get('lastName', '')}".strip()

        try:
            if email_type == 'progress':
                major = student.get('academicInfo', {}).get('major')
                progress = calculate_degree_progress(sid, major)
                if progress:
                    notification_service.send_progress_notification(email, name, progress.get('overallProgress', {}))
            elif email_type == 'custom':
                notification_service.send_advisor_message(email, name, 'CougarWorks Admin', custom_message)
            elif email_type == 'reminder':
                notification_service.send_registration_reminder(email, name, 'December 15, 2026', [])
            sent += 1
        except Exception as exc:
            logger.error('Failed to send email to %s: %s', email, exc)
            failed += 1

    return jsonify({'success': True, 'sent': sent, 'failed': failed, 'message': f'Sent {sent} emails, {failed} failed'})
