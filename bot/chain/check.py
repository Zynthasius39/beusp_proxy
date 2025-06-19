import json
import requests
import socket
from datetime import datetime
from json import JSONDecodeError
from asyncio import TimeoutError as AsyncioTimeoutError
from smtplib import SMTPException

from aiohttp import ClientError

from beusproxy.common.utils import get_logger
from beusproxy.config import API_INTERNAL_HOSTNAME, DEBUG, HOST, USER_AGENT
from beusproxy.services.email import EmailClient

from ..common.utils import grade_diff
from ..common.debug import log4grades

logger = get_logger(__package__)


def check_grades(conn, httpc, nmgr):
    """Fetch grades and compare

    Args:
        conn (sqlite3.Connection): MainDB Connection
        httpc (HTTPClient): HTTP Client
        emailc (EmailClient): Email Client
        nmgr (NotifyManager): Notification Manager
    """
    sub = conn.execute(
        """
        SELECT
            id,
            session_id
        FROM (
          SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY
                    s.id
                ORDER BY
                    ses.login_date DESC
            ) rn
          FROM Students s
          INNER JOIN Student_Sessions ses
          ON
            s.id == ses.owner_id AND
            ses.logged_out == 0
        ) t
        WHERE rn = 1 AND id = 1;
    """
    ).fetchone()

    if sub:
        sub_res = requests.get(
            f"{API_INTERNAL_HOSTNAME}resource/grades/latest",
            headers={
                "Cookie": f"SessionID={sub["session_id"]};",
                "User-Agent": USER_AGENT,
            },
        )
        if sub_res.status_code == 401:
            cur = conn.execute(
                """
                UPDATE
                    Student_Sessions
                SET
                    logged_out = 1
                WHERE
                    owner_id = 1;
            """)
            if cur.rowcount > 0:
                conn.commit()
            else:
                conn.rollback()
        with open("log/grades_history_sub1.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] - {sub_res.status_code} : {sub_res.text}")
    else:
        return

    # async def grades_coro(cr, owner_id, session_id):
    #     cr[owner_id] = await httpc.request_coro(
    #         "GET",
    #         f"{API_INTERNAL_HOSTNAME}resource/grades/latest",
    #         headers={
    #             "Host": HOST,
    #             "Cookie": f"SessionID={session_id};",
    #             "User-Agent": USER_AGENT,
    #         },
    #     )

    # # Fetch grades via API
    # cr_dict = {}
    # try:
    #     httpc.gather(
    #         *[grades_coro(cr_dict, sub["id"], sub["session_id"]) for sub in subs]
    #     )
    # except (AsyncioTimeoutError, TimeoutError, ClientError) as e:
    #     logger.error(e)
    #     return

    # async def grades_json_coro(cr, sub_id, sub_grades_cr):
    #     if sub_grades_cr.status == 200:
    #         cr[sub_id] = await sub_grades_cr.json(
    #             encoding="UTF-8", loads=json.loads, content_type="application/json"
    #         )
    #     else:
    #         cr[sub_id] = sub_grades_cr.status

    # try:
    #     httpc.gather(
    #         *[
    #             grades_json_coro(cr_dict, sub_id, sub_grades_cr)
    #             for sub_id, sub_grades_cr in cr_dict.items()
    #         ]
    #     )
    # except ClientError as e:
    #     logger.error(e)
    #     return

    # subs_grades_old = conn.execute(
    #     """
    #     SELECT
    #         sg.owner_id,
    #         sg.grades
    #     FROM
    #         Student_Grades sg
    #     INNER JOIN
    #         Students s
    #     ON
    #         sg.owner_id == s.id AND
    #         NOT (
    #             s.active_telegram_id IS NULL AND
    #             s.active_discord_id IS NULL AND
    #             s.active_email_id IS NULL
    #         );
    # """
    # ).fetchall()

    # # Get a EmailClient
    # try:
    #     emailc = EmailClient()
    # except (SMTPException, socket.gaierror, OSError) as e:
    #     logger.error(f"emailc: {e}")
    #     return

    # # Compare grades wisely
    # for sub_id, sub_grades in cr_dict.items():
    # if isinstance(sub_grades, int):
    #     if sub_grades == 401:
    #         cur = conn.execute(
    #             """
    #             UPDATE
    #                 Student_Sessions
    #             SET
    #                 logged_out = 1
    #             WHERE
    #                 owner_id = ?;
    #         """,
    #             (sub_id,),
    #         )
    #         if cur.rowcount > 0:
    #             conn.commit()
    #         else:
    #             conn.rollback()
    #     logger.error("Invalid response %d for %d", sub_grades, sub_id)
    #     continue
    #     if sub_grades and dict(subs_grades_old).get(sub_id):
    #         # Grade diff util
    #         try:
    #             diffs = grade_diff(
    #                 json.loads(dict(subs_grades_old)[sub_id]), sub_grades
    #             )
    #             if len(diffs) != 0:
    #                 # Push to notifier
    #                 nmgr.notify(sub_id, diffs, sub_grades, emailc=emailc)
    #                 logger.debug(
    #                     "Changes found for Sub %d -> %s",
    #                     sub_id,
    #                     json.dumps(diffs, ensure_ascii=True),
    #                 )
    #         except JSONDecodeError as e:
    #             logger.error("Couldn't decode JSON from DB for Sub %d: %s", sub_id, e)
    #             continue
    #     if DEBUG:
    #         log4grades(sub_id, subs_grades_old, sub_grades)
    #     cur = conn.execute(
    #         """
    #         REPLACE INTO Student_Grades (
    #             owner_id, grades, updated
    #         )
    #         VALUES (
    #             ?, ?, ?
    #         );
    #     """,
    #         (sub_id, json.dumps(sub_grades), datetime.now().isoformat()),
    #     )
    #     if cur.rowcount > 0:
    #         conn.commit()
    #     else:
    #         conn.rollback()

    # emailc.quit()
