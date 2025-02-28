import logging
import sqlite3
import sys

from ..config import CACHE_DATABASE, CACHE_INIT_SQL, DATABASE

_conn_list = []
_CACHE_INIT = False


def get_db(*, readonly=False):
    """Gets a Database Connection"""
    if readonly:
        return _get_conn(f"file:{DATABASE}?mode=ro", uri=True)
    return _get_conn(DATABASE)


def get_cache_db():
    """Gets a Cache Database Connection"""
    global _CACHE_INIT  # pylint: disable=global-statement
    conn = _get_conn(CACHE_DATABASE, uri=True)
    if not _CACHE_INIT:
        _CACHE_INIT = True
        try:
            with open(CACHE_INIT_SQL, encoding="UTF-8") as f:
                conn.executescript(f.read())
        except OSError:
            logging.error("Couldn't open Cache Init Script.")
            sys.exit(1)
    return conn


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
