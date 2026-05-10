import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from bson import ObjectId
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

_db_client = None
_db = None


def init_db():
    """Initialize the database connection."""
    global _db_client, _db

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/cougarworks')

    try:
        _db_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=3000,
            socketTimeoutMS=3000
        )

        # Test connection
        _db_client.admin.command('ping')
        _db = _db_client.get_database()

        # Initialize collections
        _init_collections()

        logger.info(f"Connected to MongoDB: {_db.name}")
        return True

    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return False


def _init_collections():
    """Initialize database collections with indexes."""
    if _db is None:
        return


    _db.students.create_index('studentId', unique=True)
    _db.students.create_index('email', unique=True, sparse=True)
    _db.students.create_index('academicInfo.major')
    _db.students.create_index('academicInfo.classification')


    _db.advisors.create_index('advisorId', unique=True)
    _db.advisors.create_index('email', unique=True, sparse=True)

    _db.admins.create_index('adminId', unique=True)
    _db.admins.create_index('email', unique=True, sparse=True)

    _db.academicprogress.create_index('studentId', unique=True)
    _db.academicprogress.create_index('lastUpdated')

    _db.degreerequirements.create_index('major')
    _db.degreerequirements.create_index('catalogYear')

    logger.info("Database indexes created")


def get_db():
    """Get the database connection."""
    global _db

    if _db is None:
        init_db()

    return _db


def close_db():
    """Close the database connection."""
    global _db_client, _db

    if _db_client is not None:
        _db_client.close()
        _db_client = None
        _db = None
        logger.info("Database connection closed")



def parse_json(data):
    """Convert MongoDB BSON types to JSON-serializable formats."""
    if isinstance(data, list):
        return [parse_json(item) for item in data]
    elif isinstance(data, dict):
        return {key: parse_json(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, bytes):
        return data.decode('utf-8', errors='ignore')
    else:
        return data

def create_student(student_data):
    """Create a new student record."""
    db = get_db()
    if db is None:
        return None, "Database connection error"

    try:
        # Add timestamps
        student_data['createdAt'] = datetime.utcnow()
        student_data['updatedAt'] = datetime.utcnow()

        result = db.students.insert_one(student_data)
        return result.inserted_id, None
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        return None, str(e)


def get_student(student_id):
    """Get a student by ID."""
    db = get_db()
    if db is None:
        return None

    try:
        # Try by ObjectId first, then by studentId
        if ObjectId.is_valid(student_id):
            return db.students.find_one({'_id': ObjectId(student_id)})
        return db.students.find_one({'studentId': student_id})
    except Exception as e:
        logger.error(f"Error getting student: {e}")
        return None


def get_students(filters=None, limit=100, skip=0):
    """Get multiple students with optional filters."""
    db = get_db()
    if db is None:
        return []

    query = filters or {}

    try:
        cursor = db.students.find(query).skip(skip).limit(limit)
        return list(cursor)
    except Exception as e:
        logger.error(f"Error getting students: {e}")
        return []


def update_student(student_id, update_data):
    """Update a student record."""
    db = get_db()
    if db is None:
        return False, "Database connection error"

    try:
        update_data['updatedAt'] = datetime.utcnow()

        result = db.students.update_one(
            {'studentId': student_id},
            {'$set': update_data}
        )
        return result.modified_count > 0, None
    except Exception as e:
        logger.error(f"Error updating student: {e}")
        return False, str(e)


def delete_student(student_id):
    """Delete a student record."""
    db = get_db()
    if db is None:
        return False, "Database connection error"

    try:
        result = db.students.delete_one({'studentId': student_id})
        return result.deleted_count > 0, None
    except Exception as e:
        logger.error(f"Error deleting student: {e}")
        return False, str(e)


def get_advisor(advisor_id):
    """Get an advisor by ID."""
    db = get_db()
    if db is None:
        return None

    try:
        if ObjectId.is_valid(advisor_id):
            return db.advisors.find_one({'_id': ObjectId(advisor_id)})
        return db.advisors.find_one({'advisorId': advisor_id})
    except Exception as e:
        logger.error(f"Error getting advisor: {e}")
        return None


def get_degree_requirements(major, catalog_year=None):
    """Get degree requirements for a major."""
    db = get_db()
    if db is None:
        return None

    query = {'major': major}
    if catalog_year:
        query['catalogYear'] = catalog_year

    try:
        return db.degreerequirements.find_one(query)
    except Exception as e:
        logger.error(f"Error getting degree requirements: {e}")
        return None


def get_academic_progress(student_id):
    """Get academic progress for a student."""
    db = get_db()
    if db is None:
        return None

    try:
        return db.academicprogress.find_one({'studentId': student_id})
    except Exception as e:
        logger.error(f"Error getting academic progress: {e}")
        return None


def update_academic_progress(student_id, progress_data):
    """Update academic progress for a student."""
    db = get_db()
    if db is None:
        return False

    try:
        progress_data['lastUpdated'] = datetime.utcnow()

        result = db.academicprogress.update_one(
            {'studentId': student_id},
            {'$set': progress_data},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error updating academic progress: {e}")
        return False
