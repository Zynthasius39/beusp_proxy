from flask import current_app as app, make_response
from flask_restful import Resource, abort, reqparse

from ..config import HOST, ROOT, USER_AGENT
from ..common.utils import get_db
from ..context import c
from ..services.httpclient import HTTPClientError


class LogOut(Resource):
    """Logout

    Flask-RESTFUL resource
    """

    def post(self):
        """
        LogOut Endpoint
        ---
        summary: Logs out given SessionID.
        description: Logs out the SessionID used in API.
        responses:
            200:
                description: Logged out
            400:
                description: Couldn't log out
        """
        httpc = c.get("httpc")
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        rp.add_argument(
            "StudentID",
            type=str,
            help="Invalid studentid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        with get_db() as db_con:
            db_cur = db_con.cursor()

            # Querying current session to see if it exists
            db_res = db_cur.execute(
                """
                SELECT ss.owner_id FROM Student_Sessions ss
                INNER JOIN Students s
                ON ss.owner_id = s.id
                WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
                LIMIT 1;
            """,
                (args.get("StudentID"), args.get("SessionID")),
            ).fetchone()
            if db_res is None:
                abort(400, help="Couldn't logout")

            # Querying all sessions with ids which are not logged out yet
            owner_id = db_res["owner_id"]
            db_res = db_cur.execute(
                """
                SELECT ss.session_id FROM Student_Sessions ss
                WHERE ss.owner_id = ? AND ss.logged_out = 0
                ORDER BY ss.login_date DESC;
            """,
                (owner_id,),
            ).fetchall()
            if len(db_res) == 0:
                abort(400, help="Couldn't logout")

            # Updating database all sessions with fetched ids
            db_cur.execute(
                """
                UPDATE Student_Sessions
                SET logged_out = 1
                WHERE owner_id = ?
            """,
                (owner_id,),
            )
            db_con.commit()

        try:
            ress = httpc.gather(
                *[
                    httpc.request_coro(
                        "GET",
                        f"{ROOT}logout.php",
                        headers={
                            "Host": HOST,
                            "Cookie": f"PHPSESSID={session_id}; BEU_STUD_AR=1; ",
                            "User-Agent": USER_AGENT,
                        },
                        allow_redirects=False,
                    )
                    for session_id in list(map(lambda row: row["session_id"], db_res))
                ]
            )
        except HTTPClientError as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        # Logging out of all sessions with fetched session_ids

        try:
            if ress[0].status != 302:
                abort(400, help="Couldn't logout")
        except IndexError:
            abort(400, help="Couldn't logout")

        app.logger.info("Student %s has logged out", args.get("StudentID"))

        # Getting rid of spoiled cookies.
        mid_res = make_response("", 200)
        mid_res.set_cookie(
            "SessionID", "", httponly=False, secure=False, samesite="Lax"
        )
        mid_res.set_cookie(
            "StudentID", "", httponly=False, secure=False, samesite="Lax"
        )

        return mid_res
