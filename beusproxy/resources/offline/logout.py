from flask import make_response
from flask_restful import Resource, reqparse, abort

from beusproxy.common.utils import get_db


class LogOut(Resource):
    """Logout

    Flask-RESTFUL resource
    """

    def get(self):
        """
        LogOut Endpoint
        Logs out given SessionID.
        ---
        tags:
          - Authorization
        description: Logs out the SessionID used in API.
        responses:
            200:
                description: Logged out
            400:
                description: Couldn't log out
        """
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
        return make_response("Spaghettified", 200)
