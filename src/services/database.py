import sqlite3

def get_db():
    """Get a SQLite database connection"""
    db = sqlite3.connect("beusp.db")
    db.row_factory = sqlite3.Row

    return db
