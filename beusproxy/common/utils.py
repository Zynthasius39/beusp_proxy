import json
import os
import random
import sqlite3
from datetime import datetime
from dateutil import parser

from bs4 import BeautifulSoup
from flask import g, abort

from ..config import DATABASE, DEMO_FOLDER, HOST, ROOT, USER_AGENT
from ..services.httpclient import HTTPClient


def get_db():
    """Get a database connection.
    Create one if doesn't exist in appcontext.
    """
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def read_announce(http_client: HTTPClient, sessid):
    """Read announces of student

    Args:
        sessid (str): Student session_id
    """
    http_client.request(
        "POST",
        f"{ROOT}stud_announce.php",
        data="btnRead=Oxudum",
        headers={
            "Host": HOST,
            "Cookie": f"PHPSESSID={sessid}; ",
            "User-Agent": USER_AGENT,
        },
    )


def read_msgs(http_client: HTTPClient, sessid, msg_ids):
    """Read messages of student

    Args:
        sessid (str): Student session_id
        msg_ids (list): List of message ids to be read

    Returns:
        list: List of responses
    """

    return http_client.gather(
        *[
            http_client.request_coro(
                "POST",
                ROOT,
                data={
                    "ajx": 1,
                    "mod": "msg",
                    "action": "ShowReceivedMessage",
                    "sm_id": id,
                },
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={sessid}; ",
                    "User-Agent": USER_AGENT,
                },
            )
            for id in msg_ids
        ]
    )


def verify_code_gen(length):
    """Generate verification code of given length

    Args:
        length (int): Length of desired code

    Returns:
        str: Randomly generated code in given length
    """
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def read_json_file(path):
    """Read JSON file in the given path

    Args:
        path (str): File path

    Returns:
        str: File contents
    """

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def demo_response(res):
    """Return a demo response

    Args:
        res (str): Resource

    Returns:
        dict: JSON
    """
    file = os.path.join(DEMO_FOLDER, f"{res}.json")
    if not os.path.exists(file):
        abort(503, help=f"Resource '{res}.json' doesn't exists")

    with open(file, "r", encoding="UTF-8") as f:
        return json.load(f)


def is_expired(html):
    """Check if session is expired

    Args:
        html (str): HTML input

    Returns:
        bool: Whether the session is expired
    """
    # Check if session is expired.
    # When it is, response will consist of this abomination.
    if (
        html == "#!3%6$#@458#!2*/-&2@"
        or not html.find("Daxil ol - Tələbə Məlumat Sistemi") == -1
    ):
        return True
    return False


def is_announce(html):
    """Check if page is an announce page

    Args:
        html (str): HTML input

    Returns:
        bool: If it is an announcment
    """
    # Checking for stud_announce string.
    if not html.find("stud_announce") == -1:
        return True
    return False


def is_there_msg(html):
    """Check if there is a message

    Args:
        html (str): HTML input

    Returns:
        bool: Whether there is a message
    """
    soup = BeautifulSoup(html, "html.parser")

    # Checking if span with given attributes exist.
    if soup.find("span", attrs={"style": "color:#1E1E1E ;font-weight:bold"}):
        return True
    return False


def is_invalid(html):
    """Check if HTML is invalid
    Used before understanding the bad design of student portal

    Args:
        html (str): HTML input

    Returns:
        dict: JSON output
    """
    if html.find("<html>") != -1:
        return True
    return False

def parse_date(date, frmt=None, *, default=datetime(1970, 1, 1)):
    """Parse weirdly formatted date into readable format
    Returns same date, if format is not recognized.

    Args:
        format (str): Input format
        date (str): Input date

    Returns:
        str: Output date
    """
    date = date.replace(" PM", "").replace("AM", "")
    try:
        date = parser.parse(date, default=default)
        if not frmt:
            dt = date.isoformat()
        else:
            dt = date.strftime(frmt)
    except ValueError:
        dt = date

    # Clear unnecessary segments.
    dt = dt.replace("T00:00:00", "").replace("1970-", "")
    return dt
