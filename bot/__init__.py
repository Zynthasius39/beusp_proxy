import beusproxy.services.database as db

from . import chain


def run_chain():
    """Worker function

    Args:
    """
    # Stage 1
    # Bake cookies for students in need
    # Skips students with invalid credentials just in case.
    with db.get_db() as conn:
        chain.authorize_subs(conn)

    # Stage 2
    # Fetch grades and compare against database
    # Notify subscribers asynchronously
    with db.get_db() as conn:
        chain.check_grades(conn)
