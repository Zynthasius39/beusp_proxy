import beusproxy.services.database as db

from . import chain
from .notify_mgr import NotifyManager


def run_chain(httpc):
    """Worker function

    Args:
        httpc (HTTPClient): HTTP Client
    """
    # Stage 1
    # Bake cookies for students in need
    # Skips students with invalid credentials just in case.
    with db.get_db() as conn:
        chain.authorize_subs(conn, httpc)

    # Stage 2
    # Fetch grades and compare against database
    # Notify subscribers asynchronously
    with db.get_db() as conn, NotifyManager(httpc) as nmgr:
        chain.check_grades(conn, httpc, nmgr)
