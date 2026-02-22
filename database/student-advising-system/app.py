import os
import json
from flask import Flask, jsonify, send_from_directory, render_template
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from bson import json_util
from datetime import datetime
import sys

load_dotenv()

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

os.makedirs(template_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir)
            
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# MongoDB Atlas connection
MONGODB_URI = os.getenv('MONGODB_URI')
client = None
db = None
connection_status = 'disconnected'

def parse_json(data):
    """Convert MongoDB ObjectId to string for JSON serialization"""
    return json.loads(json_util.dumps(data))

def connect_to_mongo(): 
    """Establish connection to MongoDB Atlas"""
    global client, db, connection_status
    
    try:
        client = MongoClient(MONGODB_URI, 
                            serverSelectionTimeoutMS=5000,
                            connectTimeoutMS=5000)
        
        client.admin.command('ping')
        
        db = client['Student_Advising_System']
        connection_status = 'connected'
        
        print('\n✅ Connected to MongoDB Atlas')
        print(f'📊 Database: Student_Advising_System')
        
        collections = db.list_collection_names()
        print(f'📚 Collections found: {", ".join(collections)}')
        
        # Create indexes if they don't exist
        try:
            if 'students' in collections:
                index_names = [idx['name'] for idx in db.students.list_indexes()]
                
                if 'studentId_1' not in index_names and 'Student ID' not in index_names:
                    db.students.create_index('studentId', unique=True, name='studentId_1')
                    print('🔧 Created index: studentId_1')
                    
            if 'advisors' in collections:
                index_names = [idx['name'] for idx in db.advisors.list_indexes()]
                
                if 'advisorId_1' not in index_names and 'Advisor ID' not in index_names:
                    db.advisors.create_index('advisorId', unique=True, name='advisorId_1')
                    print('🔧 Created index: advisorId_1')
        except Exception as e:
            print(f'⚠️ Index check: {e}')
            
    except ConnectionFailure as e:
        connection_status = 'error'
        print('\n❌ MongoDB Atlas connection error:')
        print('   Check your connection string and IP whitelist in Atlas')
        print(f'   Error details: {e}')
    except Exception as e:
        connection_status = 'error'
        print(f'\n❌ Unexpected error: {e}')

# Connect to MongoDB on startup
if not os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    connect_to_mongo()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': connection_status,
        'database': 'Student_Advising_System',
        'timestamp': datetime.now().isoformat(),
        'connected': db is not None 
    })

@app.route('/api/test', methods=['GET'])
def test():
    """Simple test endpoint"""
    return jsonify({
        'status': 'ok',
        'connected': db is not None,
        'message': 'API is working'
    })

@app.route('/api/debug', methods=['GET'])
def debug():
    """Debug endpoint with system information"""
    info = {
        'db_connected': db is not None,
        'env_file_exists': os.path.exists('.env'),
        'mongodb_uri_set': os.getenv('MONGODB_URI') is not None,
        'current_directory': os.getcwd(),
        'templates_folder_exists': os.path.exists('templates'),
        'static_folder_exists': os.path.exists('static'),
        'connection_status': connection_status
    }
    
    if db is not None:
        try:
            info['collections'] = db.list_collection_names()
            info['collection_counts'] = {}
            for coll in info['collections']:
                info['collection_counts'][coll] = db[coll].count_documents({})
        except Exception as e:
            info['collection_error'] = str(e)
    
    return jsonify(info)

