import logging

from aiohttp import ClientError

from beusproxy.config import API_HOSTNAME
from beusproxy.services.httpclient import HTTPClientError


def authorize_subs(cconn, httpc):
    """Authorize Student Subscribers"""
    logger = logging.getLogger("beuspbot")

    stud_credentials = cconn.execute(
        """
        SELECT
            ss.id,
            ss.student_id,
            ss.password,
            ses.session_id
        FROM
            Student_Subscribers ss
        LEFT JOIN
            Student_Sessions ses
        ON
            ss.id == ses.owner_id AND
            ses.logged_out == 0
    """
    ).fetchall()

    id_table = {}
    for stud in stud_credentials:
        id_table[stud["student_id"]] = stud["id"]
    print(id_table)

    async def auth_stud_coro(student_id, password):
        """Authorize Student"""
        try:
            return (
                student_id,
                await httpc.request_coro(
                    "GET",
                    f"{API_HOSTNAME}auth",
                    params={"studentId": student_id, "password": password},
                ),
            )
        except ClientError as e:
            logger.error(e)
            return

    try:
        ress = httpc.gather(
            *[
                auth_stud_coro(stud["student_id"], stud["password"])
                for stud in stud_credentials
            ]
        )
    except HTTPClientError as e:
        logger.error(e)

    for student_id, res in ress:
        if res.status != 200:
            logger.warning("Auth failed for %d: %d", student_id, res.status)
            continue
        if (
            sess_id := dict(
                cookie.split("=", 1)
                # TODO: Fix cookie theft
                for cookie in res.headers.get("Set-Cookie").split("; ")
            ).get("SessionID")
            is None
        ):
            logger.error("No cookie for %d: %d", student_id, res.status)
            continue
        cconn.execute(
            """
            INSERT INTO Student_Sessions (
                owner_id,
                session_id
            )
            VALUES (
                ?, ?
            )
        """,
            (id_table.get(student_id), sess_id),
        )
        cconn.commit()
