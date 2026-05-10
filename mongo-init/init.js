const appDbName = process.env.MONGO_INITDB_DATABASE || 'CougarWorks';
db = db.getSiblingDB(appDbName);

// Create the application collections used by CougarWorks.
[
  'admins',
  'advisors',
  'students',
  'academicprogress',
  'degreerequirements',
  'studentNotes',
  'meetings'
].forEach((name) => {
  if (!db.getCollectionNames().includes(name)) {
    db.createCollection(name);
  }
});

// Helpful indexes for login, lookup, advisor dashboards, and degree progress pages.
db.admins.createIndex({ adminId: 1 }, { unique: true });
db.admins.createIndex({ email: 1 }, { unique: true, sparse: true });
db.advisors.createIndex({ advisorId: 1 }, { unique: true });
db.advisors.createIndex({ email: 1 }, { unique: true, sparse: true });
db.students.createIndex({ studentId: 1 }, { unique: true });
db.students.createIndex({ email: 1 }, { unique: true, sparse: true });
db.students.createIndex({ 'academicInfo.advisor': 1 });
db.academicprogress.createIndex({ studentId: 1 }, { unique: true });
db.degreerequirements.createIndex({ major: 1, catalogYear: 1 });
db.studentNotes.createIndex({ studentId: 1 });
db.studentNotes.createIndex({ advisorId: 1 });
db.meetings.createIndex({ advisorId: 1, scheduledDate: 1 });
db.meetings.createIndex({ studentId: 1, scheduledDate: 1 });

print(`CougarWorks database '${appDbName}' initialized. Import demo data with scripts/import_seed.sh or scripts/import_seed.ps1.`);
