import json
import logging
from datetime import datetime

from jsondiff import diff

from beusproxy.config import API_HOSTNAME, HOST, USER_AGENT

from ..common.utils import grade_diff


def check_grades(cconn, httpc):
    """Fetch grades and compare"""
    # Fetch grades json from db
    subs = cconn.execute(
        """
        SELECT
            owner_id,
            session_id
        FROM
            Student_Sessions
        WHERE
            expired == 0;
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
    httpc.gather(
        *[grades_coro(cr_dict, sub["owner_id"], sub["session_id"]) for sub in subs]
    )

    async def grades_json_coro(cr, sub_id, sub_grades_cr):
        if sub_grades_cr.status == 200:
            cr[sub_id] = await sub_grades_cr.json(
                encoding="UTF-8", loads=json.loads, content_type="application/json"
            )
        elif sub_grades_cr.status == 401:
            cr[sub_id] = 401

    httpc.gather(
        *[
            grades_json_coro(cr_dict, sub_id, sub_grades_cr)
            for sub_id, sub_grades_cr in cr_dict.items()
        ]
    )

    subs_grades_old = cconn.execute(
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
        if sub_grades and subs_grades_old_dict.get(sub_id):
            # Write notes and changes back to db
            if sub_grades == 401:
                res = cconn.execute(
                    """
                    UPDATE Student_Sessions
                    SET expired = 1
                    WHERE owner_id = ?;
                """,
                    sub_id,
                )
                if res.rowcount <= 0:
                    logging.error("No session for %d", sub_id)
                    cconn.revert()
                cconn.commit()
                continue
            grade_diff(sub_grades, json.loads(subs_grades_old_dict[sub_id]))
        json_grades = json.dumps(sub_grades)
        res = cconn.execute(
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
    cconn.commit()
    # Set expired sessions
