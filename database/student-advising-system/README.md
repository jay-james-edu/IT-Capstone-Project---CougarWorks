# CSU Student Advising Database

The Database Component of the CougarWorks Project. Built with Flask and MongoDB Atlas.

## Overview

This database component serves as the backend for the student advising system, managing:
- Student records and academic information
- Advisor assignments and workloads
- Degree progress tracking
- Department-wide analytics
- Course completion monitoring

## Features

### Database Operations
- **Student Management**: CRUD operations for 120+ student records
- **Advisor Tracking**: Manage advisor-student relationships
- **Degree Progress**: Track completion of 120-credit degree requirements
- **Course History**: Record grades and semester-by-semester progress

### API Endpoints
- **GET /api/students** - Paginated student list with filters
- **GET /api/students/:id** - Complete student profile with advisor
- **GET /api/advisors** - Advisor directory with caseloads
- **GET /api/academic-progress** - Degree completion tracking
- **GET /api/department-stats** - Real-time analytics dashboard

### Data Aggregation
- Department-wide GPA calculations
- Standing distribution analytics
- Advisor workload balancing
- Graduation projection reports
- Course completion rates

## Tech Stack

- **Backend**: Python Flask
- **Database**: MongoDB Atlas

## Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account
- Git

## Installation

## Step 1. **Clone the repository**
   git clone https://github.com/yourusername/student-advising-database.git
  
   cd student-advising-system
   
## Step 2: Set Up Virtual Environment
python -m venv venv

Activate it

venv\Scripts\activate

## Step 3: Install Dependencies

pip install -r requirements.txt

## Step 4: Configure Environment Variables

 Copy example environment file
 
cp .env.example .env

 Edit .env with your MongoDB Atlas credentials
 
Get your connection string from Atlas: Database > Connect > Connect your application

<img width="1235" height="207" alt="Screenshot 2026-02-22 160715" src="https://github.com/user-attachments/assets/4feff052-9dbb-4abc-b4bd-5510ef95826f" />

.env file structure:

MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/Student_Advising_System?retryWrites=true&w=majority
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
PORT=5000

## Step 5: Import Data

 Import the sample data
mongoimport --uri YOUR_ATLAS_URI --collection students --file students.json --jsonArray
mongoimport --uri YOUR_ATLAS_URI --collection advisors --file advisors.json --jsonArray

## Step 6: Run the Application

python app.py

The server will start at http://localhost:5000   

<img width="1421" height="517" alt="Screenshot 2026-02-22 160818" src="https://github.com/user-attachments/assets/831f2a0d-ac1d-4fd1-ad13-ec99d2bca41b" />

# MongoDB Atlas Setup

    Create a cluster at MongoDB Atlas

    Add your IP to the access list

    Create a database user

    Get your connection string

    Add it to .env
