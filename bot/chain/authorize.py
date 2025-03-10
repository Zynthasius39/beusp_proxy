import logging

from aiohttp import ClientError

from beusproxy.config import API_HOSTNAME


def authorize_subs(cconn, httpc):
    """Authorize Student Subscribers

    Args:
        cconn (sqlite3.Connection): CacheDB Connection
        httpc (HTTPClient): HTTP Client
    """
    logger = logging.getLogger("beuspbot")

    # Fetch students to be authorized.
    stud_credentials = cconn.execute(
        """
        SELECT
            ss.sub_id,
            ss.student_id,
            ss.password
        FROM
            Student_Subscribers ss
        LEFT JOIN
            Student_Sessions ses
        ON
            ss.sub_id == ses.owner_id AND
            ses.expired == 0
        WHERE
            ses.session_id IS NULL;
    """
    ).fetchall()

    # Mapping sqlite3.Row's.
    id_table = {}
    for stud in stud_credentials:
        id_table[stud["student_id"]] = stud["sub_id"]
    logger.debug("Authenticating: %s", str(id_table))

    # Authorization Coroutine
    async def auth_stud_coro(student_id, password):
        """Authorize Student"""
        return (
            student_id,
            await httpc.request_coro(
                "GET",
                f"{API_HOSTNAME}auth",
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
    except ClientError as e:
        logger.error(e)
        return

    for student_id, res in ress:
        if res.status != 200:
            logger.warning("Auth failed for %d: %d", student_id, res.status)
            continue
        if (sess_id := res.cookies.get("SessionID")) is None:
            logger.error("No cookie for %d: %d", student_id, res.status)
            continue

        # Put cookies into jar.
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
            (id_table.get(student_id), sess_id.value),
        )
        cconn.commit()
