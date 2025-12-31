import asyncio
import json
import logging
import os
import random
import sqlite3
import requests
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from dateutil import parser
from flask import abort, g, logging as flogging

from ..config import DATABASE, DEMO_FOLDER, HOST, ROOT, USER_AGENT, REQUEST_TIMEOUT
from ..services.email import EmailClient

def get_logger(name=None):
    """Get a logger

    Args:
        name (str): Logger name

    Returns:
        Logger: Logger
    """
    logger = logging.getLogger(name)
    logger.addHandler(flogging.default_handler)
    return logger


def get_db():
    """Get a database connection.
    Create one if doesn't exist in appcontext.
    """
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def get_emailc():
    """Get an email client.
    Create one if doesn't exist in appcontext.
    """
    emailc = getattr(g, "_emailc", None)
    if emailc is None:
        emailc = g._database = EmailClient()
    return emailc


def read_announce(sessid):
    """Read announces of student

    Args:
        sessid (str): Student session_id
    """
    requests.request(
        "POST",
        ROOT,
        data={
            "btnRead": "Oxudum",
        },
        headers={
            "Host": HOST,
            "Cookie": f"PHPSESSID={sessid}; uname=240218019; BEU_STUD_AR=0; ",
            "User-Agent": USER_AGENT,
        },
        timeout=REQUEST_TIMEOUT,
    )


def read_msgs(sessid, msg_ids):
    """Read messages of student

    Args:
        sessid (str): Student session_id
        msg_ids (list): List of message ids to be read

    Returns:
        list: List of responses
    """

    async def read_msgs_coro():
        async with aiohttp.ClientSession() as httpc:
            results = await asyncio.gather(
                *[
                    httpc.request(
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

            msgs_raw = []
            for res in results:
                if res.status == 200:
                    msgs_raw.append(await res.text())

            return msgs_raw

    return asyncio.run(read_msgs_coro())

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
        abort(503, help=f"Resource '{res}.json' doesn't exist")

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


def parse_date(
    date, frmt=None, *, default=datetime(1970, 1, 1), no_format=False
) -> str | datetime:
    """Parse weirdly formatted date into readable format
    Returns same date, if format is not recognized.

    Args:
        date (str): Input date
        frmt (str): Input format
        default (datetime): Default date to add on top of
        no_format (bool): Return datetime instead if true

    Returns:
        str: Output date in isoformat or given format
        datetime: Output datetime
    """
    date = date.replace(" PM", "").replace("AM", "")
    try:
        date = parser.parse(date, default=default)
        if no_format:
            return date
        if not frmt:
            dt = date.isoformat()
        else:
            dt = date.strftime(frmt)
    except ValueError:
        if no_format:
            return default
        dt = date

    # Clear unnecessary segments.
    dt = dt.replace("T00:00:00", "").replace("1970-", "")
    return dt
