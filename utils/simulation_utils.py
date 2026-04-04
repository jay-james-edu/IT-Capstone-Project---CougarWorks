from typing import Dict, List, Any

DEGREE_TEMPLATES = {
    "Computer Science": {
        "total_credits": 120,
        "required_courses": [
            "CPSC 1301K", "CPSC 1302K", "CPSC 2105", 
            "CYBR 2159", "CYBR 2160", "MATH 2125"
        ],
        "electives_required": 4
    },
    "Business Administration": {
        "total_credits": 120,
        "required_courses": [
            "BUS101", "ACC201", "MKT301",
            "FIN201", "MGMT301"
        ],
        "electives_required": 5
    },
    "Biology": {
        "total_credits": 120,
        "required_courses": [
            "BIO101", "BIO201", "CHEM101",
            "CHEM201", "PHYS101"
        ],
        "electives_required": 4
    },
    "Information Technology": {
        "total_credits": 120,
        "required_courses": [
            "IT101", "IT201", "IT301",
            "CS101", "NET201"
        ],
        "electives_required": 4
    },
    "Cybersecurity": {
        "total_credits": 120,
        "required_courses": [
            "CYB101", "CYB201", "NET201",
            "CS101", "CS201"
        ],
        "electives_required": 4
    }
}

class WhatIfSimulationService:
    @staticmethod
    def simulate(student_data: Dict[str, Any], new_major: str) -> Dict[str, Any]:
        if new_major not in DEGREE_TEMPLATES:
            raise ValueError("Invalid major selected")

        template = DEGREE_TEMPLATES[new_major]


        completed_courses_flat = []

        # Checks the current semester courses
        current_courses = student_data.get('degreeProgress', {}).get('currentSemesterCourses', [])
        completed_courses_flat.extend([c.get('code') for c in current_courses if c.get('code')])

        deg_prog = student_data.get('degreeProgress', {})
        if 'fieldOfStudy' in deg_prog:
            completed_courses_flat.extend([c.get('code') for c in deg_prog['fieldOfStudy'].get('courses', [])])
        if 'requiredForMajor' in deg_prog:
            completed_courses_flat.extend([c.get('code') for c in deg_prog['requiredForMajor'].get('courses', [])])

        completed_courses = list(set(completed_courses_flat))

        required_courses = template['required_courses']

        completed_required = [
            course for course in completed_courses
            if course in required_courses
        ]

        progress_percentage = (
            len(completed_required) / len(required_courses)
        ) * 100 if required_courses else 0

        return {
            "simulated_major": new_major,
            "completed_required_courses": len(completed_required),
            "total_required_courses": len(required_courses),
            "progress_percentage": round(progress_percentage, 2),
            "disclaimer": "This is a simulation only and does not change your official academic record."
        }
