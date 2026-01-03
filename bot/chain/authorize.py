import asyncio

from aiohttp import ClientSession, ClientTimeout, ClientResponseError, ClientConnectorError

from beusproxy.common.utils import get_logger
from beusproxy.config import API_INTERNAL_HOSTNAME, REQUEST_TIMEOUT


def authorize_subs(conn):
    """Authorize Student Subscribers

    Args:
        conn (sqlite3.Connection): MainDB Connection
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
            ) AND
            s.student_id != 99;
    """
    ).fetchall()

    logger.debug("Authenticating -> %s", str([stud["student_id"] for stud in stud_credentials]))

    # Authorization Coroutine
    async def auth_stud_coro(student_id, password):
        """Authorize Student"""
        async with ClientSession(timeout=ClientTimeout(REQUEST_TIMEOUT)) as httpc:
            return (
                student_id,
                await httpc.request(
                    "POST",
                    f"{API_INTERNAL_HOSTNAME}auth",
                    json={"studentId": student_id, "password": password},
                ),
            )

    # Grab hot cookies for every student.
    async def auth_stud_gather_coro():
        try:
            return await asyncio.gather(
                *[
                    auth_stud_coro(stud["student_id"], stud["password"])
                    for stud in stud_credentials
                ]
            )
        except (ClientConnectorError, ClientResponseError, asyncio.TimeoutError) as e:
            logger.error(e)

    ress = asyncio.run(auth_stud_gather_coro())

    for student_id, res in ress:
        if res.status != 200:
            logger.warning("Auth failed for %d: %d", student_id, res.status)
            continue
