from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request
from functools import wraps
from bson import ObjectId
from utils.db_utils import get_db

system_bp = Blueprint('system', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@system_bp.route('/')
def index():
    return redirect(url_for('auth.login'))



@system_bp.route('/admin/manage-advisor/<advisor_id>')
@login_required
def admin_manage_advisor(advisor_id):
    """Admin page to manage a specific advisor"""
    role = session.get('role')
    if role != 'admin':
        return redirect(url_for('system.dashboard'))

    db = get_db()
    if db is None:
        return render_template('error_page.html')

    advisor = db.advisors.find_one({"advisorId": advisor_id})
    if not advisor:
        return render_template('error_page.html', error="Advisor not found")

    advisees = list(db.students.find({"academicInfo.advisor": advisor_id}))
    all_students = list(db.students.find())

    return render_template('admin/manage_advisor.html',
                           advisor=advisor,
                           advisees=advisees,
                           all_students=all_students)


@system_bp.route('/admin/view-student/<student_id>')
@login_required
def admin_view_student(student_id):
    """Admin page to view student's full profile and progress"""
    role = session.get('role')
    if role != 'admin':
        return redirect(url_for('system.dashboard'))

    db = get_db()
    if db is None:
        return render_template('error_page.html')

    student = db.students.find_one({"studentId": student_id})
    if not student:
        return render_template('error_page.html', error="Student not found")

    if not student:
        return render_template('error_page.html', error='Student not found')

    student_data = dict(student)
    student_data.setdefault('academicInfo', {})
    student_data.setdefault('personalInfo', {})

    progress = db.academicprogress.find_one({"studentId": student_id})

    return render_template('admin/view_student.html',
                           student=student_data,
                           student_id=student_id,
                           progress=progress)


@system_bp.route('/admin/assign-advisor', methods=['POST'])
@login_required
def admin_assign_advisor():
    """API to assign an advisor to a student (JSON)"""
    role = session.get('role')
    if role != 'admin':
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    db = get_db()
    if db is None:
        return jsonify({"success": False, "error": "Database error"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No JSON data"}), 400

    student_id = data.get('student_id')
    advisor_id = data.get('advisor_id')

    if not student_id or not advisor_id:
        return jsonify({"success": False, "error": "Missing parameters"}), 400

    result = db.students.update_one(
        {"studentId": student_id},
        {"$set": {"academicInfo.advisor": advisor_id}}
    )

    if result.modified_count > 0 or result.matched_count > 0:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "No changes made"})


@system_bp.route('/admin/remove-advisee', methods=['POST'])
@login_required
def admin_remove_advisee():
    """API to remove a student from an advisor"""
    role = session.get('role')
    if role != 'admin':
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    db = get_db()
    if db is None:
        return jsonify({"success": False, "error": "Database error"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No JSON data"}), 400

    student_id = data.get('student_id')
    if not student_id:
        return jsonify({"success": False, "error": "Missing student_id"}), 400

    result = db.students.update_one(
        {"studentId": student_id},
        {"$set": {"academicInfo.advisor": None}}
    )

    if result.modified_count > 0 or result.matched_count > 0:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "No changes made"})



@system_bp.route('/advisor/view-student/<student_id>')
@login_required
def advisor_view_student(student_id):
    """Advisor page to view student's progress"""
    role = session.get('role')
    if role != 'advisor':
        return redirect(url_for('system.dashboard'))

    db = get_db()
    if db is None:
        return render_template('error_page.html')

    student = db.students.find_one({"studentId": student_id})
    if not student:
        return render_template('error_page.html', error="Student not found")

    if not student:
        return render_template('error_page.html', error='Student not found')

    student_data = dict(student)
    student_data.setdefault('academicInfo', {})
    student_data.setdefault('personalInfo', {})

    return render_template('advisor/view_student.html',
                           student=student_data,
                           student_id=student_id)




@system_bp.route('/api/students')
@login_required
def api_students():
    """Return students for admin/advisor pages that use client-side tables."""
    role = session.get('role')
    if role not in {'admin', 'advisor'}:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    if db is None:
        return jsonify([])

    query = {}
    if role == 'advisor':
        advisor = db.advisors.find_one({'email': session.get('email')})
        if advisor:
            query = {'academicInfo.advisor': advisor.get('advisorId')}

    students = list(db.students.find(query, {
        'studentId': 1,
        'email': 1,
        'personalInfo': 1,
        'academicInfo': 1
    }))
    for student in students:
        student['_id'] = str(student['_id'])
    return jsonify(students)


@system_bp.route('/api/students/<student_id>/degree-progress-summary')
@login_required
def api_degree_progress_summary(student_id):
    """API endpoint for degree progress"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database disconnected"}), 500

    student = db.students.find_one({"studentId": student_id})
    if not student:
        return jsonify({"error": "Student not found"}), 404

    major = student.get('academicInfo', {}).get('major', 'Computer Science')
    completed_courses = {c['courseCode']: c for c in student.get('academicInfo', {}).get('completedCourses', [])}

    degree_doc = db.degreerequirements.find_one({"major": major})

    if not degree_doc:
        return jsonify({
            "overallProgress": {"percentage": 0, "completedCredits": 0, "requiredCredits": 120, "currentGPA": 0.0, "programName": major},
            "categoryProgress": []
        })

    total_required = degree_doc.get('totalCreditsRequired', 120)
    total_completed = 0

    categories = []
    for cat in degree_doc.get('categories', []):
        cat_name = cat.get('name', 'Unknown')
        cat_required = cat.get('creditsRequired', 0)
        cat_completed = 0

        courses_list = []
        for course in cat.get('courses', []):
            code = course.get('courseCode', '')

            if code in completed_courses:
                cdata = completed_courses[code]
                credits = cdata.get('credits', course.get('credits', 3))
                courses_list.append({
                    "code": code,
                    "name": course.get('courseName', cdata.get('courseName', '')),
                    "credits": credits,
                    "status": "Completed",
                    "grade": cdata.get('grade', ''),
                    "semester": cdata.get('semester', '')
                })
                cat_completed += credits
                total_completed += credits
            else:
                credits = course.get('credits', 3)
                courses_list.append({
                    "code": code,
                    "name": course.get('courseName', ''),
                    "credits": credits,
                    "status": "Remaining",
                    "grade": "",
                    "semester": ""
                })

        cat_pct = int((cat_completed / cat_required) * 100) if cat_required > 0 else 0

        categories.append({
            "name": cat_name,
            "required": cat_required,
            "completed": cat_completed,
            "percentage": cat_pct,
            "courses": courses_list
        })

    overall_pct = int((total_completed / total_required) * 100) if total_required > 0 else 0

    progress = db.academicprogress.find_one({"studentId": student_id})
    current_gpa = 0.0
    if progress and 'overallProgress' in progress:
        current_gpa = progress['overallProgress'].get('currentGPA', 0.0)

    return jsonify({
        "overallProgress": {
            "percentage": overall_pct,
            "completedCredits": total_completed,
            "requiredCredits": total_required,
            "currentGPA": current_gpa,
            "programName": f"{degree_doc.get('degree', 'BS')} {major}"
        },
        "categoryProgress": categories
    })


@system_bp.route('/api/students/<student_id>/what-if')
@login_required
def api_what_if(student_id):
    """API for What-If analysis"""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database disconnected"}), 500

    major_alias = request.args.get('major', 'Computer Science')

    major_map = {
        'CS': 'Computer Science',
        'IT': 'Information Technology',
        'Cybersecurity': 'Cybersecurity',
        'Finance': 'Management Information Systems',
        'MIS': 'Management Information Systems'
    }
    major_name = major_map.get(major_alias, major_alias)

    student = db.students.find_one({"studentId": student_id})
    completed_courses = {c['courseCode']: c for c in student.get('academicInfo', {}).get('completedCourses', [])} if student else {}

    degree_doc = db.degreerequirements.find_one({"major": major_name})

    if not degree_doc:
        return jsonify({
            "overallProgress": {"percentage": 0, "completedCredits": 0, "requiredCredits": 120, "currentGPA": 0.0, "programName": f"What-If: {major_name}"},
            "categoryProgress": []
        })

    total_required = degree_doc.get('totalCreditsRequired', 120)
    total_completed = 0

    categories = []
    for cat in degree_doc.get('categories', []):
        cat_name = cat.get('name', 'Unknown')
        cat_required = cat.get('creditsRequired', 0)
        cat_completed = 0

        courses_list = []
        for course in cat.get('courses', []):
            code = course.get('courseCode', '')

            if code in completed_courses:
                cdata = completed_courses[code]
                credits = cdata.get('credits', course.get('credits', 3))
                courses_list.append({
                    "code": code,
                    "name": course.get('courseName', ''),
                    "credits": credits,
                    "status": "Completed",
                    "grade": cdata.get('grade', ''),
                    "semester": cdata.get('semester', '')
                })
                cat_completed += credits
                total_completed += credits
            else:
                credits = course.get('credits', 3)
                courses_list.append({
                    "code": code,
                    "name": course.get('courseName', ''),
                    "credits": credits,
                    "status": "Remaining",
                    "grade": "",
                    "semester": ""
                })

        cat_pct = int((cat_completed / cat_required) * 100) if cat_required > 0 else 0

        categories.append({
            "name": cat_name,
            "required": cat_required,
            "completed": cat_completed,
            "percentage": cat_pct,
            "courses": courses_list
        })

    overall_pct = int((total_completed / total_required) * 100) if total_required > 0 else 0

    return jsonify({
        "overallProgress": {
            "percentage": overall_pct,
            "completedCredits": total_completed,
            "requiredCredits": total_required,
            "currentGPA": 0.0,
            "programName": f"What-If: {degree_doc.get('degree', 'BS')} {major_name}"
        },
        "categoryProgress": categories
    })


@system_bp.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    email = session.get('email')

    db = get_db()
    if db is None:
        return render_template('error_page.html')

    if role == 'admin':
        all_students = list(db.students.find())
        all_advisors = list(db.advisors.find())

        stats = {
            'totalStudents': len(all_students),
            'totalAdvisors': len(all_advisors)
        }

        return render_template('/admin/dashboard.html',
                               students=all_students,
                               advisors=all_advisors,
                               stats=stats)

    elif role == 'advisor':
        advisor = db.advisors.find_one({"email": email})
        if not advisor:
            advisor = db.advisors.find_one()

        advisor_id = advisor.get("advisorId")
        advisees = list(db.students.find({"academicInfo.advisor": advisor_id}))

        stats = {'total': len(advisees)}

        return render_template('/advisor/dashboard.html',
                               advisor=advisor,
                               students=advisees,
                               stats=stats)

    elif role == 'student':
        return redirect(url_for('system.student_dashboard'))

    return redirect(url_for('auth.login'))


@system_bp.route('/student/dashboard')
@login_required
def student_dashboard():
    email = session.get('email')
    db = get_db()
    if db is None:
        return render_template('error_page.html', error="Database Disconnected")

    student = db.students.find_one({"email": email})
    if not student:
        student = db.students.find_one()

    if student:
        student_data = dict(student)
        student_data.setdefault('academicInfo', {})
        student_data.setdefault('personalInfo', {})

        real_id = student_data.get('studentId')

        progress = db.academicprogress.find_one({"studentId": real_id})
        credits_earned = 0
        gpa = 0.0
        if progress:
            credits_earned = progress.get('overallProgress', {}).get('completedCredits', 0)
            gpa = progress.get('overallProgress', {}).get('currentGPA', 0.0)

        student_data['academicInfo'].setdefault('major', 'Not Assigned')
        student_data['academicInfo'].setdefault('advisor', 'Unassigned')
        student_data['academicInfo']['creditsEarned'] = credits_earned
        student_data['academicInfo']['gpa'] = gpa

        if credits_earned > 90:
            classification = 'Senior'
        elif credits_earned > 60:
            classification = 'Junior'
        elif credits_earned > 30:
            classification = 'Sophomore'
        else:
            classification = 'Freshman'
        student_data['personalInfo']['classification'] = classification

        standing = {
            'isGoodStanding': gpa >= 2.0,
            'gpa': gpa,
            'status': 'Good Standing' if gpa >= 2.0 else 'Academic Warning'
        }

        return render_template('/student/dashboard.html',
                               student=student_data,
                               student_id=real_id,
                               gpa=gpa,
                               credits=credits_earned,
                               standing=standing)

    return render_template('error_page.html', error="No students found")


@system_bp.route('/degree-progress')
@login_required
def degree_progress():
    email = session.get('email')
    db = get_db()
    if db is None:
        return render_template('error_page.html')

    student = db.students.find_one({"email": email})
    if not student:
        student = db.students.find_one()

    student_data = dict(student)
    current_major = student_data.get('academicInfo', {}).get('major', 'Computer Science')
    real_id = student_data.get('studentId')

    return render_template('/student/degree_progress.html',
                           student_id=real_id,
                           current_major=current_major,
                           student=student_data)


@system_bp.route('/remaining_courses')
@login_required
def remaining_courses():
    email = session.get('email')
    db = get_db()
    student = db.students.find_one({"email": email})
    if not student:
        student = db.students.find_one()
    real_id = student.get('studentId')
    return render_template('/student/remaining_courses.html', student_id=real_id)


@system_bp.route('/gpa_standing')
@login_required
def gpa_standing():
    email = session.get('email')
    db = get_db()
    student = db.students.find_one({"email": email})
    if not student:
        student = db.students.find_one()
    real_id = student.get('studentId')

    progress = db.academicprogress.find_one({"studentId": real_id})
    gpa = 0.0
    if progress:
        gpa = progress.get('overallProgress', {}).get('currentGPA', 0.0)

    return render_template('/student/gpa_standing.html', gpa=gpa, student_id=real_id)


@system_bp.route('/profile')
@login_required
def profile():
    email = session.get('email')
    db = get_db()
    if db is None:
        return render_template('error_page.html')

    student = db.students.find_one({"email": email})
    if not student:
        student = db.students.find_one()

    student_data = dict(student)
    student_data.setdefault('personalInfo', {})
    student_data.setdefault('academicInfo', {})

    real_id = student_data.get('studentId')
    progress = db.academicprogress.find_one({"studentId": real_id})

    # Get advisor name if assigned
    advisor_id = student_data.get('academicInfo', {}).get('advisor')
    advisor_name = "Unassigned"
    if advisor_id:
        advisor = db.advisors.find_one({"advisorId": advisor_id})
        if advisor:
            advisor_name = f"{advisor.get('personalInfo', {}).get('firstName', '')} {advisor.get('personalInfo', {}).get('lastName', '')}".strip()

    # Calculate classification
    credits = 0
    if progress:
        credits = progress.get('overallProgress', {}).get('completedCredits', 0)

    if credits > 90:
        classification = 'Senior'
    elif credits > 60:
        classification = 'Junior'
    elif credits > 30:
        classification = 'Sophomore'
    else:
        classification = 'Freshman'

    # Format address dictionary into string
    address_dict = student_data.get('personalInfo', {}).get('address', {})
    if isinstance(address_dict, dict):
        street = address_dict.get('street', '')
        city = address_dict.get('city', '')
        state = address_dict.get('state', '')
        zip_code = address_dict.get('zip', '')
        formatted_address = f"{street}, {city}, {state} {zip_code}".strip(', ')
        if not formatted_address.replace(',', '').replace(' ', ''):
            formatted_address = 'N/A'
    else:
        formatted_address = address_dict or 'N/A'


    return render_template('student/profile.html', 
                           student=student_data,
                           advisor_name=advisor_name,
                           classification=classification,
                           credits=credits,
                           formatted_address=formatted_address,
                           progress=progress)



@system_bp.route('/admin/profile')
@login_required
def admin_profile():
    role = session.get('role')
    if role != 'admin':
        return redirect(url_for('system.dashboard'))

    email = session.get('email')
    db = get_db()
    if db is None:
        return render_template('error_page.html')

    admin = db.admins.find_one({"email": email})
    if not admin:
        admin = db.admins.find_one()

    if not admin:
        return render_template('error_page.html', error='Admin not found')

    admin_data = dict(admin)
    admin_data.setdefault('personalInfo', {})
    admin_data['personalInfo'].setdefault('firstName', 'Admin')
    admin_data['personalInfo'].setdefault('lastName', 'User')
    admin_data.setdefault('phone', 'N/A')

    return render_template('admin/profile.html', admin=admin_data)


@system_bp.route('/advisor/profile')
@login_required
def advisor_profile():
    role = session.get('role')
    if role != 'advisor':
        return redirect(url_for('system.dashboard'))

    email = session.get('email')
    db = get_db()
    if db is None:
        return render_template('error_page.html')

    advisor = db.advisors.find_one({"email": email})
    if not advisor:
        advisor = db.advisors.find_one()

    if not advisor:
        return render_template('error_page.html', error='Advisor not found')

    advisor_data = dict(advisor)
    advisor_data.setdefault('personalInfo', {})

    # Ensure all fields have values
    advisor_data['personalInfo'].setdefault('firstName', 'Unknown')
    advisor_data['personalInfo'].setdefault('lastName', 'Advisor')
    advisor_data.setdefault('phone', 'N/A')
    advisor_data.setdefault('department', 'Academic Advising')
    advisor_data.setdefault('office', 'Main Campus')
    advisor_data.setdefault('officeHours', 'M-F 9:00 AM - 5:00 PM')

    advisor_id = advisor_data.get('advisorId')
    advisee_count = db.students.count_documents({"academicInfo.advisor": advisor_id})
    
    
    # Format office hours dictionary into readable string
    office_hours_dict = advisor_data.get('officeHours', {})
    if isinstance(office_hours_dict, dict):
        formatted_hours = []
        day_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        day_names = {'monday': 'Mon', 'tuesday': 'Tue', 'wednesday': 'Wed', 
                     'thursday': 'Thu', 'friday': 'Fri', 'saturday': 'Sat', 'sunday': 'Sun'}

        for day in day_order:
            if day in office_hours_dict and office_hours_dict[day]:
                formatted_hours.append(f"{day_names.get(day, day.title())}: {office_hours_dict[day]}")

        if formatted_hours:
            formatted_office_hours = ' | '.join(formatted_hours)
        else:
            formatted_office_hours = 'By Appointment'
    else:
        formatted_office_hours = office_hours_dict or 'By Appointment'

    return render_template('advisor/profile.html', 
                           advisor=advisor_data,
                           advisee_count=advisee_count,
                           formatted_office_hours=formatted_office_hours)



@system_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
