DROP TABLE IF EXISTS Students;
DROP TABLE IF EXISTS Student_Sessions;
DROP TABLE IF EXISTS Telegram_Subscribers;
DROP TABLE IF EXISTS Discord_Subscribers;
DROP TABLE IF EXISTS Email_Subscribers;
DROP TABLE IF EXISTS Verifications;

CREATE TABLE Students(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	student_id INTEGER(9) NOT NULL UNIQUE,
	password TEXT NOT NULL,
	active_telegram_id INTEGER,
	active_discord_id INTEGER,
	active_email_id INTEGER
);

CREATE TABLE Student_Sessions(
	owner_id INTEGER,
	session_id VARCHAR(32) NOT NULL,
	login_date TEXT,
	logged_out BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE Telegram_Subscribers(
	owner_id INTEGER,
	telegram_id INTEGER PRIMARY KEY AUTOINCREMENT,
	telegram_username TEXT NOT NULL,
	telegram_chat_id INTEGER NOT NULL,
	FOREIGN KEY(owner_id) REFERENCES Students(id)
);

CREATE TABLE Discord_Subscribers(
	owner_id INTEGER,
	discord_id INTEGER PRIMARY KEY AUTOINCREMENT,
	discord_webhook_url TEXT NOT NULL,
	FOREIGN KEY(owner_id) REFERENCES Students(id)
);

CREATE TABLE Email_Subscribers(
	owner_id INTEGER,
	email_id INTEGER PRIMARY KEY AUTOINCREMENT,
	email TEXT NOT NULL,
	FOREIGN KEY(owner_id) REFERENCES Students(id)
);

CREATE TABLE Verifications(
	owner_id INTEGER NOT NULL,
	verify_code VARCHAR(9) NOT NULL,
	verify_item TEXT NOT NULL,
	verify_service INTEGER(3) NOT NULL,
	verify_date TEXT,
	verified BOOLEAN NOT NULL DEFAULT 0,
	FOREIGN KEY(owner_id) REFERENCES Students(id)
);
