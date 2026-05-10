# CougarWorks

CougarWorks is a Flask and MongoDB web application inspired by DegreeWorks for academic advising and student degree monitoring. The app provides role-based portals for students, advisors, and administrators so users can review degree progress, manage advisor assignments, track notes, and schedule advising meetings.

## Team Members

> Add each member's GitHub username before final submission.

- Najwa Aissaoui — Project Manager / Frontend Developer — GitHub: `@najsahar`
- CJ Hickson — Backend Developer / Database Designer — GitHub: `@cjspersona`
- James Jay — Backend Developer / Database Designer / UX Design — GitHub: `@jay-james-edu`

## Technology Stack

- **Programming language:** Python 3.11
- **Backend framework:** Flask 3.0
- **WSGI server:** Gunicorn
- **Database:** MongoDB 7
- **Authentication/security:** Flask sessions and bcrypt password hashing
- **Frontend:** HTML, CSS, Jinja2 templates, vanilla JavaScript
- **Containerization:** Docker and Docker Compose
- **Deployment platform:** Local Docker deployment by default; adaptable to Render, Railway, Heroku, AWS, or another container host

## Project Objectives Assessment

This section is based on the original project proposal for the Student Advising and Degree Tracking Platform. Each objective below uses the proposal's original wording and explains how the current CougarWorks implementation addresses it.

### Objective 1: Design a web-based application that students and advisors can easily use

**Status:** Met

**Explanation:** CougarWorks provides a browser-based Flask application with separate dashboards and navigation for students, advisors, and administrators. Students can access degree-progress pages, remaining-course views, advising notes, and profile information, while advisors can manage assigned students, notes, and meetings from their own interface.

### Objective 2: Design and implement a database to store students, advisors, courses and degree requirements.

**Status:** Met

**Explanation:** The application uses MongoDB collections for students, advisors, admins, degree requirements, academic progress, advising notes, and meetings. The release now includes fake/demo JSON seed files in `database/seeds/` and import scripts so a new user can populate their own local MongoDB instance without relying on raw database storage files or shared credentials.

### Objective 3: Allow students to view completed courses and remaining degree requirements in real time.

**Status:** Partially Met

**Explanation:** Student users can view their completed coursework, degree progress, GPA standing, and remaining degree requirements through the student dashboard and related pages. This objective is marked partially met because the project currently updates from stored MongoDB records when pages are loaded rather than using a live institutional system or continuous real-time synchronization.

### Objective 4: Allow advisors to create, view, and manage advising notes for students.

**Status:** Met

**Explanation:** Advisor users can open assigned student records, view existing advising notes, add new notes, and delete or manage notes through the advisor interface. The notes are stored persistently in MongoDB and can be referenced later by advisors and students as part of the advising workflow.

## Installation Instructions

### Prerequisites

Install the following before running the project:

- Docker Desktop or Docker Engine
- Docker Compose v2
- Git

For running without Docker, install:

- Python 3.11+
- MongoDB 7+

### Docker setup

1. Clone the repository:

   ```bash
   git clone https://github.com/jay-james-edu/IT-Capstone-Project---CougarWorks.git
   cd cougarworks
   ```

2. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and replace placeholder values such as `SECRET_KEY` and `MONGO_PASS`.

4. Build and start the containers:

   ```bash
   docker compose -f compose.yml up --build
   ```

5. Open the app in your browser:

   ```text
   http://localhost:5000
   ```

### Local setup without Docker

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start or connect to MongoDB.

4. Create a `.env` file using `.env.example` as the template and set `MONGO_URI` for your local MongoDB connection.

5. Run the Flask app:

   ```bash
   cd src
   python app.py
   ```

## Database Setup

This release uses JSON seed files instead of committing MongoDB's raw `mongo_data/` storage folder. That is the better GitHub release format because each person who downloads the repo can import the fake/demo data into their own local MongoDB database using their own username and password.

When using Docker Compose for the first time, MongoDB is initialized automatically from `mongo-init/init.js`. The initialization script creates the application collections and indexes only. To load the demo project records, run one of the seed import scripts below after MongoDB starts.

The fake/demo project records are included as importable JSON files in `database/seeds/`:

- `admins.json`
- `advisors.json`
- `students.json`
- `degreerequirements.json`
- `academicprogress.json`

To manually import the seed JSON into a running MongoDB instance, start MongoDB and run:

```bash
docker compose -f compose.yml up -d mongo
./scripts/import_seed.sh
```

On Windows PowerShell:

```powershell
docker compose -f compose.yml up -d mongo
.\scripts\import_seed.ps1
```

The import scripts use the same default demo values from `compose.yml`. If you change `MONGO_USER`, `MONGO_PASS`, or `MONGO_DB_NAME` in `.env`, use the same values when importing.

Demo local accounts:

| Role | Example Email | Password |
|---|---|---|
| Admin | `jennifer.adams@columbusstate.edu` | `admin123` |
| Advisor | `robert.wilson@advisors.columbusstate.edu` | `advisor123` |
| Student | `john.doe@students.columbusstate.edu` | `student123` |

Change these demo passwords before using the project outside a local class demonstration.

## Configuration Requirements

Do not commit real secrets or production credentials. Use `.env.example` as the public template and keep your real `.env` file local.

Important environment variables:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing key |
| `MONGO_USER` | MongoDB username |
| `MONGO_PASS` | MongoDB password |
| `MONGO_HOST` | MongoDB hostname |
| `MONGO_PORT` | MongoDB port |
| `MONGO_DB_NAME` | Application database name |
| `MONGO_URI` | Full MongoDB connection string |

## Usage Instructions

1. Go to `http://localhost:5000`.
2. Log in with one of the demo accounts or an account created by an admin.
3. Admin users can add students/advisors and assign students to advisors.
4. Advisor users can view assigned advisees, manage advising notes, and schedule meetings.
5. Student users can view their dashboard, profile, degree progress, remaining courses, and GPA standing.


## Repository Structure

```text
.
├── Dockerfile
├── README.md
├── compose.yml
├── mongo-init/
│   └── init.js
├── nginx.conf
├── requirements.txt
└── src/
    ├── app.py
    ├── routes/
    ├── static/
    ├── templates/
    └── utils/
```
