from functools import wraps
import datetime

from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request

from utils.db_utils import parse_json, get_db

advisor_bp = Blueprint('advisors', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'advisor':
            return redirect(url_for('system.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def _get_current_advisor():
    db = get_db()
    email = session.get('email')
    if db is None or not email:
        return None

    # Advisor documents in this project store email at the top level.
    advisor = db.advisors.find_one({'email': email})

    # Backward compatibility for old data that may have nested advisor email.
    if not advisor:
        advisor = db.advisors.find_one({'personalInfo.email': email})

    return advisor


@advisor_bp.route('/api/advisors', methods=['GET'])
def get_all_advisors():
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database not connected'}), 500

        advisors = list(db.advisors.find(
            {},
            {
                'advisorId': 1,
                'personalInfo.firstName': 1,
                'personalInfo.lastName': 1,
                'email': 1,
                'department': 1,
                'title': 1
            }
        ))

        return jsonify(parse_json(advisors))
    except Exception as e:
        print(f"\n❌ Error in /advisor/api/advisors: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advisor_bp.route('/api/advisors/<advisor_id>', methods=['GET'])
def get_advisor_details(advisor_id):
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database not connected'}), 500

        advisor = db.advisors.find_one({'advisorId': advisor_id})
        if not advisor:
            return jsonify({'error': 'Advisor not found'}), 404

        return jsonify(parse_json(advisor))
    except Exception as e:
        print(f"\n❌ Error in /advisor/api/advisors/{advisor_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advisor_bp.route('/api/advisors/<advisor_id>/students', methods=['GET'])
def get_advisor_students(advisor_id):
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Database not connected'}), 500

        students = list(db.students.find(
            {'academicInfo.advisor': advisor_id},
            {
                'studentId': 1,
                'personalInfo.firstName': 1,
                'personalInfo.lastName': 1,
                'email': 1,
                'academicInfo.major': 1,
                'academicInfo.standing': 1,
                'academicInfo.enrollmentStatus': 1
            }
        ))

        return jsonify(parse_json(students))
    except Exception as e:
        print(f"\n❌ Error in /advisor/api/advisors/{advisor_id}/students: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advisor_bp.route('/student-notes/<student_id>')
@login_required
def student_notes(student_id):
    db = get_db()
    advisor = _get_current_advisor()
    student = db.students.find_one({'studentId': student_id})

    if not advisor:
        return render_template('error_page.html', error='Advisor not found for this account')
    if not student:
        return render_template('error_page.html', error='Student not found')

    if 'studentNotes' not in db.list_collection_names():
        notes = []
    else:
        notes = list(db.studentNotes.find({'studentId': student_id}).sort('createdAt', -1))

    return render_template('advisor/student_notes.html', advisor=advisor, student=student, notes=notes)


@advisor_bp.route('/add-note/<student_id>', methods=['POST'])
@login_required
def add_note(student_id):
    db = get_db()
    advisor = _get_current_advisor()

    if not advisor:
        return render_template('error_page.html', error='Advisor not found for this account')

    content = request.form.get('content')
    if content:
        if 'studentNotes' not in db.list_collection_names():
            db.create_collection('studentNotes')

        new_note = {
            'noteId': datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'),
            'studentId': student_id,
            'advisorId': advisor['advisorId'],
            'content': content,
            'createdAt': datetime.datetime.utcnow(),
            'updatedAt': datetime.datetime.utcnow(),
            'isPrivate': request.form.get('isPrivate') == 'on'
        }

        db.studentNotes.insert_one(new_note)

    return redirect(url_for('advisors.student_notes', student_id=student_id))


@advisor_bp.route('/delete-note/<note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    db = get_db()
    if 'studentNotes' in db.list_collection_names():
        db.studentNotes.delete_one({'noteId': note_id})
    return jsonify({'success': True})


@advisor_bp.route('/meetings')
@login_required
def advisor_meetings():
    db = get_db()
    advisor = _get_current_advisor()

    if not advisor:
        return render_template('error_page.html', error='Advisor not found for this account')

    advisor_id = advisor['advisorId']

    if 'meetings' not in db.list_collection_names():
        meetings = []
    else:
        meetings = list(db.meetings.find({'advisorId': advisor_id}).sort('scheduledDate', 1))

    for meeting in meetings:
        student = db.students.find_one({'studentId': meeting.get('studentId')})
        if student:
            meeting['studentName'] = f"{student.get('personalInfo', {}).get('firstName', '')} {student.get('personalInfo', {}).get('lastName', '')}".strip()
        else:
            meeting['studentName'] = 'Unknown'

    return render_template('advisor/meetings.html', advisor=advisor, meetings=meetings)


@advisor_bp.route('/schedule-meeting', methods=['GET', 'POST'])
@login_required
def schedule_meeting():
    db = get_db()
    advisor = _get_current_advisor()

    if not advisor:
        return render_template('error_page.html', error='Advisor not found for this account')

    if request.method == 'POST':
        if 'meetings' not in db.list_collection_names():
            db.create_collection('meetings')

        new_meeting = {
            'meetingId': datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'),
            'studentId': request.form.get('studentId'),
            'advisorId': advisor['advisorId'],
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'scheduledDate': request.form.get('scheduledDate'),
            'startTime': request.form.get('startTime'),
            'endTime': request.form.get('endTime'),
            'location': request.form.get('location'),
            'status': 'Scheduled',
            'createdAt': datetime.datetime.utcnow(),
            'updatedAt': datetime.datetime.utcnow()
        }

        db.meetings.insert_one(new_meeting)
        return redirect(url_for('advisors.advisor_meetings'))

    advisees = list(db.students.find({'academicInfo.advisor': advisor['advisorId']}))

    return render_template('advisor/schedule_meeting.html', advisor=advisor, advisees=advisees)


@advisor_bp.route('/update-meeting/<meeting_id>', methods=['POST'])
@login_required
def update_meeting(meeting_id):
    db = get_db()
    advisor = _get_current_advisor()

    if not advisor:
        return render_template('error_page.html', error='Advisor not found for this account')

    status = request.form.get('status')

    if 'meetings' in db.list_collection_names():
        db.meetings.update_one(
            {'meetingId': meeting_id, 'advisorId': advisor['advisorId']},
            {'$set': {'status': status, 'updatedAt': datetime.datetime.utcnow()}}
        )

    return redirect(url_for('advisors.advisor_meetings'))
