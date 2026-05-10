"""
GPA calculation and academic standing utilities for CougarWorks.
"""

import logging

logger = logging.getLogger(__name__)

# Grade point values
GRADE_POINTS = {
    'A': 4.0,
    'A-': 3.7,
    'B+': 3.3,
    'B': 3.0,
    'B-': 2.7,
    'C+': 2.3,
    'C': 2.0,
    'C-': 1.7,
    'D+': 1.3,
    'D': 1.0,
    'D-': 0.7,
    'F': 0.0,
    'WF': 0.0,
    'P': None,  # Pass - not counted in GPA
    'W': None,  # Withdrawal - not counted
    'I': None,  # Incomplete - not counted
    'IP': None  # In progress - not counted
}


def calculate_gpa(student_id):
    """
    Calculates GPA safely. Returns 0.0 on any error or if no grades exist.
    """
    db = get_db()
    if db is None:
        print("[GPA] Database not connected")
        return 0.0

    try:
        prog_doc = db.academicprogress.find_one({"studentId": student_id})

        if not prog_doc:
            print(f"[GPA] No academic progress found for {student_id}")
            return 0.0

        work_progress = prog_doc.get("workProgress", [])
        if not work_progress:
            print("[GPA] No courses in work progress")
            return 0.0

        total_points = 0
        total_credits = 0

        for item in work_progress:
            # Skip if item is a string instead of dict
            if isinstance(item, str):
                print(f"[GPA] Skipping string item: {item}")
                continue

            if not isinstance(item, dict):
                continue

            grade = item.get("grade", "")
            if grade:
                grade = grade.upper()
            creds = item.get("credits", 0)

            if creds > 0 and grade:
                grade_points = {
                    'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0,
                    'A+': 4.0, 'B+': 3.5, 'C+': 2.5, 'D+': 1.5
                }

                if grade in grade_points:
                    total_points += grade_points[grade] * creds
                    total_credits += creds

        if total_credits == 0:
            return 0.0

        gpa = total_points / total_credits
        return round(gpa, 2)

    except Exception as e:
        print(f"[GPA] Error calculating GPA: {e}")
        return 0.0


def calculate_semester_gpa(courses, semester):
    """
    Calculate GPA for a specific semester.

    Args:
        courses: List of all courses
        semester: Semester identifier (e.g., 'Fall 2025')

    Returns:
        float: Semester GPA
    """
    semester_courses = [
        c for c in courses 
        if c.get('semester') == semester
    ]
    return calculate_gpa(semester_courses)


def determine_standing(gpa, total_credits):
    """
    Determine academic standing based on GPA and credits.

    Args:
        gpa: Student's GPA
        total_credits: Total credits earned

    Returns:
        dict: Standing information
    """
    if gpa >= 3.5:
        standing = 'Dean\'s List'
        status = 'Good Standing'
    elif gpa >= 3.0:
        standing = 'Honor Roll'
        status = 'Good Standing'
    elif gpa >= 2.0:
        standing = 'Good Standing'
        status = 'Good Standing'
    elif gpa >= 1.5:
        standing = 'Academic Warning'
        status = 'Warning'
    elif gpa >= 1.0:
        standing = 'Academic Probation'
        status = 'Probation'
    else:
        standing = 'Academic Suspension'
        status = 'Suspension'

    return {
        'standing': standing,
        'status': status,
        'gpa': gpa,
        'totalCredits': total_credits,
        'isGoodStanding': gpa >= 2.0
    }


def get_gpa_history(courses):
    """
    Get GPA history by semester.

    Args:
        courses: List of courses with semester and grade info

    Returns:
        list: GPA history by semester
    """
    semesters = {}

    for course in courses:
        semester = course.get('semester', 'Unknown')
        if semester not in semesters:
            semesters[semester] = []
        semesters[semester].append(course)

    history = []
    for semester, semester_courses in sorted(semesters.items()):
        history.append({
            'semester': semester,
            'gpa': calculate_gpa(semester_courses),
            'credits': sum(c.get('credits', 3) for c in semester_courses)
        })

    return history


def get_grade_distribution(courses):
    """
    Get distribution of grades for a student.

    Args:
        courses: List of courses with grades

    Returns:
        dict: Grade distribution counts
    """
    distribution = {grade: 0 for grade in GRADE_POINTS.keys() if GRADE_POINTS[grade] is not None}
    distribution['Other'] = 0

    for course in courses:
        grade = course.get('grade', '').upper()
        if grade in distribution:
            distribution[grade] += 1
        else:
            distribution['Other'] += 1

    return distribution


def calculate_target_gpa(current_gpa, current_credits, target_gpa, remaining_credits):
    """
    Calculate required GPA in remaining courses to reach target.

    Args:
        current_gpa: Current cumulative GPA
        current_credits: Total credits earned
        target_gpa: Target cumulative GPA
        remaining_credits: Credits remaining

    Returns:
        dict: Information about what's needed to reach target
    """
    current_points = current_gpa * current_credits
    target_points = target_gpa * (current_credits + remaining_credits)
    needed_points = target_points - current_points

    if needed_points <= 0:
        return {
            'possible': True,
            'requiredGPA': 0,
            'message': 'Target already achieved or will be with current GPA'
        }

    required_gpa = needed_points / remaining_credits

    return {
        'possible': required_gpa <= 4.0,
        'requiredGPA': round(required_gpa, 2),
        'message': f"Need a {required_gpa:.2f} GPA in remaining {remaining_credits} credits to reach {target_gpa}"
    }