@app.route('/api/info', methods=['GET'])
def database_info():
    """Get database information"""
    try:
        if db is None:
            return jsonify({'error': 'Database not connected'}), 500
        
        collections = db.list_collection_names()
        stats = {
            'database': 'Student_Advising_System',
            'collections': collections,
            'documentCounts': {}
        }
        
        for collection in collections:
            stats['documentCounts'][collection] = db[collection].count_documents({})
        
        return jsonify(parse_json(stats))
    except Exception as e:
        print(f"\n❌ Error in /api/info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_all_students():
    """Get all students with basic information"""
    try:
        if db is None:
            return jsonify({'error': 'Database not connected'}), 500
        
        if 'students' not in db.list_collection_names():
            return jsonify({'error': 'Students collection not found'}), 404
        
        students = list(db.students.find(
            {},
            {
                'studentId': 1,
                'personalInfo.firstName': 1,
                'personalInfo.lastName': 1,
                'personalInfo.email': 1,
                'academicInfo.major': 1,
                'academicInfo.standing': 1,
                'academicInfo.gpa': 1,
                'academicInfo.creditsEarned': 1,
                'advisorId': 1,
                'enrollmentStatus': 1
            }
        ))
        
        return jsonify(parse_json(students))
    except Exception as e:
        print(f"\n❌ Error in /api/students: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advisors', methods=['GET'])
def get_all_advisors():
    """Get all advisors"""
    try:
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
                'personalInfo.department': 1,
                'students': 1
            }
        ))
        
        # Process advisors to ensure department is set
        processed_advisors = []
        for advisor in advisors:
            department = None
            
            if 'department' in advisor and advisor['department']:
                department = advisor['department']
            elif 'personalInfo' in advisor and 'department' in advisor['personalInfo']:
                department = advisor['personalInfo']['department']
            
            if not department:
                department = "Computer Science"

            clean_advisor = {
                'advisorId': advisor.get('advisorId', ''),
                'personalInfo': {
                    'firstName': advisor.get('personalInfo', {}).get('firstName', ''),
                    'lastName': advisor.get('personalInfo', {}).get('lastName', ''),
                    'email': advisor.get('personalInfo', {}).get('email', ''),
                    'department': department 
                },
                'department': department,  
                'students': advisor.get('students', [])
            }
            processed_advisors.append(clean_advisor)
        
        return jsonify(parse_json(processed_advisors))
    except Exception as e:
        print(f"\n❌ Error in /api/advisors: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<student_id>', methods=['GET'])
def get_student_details(student_id):
    """Get detailed student information including advisor and progress"""
    try:
        if db is None:
            return jsonify({'error': 'Database not connected'}), 500
        
        pipeline = [
            {'$match': {'studentId': student_id}},
            {
                '$lookup': {
                    'from': 'advisors',
                    'localField': 'advisorId',
                    'foreignField': 'advisorId',
                    'as': 'advisor'
                }
            },
            {
                '$lookup': {
                    'from': 'academicprogress',
                    'localField': 'studentId',
                    'foreignField': 'studentId',
                    'as': 'progress'
                }
            },
            {
                '$addFields': {
                    'advisor': {
                        '$cond': {
                            'if': {'$isArray': '$advisor'},
                            'then': {'$arrayElemAt': ['$advisor', 0]},
                            'else': None
                        }
                    },
                    'progress': {
                        '$cond': {
                            'if': {'$isArray': '$progress'},
                            'then': {'$arrayElemAt': ['$progress', 0]},
                            'else': None
                        }
                    }
                }
            },
            {
                '$project': {
                    'studentId': 1,
                    'name': {
                        '$concat': [
                            {'$ifNull': ['$personalInfo.firstName', '']},
                            ' ',
                            {'$ifNull': ['$personalInfo.lastName', '']}
                        ]
                    },
                    'email': {'$ifNull': ['$personalInfo.email', '']},
                    'phone': {'$ifNull': ['$personalInfo.phone', '']},
                    'major': {'$ifNull': ['$academicInfo.major', 'Computer Science']},
                    'standing': {'$ifNull': ['$academicInfo.standing', '']},
                    'gpa': {'$ifNull': ['$academicInfo.gpa', 0]},
                    'creditsEarned': {'$ifNull': ['$academicInfo.creditsEarned', 0]},
                    'expectedGraduation': {'$ifNull': ['$academicInfo.expectedGraduation', '']},
                    'enrollmentStatus': {'$ifNull': ['$enrollmentStatus', 'Active']},
                    'advisor': {
                        'name': {
                            '$concat': [
                                {'$ifNull': ['$advisor.personalInfo.firstName', '']},
                                ' ',
                                {'$ifNull': ['$advisor.personalInfo.lastName', '']}
                            ]
                        },
                        'email': {'$ifNull': ['$advisor.personalInfo.email', '']},
                        'department': {'$ifNull': ['$advisor.department', 'Computer Science']}
                    },
                    'currentSemester': {'$ifNull': ['$progress.currentSemester', 'Spring 2026']},
                    'currentCourses': {'$ifNull': ['$progress.degreeProgress.currentSemesterCourses', []]},
                    'totalCreditsEarned': {'$ifNull': ['$progress.degreeProgress.totalCreditsEarned', 0]},
                    'remainingCredits': {'$ifNull': ['$progress.degreeProgress.remainingCredits', 120]}
                }
            }
        ]
        
        result = list(db.students.aggregate(pipeline))
        
        if not result:
            return jsonify({'error': 'Student not found'}), 404
            
        return jsonify(parse_json(result[0]))
        
    except Exception as e:
        print(f"\n❌ Error in /api/students/{student_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/academic-progress', methods=['GET'])
def get_academic_progress():
    """Get all academic progress records"""
    try:
        if db is None:
            return jsonify({'error': 'Database not connected'}), 500
        
        if 'academicprogress' not in db.list_collection_names():
            return jsonify({'error': 'Academic progress collection not found'}), 404
        
        progress = list(db.academicprogress.find(
            {},
            {
                'studentId': 1,
                'catalogYear': 1,
                'currentSemester': 1,
                'degreeProgress.totalCreditsEarned': 1,
                'degreeProgress.remainingCredits': 1,
                'degreeProgress.currentSemesterCourses': 1
            }
        ))
        
        return jsonify(parse_json(progress))
    except Exception as e:
        print(f"\n❌ Error in /api/academic-progress: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/department-stats', methods=['GET'])
def get_department_stats():
    """Get department statistics"""
    try:
        if db is None:
            return jsonify({
                'overview': [{'totalStudents': 0, 'averageGPA': 0, 'honorRoll': 0, 'totalCredits': 0}],
                'byStanding': [],
                'byAdvisor': []
            })
        
        if 'students' not in db.list_collection_names():
            return jsonify({
                'overview': [{'totalStudents': 0, 'averageGPA': 0, 'honorRoll': 0, 'totalCredits': 0}],
                'byStanding': [],
                'byAdvisor': []
            })
        
        pipeline = [
            {
                '$facet': {
                    'overview': [
                        {
                            '$group': {
                                '_id': None,
                                'totalStudents': {'$sum': 1},
                                'averageGPA': {'$avg': '$academicInfo.gpa'},
                                'totalCredits': {'$sum': '$academicInfo.creditsEarned'},
                                'honorRoll': {
                                    '$sum': {
                                        '$cond': [{'$gte': ['$academicInfo.gpa', 3.5]}, 1, 0]
                                    }
                                }
                            }
                        },
                        {
                            '$project': {
                                '_id': 0,
                                'totalStudents': 1,
                                'averageGPA': {'$round': ['$averageGPA', 2]},
                                'totalCredits': 1,
                                'honorRoll': 1
                            }
                        }
                    ],
                    'byStanding': [
                        {
                            '$group': {
                                '_id': '$academicInfo.standing',
                                'count': {'$sum': 1},
                                'avgGPA': {'$avg': '$academicInfo.gpa'}
                            }
                        },
                        {'$sort': {'_id': 1}}
                    ],
                    'byAdvisor': [
                        {
                            '$group': {
                                '_id': '$advisorId',
                                'count': {'$sum': 1}
                            }
                        }
                    ]
                }
            }
        ]
        
        result = list(db.students.aggregate(pipeline))
        
        if result and len(result) > 0 and result[0] is not None:
            return jsonify(parse_json(result[0]))
        
        return jsonify({
            'overview': [{'totalStudents': 0, 'averageGPA': 0, 'honorRoll': 0, 'totalCredits': 0}],
            'byStanding': [],
            'byAdvisor': []
        })
    except Exception as e:
        print(f"\n❌ Error in /api/department-stats: {str(e)}")
        return jsonify({
            'overview': [{'totalStudents': 0, 'averageGPA': 0, 'honorRoll': 0, 'totalCredits': 0}],
            'byStanding': [],
            'byAdvisor': []
        })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("\n" + "="*50)
    print("🚀 Starting Student Advising System")
    print("="*50)
    print(f"📡 Port: {port}")
    print(f"🔗 MongoDB: {'Connected' if db is not None else 'Disconnected'}")
    print(f"📁 Templates: {'Found' if os.path.exists('templates') else 'Missing'}")
    print(f"📁 Static: {'Found' if os.path.exists('static') else 'Missing'}")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)