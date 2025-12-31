import asyncio
import json
import socket
from datetime import datetime
from json import JSONDecodeError
from asyncio import TimeoutError as AsyncioTimeoutError
from smtplib import SMTPException

from aiohttp import ClientSession, ClientTimeout, ClientError

from beusproxy.common.utils import get_logger
from beusproxy.config import API_INTERNAL_HOSTNAME, DEBUG, HOST, USER_AGENT, REQUEST_TIMEOUT
from beusproxy.services.email import EmailClient

from ..common.utils import grade_diff
from ..common.debug import log4grades
from ..notify_mgr import notify

logger = get_logger(__package__)


def check_grades(conn):
    """Fetch grades and compare

    Args:
        conn (sqlite3.Connection): MainDB Connection
    """
    subs = conn.execute(
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
            s.id == ses.owner_id
          WHERE
            ses.logged_out == 0 AND
            NOT (
                s.active_telegram_id IS NULL AND
                s.active_discord_id IS NULL AND
                s.active_email_id IS NULL
            )
        ) t
        WHERE rn = 1;
    """
    ).fetchall()

    cr = {}
    async def grades_coro(owner_id, session_id):
        try:
            async with ClientSession(timeout=ClientTimeout(REQUEST_TIMEOUT)) as httpc:
                cr[owner_id] = await httpc.request(
                    "GET",
                    f"{API_INTERNAL_HOSTNAME}resource/grades/latest",
                    headers={
                        "Cookie": f"SessionID={session_id};",
                        "User-Agent": USER_AGENT,
                    },
                )
        except ClientError as e:
            logger.error("Error occurred in grades_coro for owner_id %s: %s", owner_id, e)

    # Fetch grades via API
    async def grades_gather_coro():
        try:
            await asyncio.gather(
                *[grades_coro(sub["id"], sub["session_id"]) for sub in subs]
            )
        except AsyncioTimeoutError as e:
            logger.error(e)

    cr_json = {}
    async def grades_json_coro(sub_id, sub_grades_cr):
        if sub_grades_cr.status == 200:
            try:
                cr_json[sub_id] = await sub_grades_cr.json(
                    encoding="UTF-8", loads=json.loads, content_type="application/json"
                )
            except RuntimeError as e:
                logger.error("Error occurred in grades_json_coro for sub_id %s: %s", sub_id, e)
        else:
            cr_json[sub_id] = sub_grades_cr.status

    async def grades_json_gather_coro():
        try:
            await asyncio.gather(
                *[
                    grades_json_coro(sub_id, sub_grades_cr)
                    for sub_id, sub_grades_cr in cr.items()
                ]
            )
        except ClientError as e:
            logger.error(e)

    asyncio.run(grades_gather_coro())
    asyncio.run(grades_json_gather_coro())

    subs_grades_old = conn.execute(
        """
        SELECT
            sg.owner_id,
            sg.grades
        FROM
            Student_Grades sg
        INNER JOIN
            Students s
        ON
            sg.owner_id == s.id AND
            NOT (
                s.active_telegram_id IS NULL AND
                s.active_discord_id IS NULL AND
                s.active_email_id IS NULL
            );
    """
    ).fetchall()

    # Get a EmailClient
    try:
        emailc = EmailClient()
    except (SMTPException, socket.gaierror, OSError) as e:
        logger.error("emailc: %s", e)
        return

    # Compare grades wisely
    for sub_id, sub_grades in cr_json.items():
        if isinstance(sub_grades, int):
            if sub_grades == 401:
                cur = conn.execute(
                    """
                    UPDATE
                        Student_Sessions
                    SET
                        logged_out = 1
                    WHERE
                        owner_id = ?;
                """,
                    (sub_id,),
                )
                if cur.rowcount > 0:
                    conn.commit()
                else:
                    conn.rollback()
            logger.error("Invalid response %d for %d", sub_grades, sub_id)
            continue
        if sub_grades and dict(subs_grades_old).get(sub_id):
            # Grade diff util
            try:
                diffs = grade_diff(
                    json.loads(dict(subs_grades_old)[sub_id]), sub_grades
                )
                if len(diffs) != 0:
                    # Push to notifier
                    notify(sub_id, diffs, sub_grades, emailc=emailc)
                    logger.debug(
                        "Changes found for Sub %d -> %s",
                        sub_id,
                        json.dumps(diffs, ensure_ascii=True),
                    )
            except JSONDecodeError as e:
                logger.error("Couldn't decode JSON from DB for Sub %d: %s", sub_id, e)
                continue
        if DEBUG:
            log4grades(sub_id, subs_grades_old, sub_grades)
        cur = conn.execute(
            """
            REPLACE INTO Student_Grades (
                owner_id, grades, updated
            )
            VALUES (
                ?, ?, ?
            );
        """,
            (sub_id, json.dumps(sub_grades), datetime.now().isoformat()),
        )
        if cur.rowcount > 0:
            conn.commit()
        else:
            conn.rollback()

    emailc.quit()
