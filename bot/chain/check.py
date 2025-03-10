import json
import logging
import sys
from datetime import datetime
from json import JSONDecodeError

from aiohttp import ClientError

from beusproxy.config import API_HOSTNAME, HOST, USER_AGENT

from ..common.utils import grade_diff

logger = logging.getLogger(__package__)

def check_grades(conn, httpc, nmgr):
    """Fetch grades and compare

    Args:
        conn (sqlite3.Connection): MainDB Connection
        httpc (HTTPClient): HTTP Client
        nmgr (NotifyManager): Notification Manager
    """
    # Fetch grades json from db
    subs = conn.execute(
        """
        SELECT
            owner_id,
            session_id
        FROM
            Student_Sessions
        WHERE
            logged_out == 0;
    """
    ).fetchall()

    async def grades_coro(cr, owner_id, session_id):
        cr[owner_id] = await httpc.request_coro(
            "GET",
            f"{API_HOSTNAME}resource/grades/latest",
            headers={
                "Host": HOST,
                "Cookie": f"SessionID={session_id};",
                "User-Agent": USER_AGENT,
            },
        )

    # Fetch grades via API
    cr_dict = {}
    try:
        httpc.gather(
            *[grades_coro(cr_dict, sub["owner_id"], sub["session_id"]) for sub in subs]
        )
    except ClientError as e:
        logger.error(e)
        sys.exit(1)

    async def grades_json_coro(cr, sub_id, sub_grades_cr):
        if sub_grades_cr.status == 200:
            cr[sub_id] = await sub_grades_cr.json(
                encoding="UTF-8", loads=json.loads, content_type="application/json"
            )
        else:
            cr[sub_id] = sub_grades_cr.status

    try:
        httpc.gather(
            *[
                grades_json_coro(cr_dict, sub_id, sub_grades_cr)
                for sub_id, sub_grades_cr in cr_dict.items()
            ]
        )
    except ClientError as e:
        logger.error(e)
        sys.exit(1)

    subs_grades_old = conn.execute(
        """
        SELECT
            owner_id,
            grades
        FROM
            Student_Grades;
    """
    ).fetchall()

    subs_grades_old_dict = {}
    for sub_id, sub_grades in dict(subs_grades_old).items():
        subs_grades_old_dict[sub_id] = sub_grades
    # Compare grades wisely
    for sub_id, sub_grades in cr_dict.items():
        if isinstance(sub_grades, int):
            logger.error("Invalid response %d for %d", sub_grades, sub_id)
            continue
        if sub_grades and subs_grades_old_dict.get(sub_id):
            # Grade diff util
            try:
                diffs = grade_diff(json.loads(
                    subs_grades_old_dict[sub_id]), sub_grades)
                if len(diffs) != 0:
                    logger.debug(
                        "Changes found for Sub %d: %s", sub_id, json.dumps(
                            diffs, indent=1)
                    )
            except JSONDecodeError as e:
                logger.error("Couldn't decode JSON from DB for Sub %d", sub_id)

            # Push to notifier
            # nmgr.notify(sub_id, diffs)
        json_grades = json.dumps(sub_grades)

        # Write notes and changes back to db
        cur = conn.execute(
            """
            REPLACE INTO Student_Grades (
                owner_id, grades, updated
            )
            VALUES (
                ?, ?, ?
            );
        """,
            (sub_id, json_grades, datetime.now().isoformat()),
        )
        if cur.rowcount > 0:
            conn.commit()
        else:
            conn.rolback()
