import time

import beusproxy.services.database as db
from beusproxy.services.httpclient import HTTPClient

from . import chain


def run_chain():
    """Worker function"""
    with db.get_cache_db() as cconn:
        # Stage 1
        # Fetch subscribed students
        mconn = db.get_db(readonly=True)
        chain.fetch_subs(cconn, mconn)
        mconn.close()

        # Stage 2
        # Bake cookies for students in need
        # Skips students with invalid credentials just in case.
        httpc = HTTPClient()
        chain.authorize_subs(cconn, httpc)

        # Stage 3
        # Fetch grades and compare against database
        chain.check_grades(cconn, httpc)
        httpc.close()

        # Stage 4
        # Notify subscribers with visual cards
