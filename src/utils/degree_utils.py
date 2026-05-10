"""
Degree tracking utilities for CougarWorks.
Handles degree progress calculation and remaining course tracking.
"""

import logging
from utils.db_utils import get_db, get_student, get_degree_requirements

logger = logging.getLogger(__name__)


def calculate_degree_progress(student_id, major=None):

    student = get_student(student_id)
    if not student:
        return None

    # Get major from student record if not provided
    if not major:
        major = student.get('academicInfo', {}).get('major')

    if not major:
        logger.warning(f"No major found for student {student_id}")
        return None

    # Get degree requirements
    requirements = get_degree_requirements(major)
    if not requirements:
        logger.warning(f"No degree requirements found for major: {major}")
        return _generate_default_progress(student)

    # Get student's completed courses
    completed_courses = student.get('academicInfo', {}).get('completedCourses', [])
    current_gpa = student.get('academicInfo', {}).get('gpa', 0.0)
    total_credits = student.get('academicInfo', {}).get('totalCredits', 0)

    # Calculate progress for each requirement category
    progress = {
        'studentId': student_id,
        'studentName': f"{student.get('personalInfo', {}).get('firstName', '')} {student.get('personalInfo', {}).get('lastName', '')}",
        'major': major,
        'overallProgress': {
            'percentage': 0,
            'completedCredits': total_credits,
            'requiredCredits': requirements.get('totalCreditsRequired', 120),
            'currentGPA': current_gpa
        },
        'categories': [],
        'remainingRequirements': []
    }

    # Process each requirement category
    categories = requirements.get('categories', [])
    total_required = 0
    total_completed = 0

    for category in categories:
        cat_name = category.get('name', 'Unknown')
        cat_credits_required = category.get('creditsRequired', 0)
        cat_courses = category.get('courses', [])

        # Calculate completed credits in this category
        cat_credits_completed = 0
        completed_in_category = []

        for course in cat_courses:
            course_code = course.get('courseCode')
            course_credits = course.get('credits', 3)

            # Check if student completed this course
            is_completed = any(
                cc.get('courseCode') == course_code 
                for cc in completed_courses
            )

            if is_completed:
                cat_credits_completed += course_credits
                completed_in_category.append(course_code)
                total_completed += course_credits
            else:
                progress['remainingRequirements'].append({
                    'category': cat_name,
                    'courseCode': course_code,
                    'courseName': course.get('courseName', ''),
                    'credits': course_credits
                })

        total_required += cat_credits_required

        cat_percentage = round((cat_credits_completed / cat_credits_required) * 100) if cat_credits_required > 0 else 0

        progress['categories'].append({
            'name': cat_name,
            'creditsRequired': cat_credits_required,
            'creditsCompleted': cat_credits_completed,
            'percentage': cat_percentage,
            'completedCourses': completed_in_category
        })

    # Calculate overall percentage
    progress['overallProgress']['percentage'] = round((total_completed / total_required) * 100) if total_required > 0 else 0

    return progress


def _generate_default_progress(student):
    """Generate a default progress object when requirements aren't found."""
    total_credits = student.get('academicInfo', {}).get('totalCredits', 0)
    gpa = student.get('academicInfo', {}).get('gpa', 0.0)

    return {
        'studentId': student.get('studentId'),
        'studentName': f"{student.get('personalInfo', {}).get('firstName', '')} {student.get('personalInfo', {}).get('lastName', '')}",
        'major': student.get('academicInfo', {}).get('major', 'Unknown'),
        'overallProgress': {
            'percentage': round((total_credits / 120) * 100),
            'completedCredits': total_credits,
            'requiredCredits': 120,
            'currentGPA': gpa
        },
        'categories': [],
        'remainingRequirements': []
    }


def get_remaining_courses(student_id):
    """
    Get list of remaining courses for a student.

    Args:
        student_id: Student's ID

    Returns:
        list: List of remaining courses with details
    """
    progress = calculate_degree_progress(student_id)
    if not progress:
        return []

    return progress.get('remainingRequirements', [])


def check_graduation_eligibility(student_id):
    """
    Check if a student is eligible for graduation.

    Args:
        student_id: Student's ID

    Returns:
        dict: Eligibility status with details
    """
    progress = calculate_degree_progress(student_id)
    student = get_student(student_id)

    if not progress or not student:
        return {'eligible': False, 'reasons': ['Student record not found']}

    reasons = []
    eligible = True

    # Check credit requirements
    total_credits = student.get('academicInfo', {}).get('totalCredits', 0)
    required_credits = progress['overallProgress']['requiredCredits']

    if total_credits < required_credits:
        eligible = False
        reasons.append(f"Need {required_credits - total_credits} more credits")

    # Check GPA requirements
    gpa = student.get('academicInfo', {}).get('gpa', 0.0)
    if gpa < 2.0:
        eligible = False
        reasons.append(f"GPA below minimum (current: {gpa:.2f}, required: 2.0)")

    # Check remaining requirements
    remaining = progress.get('remainingRequirements', [])
    if remaining:
        eligible = False
        reasons.append(f"{len(remaining)} required courses remaining")

    return {
        'eligible': eligible,
        'reasons': reasons if reasons else ['All requirements met'],
        'progress': progress
    }
