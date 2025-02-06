import sqlite3

from config import DATABASE

def get_db():
    """Get a SQLite database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row

    return db
