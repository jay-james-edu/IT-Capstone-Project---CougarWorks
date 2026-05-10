# Database Seed Data

This folder contains the fake/demo CougarWorks MongoDB seed data exported as JSON files. It is safer and easier for GitHub users than committing MongoDB's raw `mongo_data/` storage folder, because each developer can import the JSON into their own local MongoDB instance with their own username and password.

## Collections

- `admins.json`
- `advisors.json`
- `students.json`
- `degreerequirements.json`
- `academicprogress.json`

The main project data came from the exported CougarWorks collections for students, advisors, admins, degree requirements, and academic progress.

## Import with Docker Compose

1. Start MongoDB:

   ```bash
   docker compose -f compose.yml up -d mongo
   ```

2. Import the demo data:

   ```bash
   ./scripts/import_seed.sh
   ```

   On Windows PowerShell:

   ```powershell
   .\scripts\import_seed.ps1
   ```

The scripts use the same default demo credentials as `compose.yml`. If you change `MONGO_USER`, `MONGO_PASS`, or `MONGO_DB_NAME` in `.env`, set those same environment variables before running the import script.

## Demo Logins

| Role | Example Email | Password |
|---|---|---|
| Admin | `jennifer.adams@columbusstate.edu` | `admin123` |
| Advisor | `robert.wilson@advisors.columbusstate.edu` | `advisor123` |
| Student | `john.doe@students.columbusstate.edu` | `student123` |

Change these demo passwords before using the project outside a local class demonstration.
