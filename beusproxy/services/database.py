import sqlite3

from ..config import DATABASE

_conn_list = []


def get_db(*, readonly=False):
    """Gets a Database Connection"""
    if readonly:
        return _get_conn(f"file:{DATABASE}?mode=ro", uri=True)
    return _get_conn(DATABASE)


def _get_conn(conn_str, *, uri=False):
    """Gets a Database Connection"""
    conn = sqlite3.connect(conn_str, uri=uri)
    conn.row_factory = sqlite3.Row
    _conn_list.append(conn)
    return conn


def clean():
    """Clean Connection Pool"""
    for conn in _conn_list:
        conn.close()
