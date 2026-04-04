class GPAService:
    grade_points = {
        "A": 4.0,
        "B": 3.0,
        "C": 2.0,
        "D": 1.0,
        "F": 0.0,
        "AP": 4.0,
        "AI": 4.0,
        "BP": 3.0,
        "BI": 3.0,
        "CP": 2.0,
        "CI": 2.0,
        "DP": 1.0,
        "DI": 1.0,
        "FP": 0.0,
        "FI": 0.0,
        "W": 0.0,
        "I": 0.0
    }

    @staticmethod
    def calculate_gpa(courses: list) -> float:
        total_points = 0
        total_credits = 0

        for course in courses:
            grade = course.get("grade")
            credits = float(course.get("credits", 0))

            points = GPAService.grade_points.get(grade, 0)

            if grade not in ['W', 'I']: 
                total_points += points * credits
                total_credits += credits

        if total_credits == 0:
            return 0.0

        return round(total_points / total_credits, 2)

def determine_standing(gpa: float) -> str:
    if gpa >= 3.5:
        return "Honors"
    elif gpa >= 2.0:
        return "Good Standing"
    elif gpa >= 1.0:
        return "Academic Probation"
    else:
        return "Academic Suspension"


class GradeManager:
    @staticmethod
    def post_grade(student_id, course_code, grade, credits, db):

        student = db.students.find_one({'studentId': student_id})
        if not student:
            return None, None

        # Initialize completed_courses if not present
        if 'completed_courses' not in student.get('academicInfo', {}):
            student['academicInfo']['completed_courses'] = []

        # Add the new course
        student['academicInfo']['completed_courses'].append({
            "code": course_code,
            "grade": grade,
            "credits": credits
        })

        # Recalculate GPA
        new_gpa = GPAService.calculate_gpa(student['academicInfo']['completed_courses'])

        # Determine standing
        new_standing = determine_standing(new_gpa)

        # Update DB
        db.students.update_one(
            {"studentId": student_id},
            {
                "$set": {
                    "academicInfo.completed_courses": student['academicInfo']['completed_courses'],
                    "academicInfo.gpa": new_gpa,
                    "academicInfo.standing": new_standing
                }
            }
        )

        return new_gpa, new_standing
