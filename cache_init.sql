DROP TABLE IF EXISTS Student_Subscribers;
DROP TABLE IF EXISTS Student_Sessions;
DROP TABLE IF EXISTS Student_Grades;

CREATE TABLE Student_Subscribers (
  sub_id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER(9) NOT NULL UNIQUE,
  password TEXT NOT NULL,
  active_telegram_id INTEGER,
  active_discord_id INTEGER,
  active_email_id INTEGER
);

CREATE TABLE Student_Sessions (
	owner_id INTEGER PRIMARY KEY,
	session_id VARCHAR(32) NOT NULL,
	expired BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE Student_Grades (
  owner_id INTEGER PRIMARY KEY,
  grades TEXT NOT NULL DEFAULT "{}",
  updated TEXT
);
