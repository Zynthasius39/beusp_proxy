import asyncio

from aiohttp import ClientError

from beusproxy.common.utils import get_logger
from beusproxy.config import API_INTERNAL_HOSTNAME


def authorize_subs(conn, httpc):
    """Authorize Student Subscribers

    Args:
        conn (sqlite3.Connection): MainDB Connection
        httpc (HTTPClient): HTTP Client
    """
    logger = get_logger(__package__)

    # Fetch students to be authorized.
    stud_credentials = conn.execute(
        """
        SELECT
            s.id,
            s.student_id,
            s.password
        FROM
            Students s
        LEFT JOIN
            Student_Sessions ses
        ON
            s.id == ses.owner_id AND
            ses.logged_out == 0
        WHERE
            ses.session_id IS NULL AND
            NOT (
                s.active_telegram_id IS NULL AND
                s.active_discord_id IS NULL AND
                s.active_email_id IS NULL
            );
    """
    ).fetchall()

    # Mapping sqlite3.Row's.
    id_table = {}
    for stud in stud_credentials:
        id_table[stud["student_id"]] = stud["id"]
    logger.debug("Authenticating -> %s", str(id_table))

    # Authorization Coroutine
    async def auth_stud_coro(student_id, password):
        """Authorize Student"""
        return (
            student_id,
            await httpc.request_coro(
                "GET",
                f"{API_INTERNAL_HOSTNAME}auth",
                params={"studentId": student_id, "password": password},
            ),
        )

    # Grab hot cookies for every student.
    try:
        ress = httpc.gather(
            *[
                auth_stud_coro(stud["student_id"], stud["password"])
                for stud in stud_credentials
            ]
        )
    except (ClientError, asyncio.TimeoutError) as e:
        logger.error(e)
        return

    for student_id, res in ress:
        if res.status != 200:
            logger.warning("Auth failed for %d: %d", student_id, res.status)
            continue
