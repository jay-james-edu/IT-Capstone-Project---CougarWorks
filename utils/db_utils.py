import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import json_util
import json

# MongoDB connection settings
MONGODB_URI = "mongodb://localhost:27017/"
client = None
db = None
connection_status = 'disconnected'

def parse_json(data):
    """Convert MongoDB ObjectId to string for JSON serialization"""
    return json.loads(json_util.dumps(data))

def connect_to_mongo(): 
    """Establish connection to MongoDB"""
    global client, db, connection_status

    try:
        client = MongoClient("mongodb://localhost:27017/", 
                            serverSelectionTimeoutMS=5000,
                            connectTimeoutMS=5000)

        # Test the connection
        client.admin.command('ping')

        db = client['Student_Advising_System']
        connection_status = 'connected'

        collections = db.list_collection_names()

        try:
            if 'students' in collections:
                index_names = [idx['name'] for idx in db.students.list_indexes()]

                if 'studentId_1' not in index_names and 'Student ID' not in index_names:
                    db.students.create_index('studentId', unique=True, name='studentId_1')
                    print('Created index: studentId_1\n')

            if 'advisors' in collections:
                index_names = [idx['name'] for idx in db.advisors.list_indexes()]

                if 'advisorId_1' not in index_names and 'Advisor ID' not in index_names:
                    db.advisors.create_index('advisorId', unique=True, name='advisorId_1')
                    print('Created index: advisorId_1\n')
        except Exception as e:
            print(f'⚠️ Index check: {e}')

        return True
    except ConnectionFailure as e:
        connection_status = 'error'
        print('\n❌ MongoDB connection error:')
        print(f'   Error details: {e}')
        return False
    except Exception as e:
        connection_status = 'error'
        print(f'\n❌ Unexpected error: {e}')
        return False

def get_db():
    """Get database instance"""
    return db

def is_connected():
    """Check if database is connected"""
    return connection_status == 'connected' and db is not None
