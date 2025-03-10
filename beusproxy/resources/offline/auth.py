from datetime import datetime

from flask import make_response
from flask_restful import Resource, reqparse, abort

from beusproxy.common.utils import get_db


class Auth(Resource):
    """Authenticate

    Flask-RESTFUL resource
    """

    def get(self):
        """Bakes cookies for students
        Authenticates and returns a SessionID to be used in API. \
        If there is no record of the student/educator in the database, \
        StudentID gets registered, assuming user has agreed the ToS \
        which is usually shown in the login page.
        ---
        tags:
          - Authorization
        parameters:
        - name: studentId
          in: query
          description: Student ID to login as
          required: true
          schema:
            type: integer
          example: 220106000
        - name: password
          in: query
          description: Password of the Student
          required: true
          schema:
            type: string
            format: password
          example: demostudent
        responses:
            200:
                description: Authenticated
                headers:
                    Set-Cookie:
                        schema:
                            type: string
                            example: SessionID=8c3589030a3854d8c3589030a38548c3;
            400:
                description: Invalid credentials
            401:
                description: Bad credentials
            502:
                description: Bad response from root server
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "studentId",
            required=True,
            help="Missing the credential parameter in the JSON body",
            location="args",
        )
        rp.add_argument(
            "password",
            required=True,
            help="Missing the credential parameter in the JSON body",
            location="args",
        )
        args = rp.parse_args()
        student_id = args.get("studentId")
        password = args.get("password")

        with get_db() as db_con:
            db_res = db_con.execute(
                """
                INSERT INTO Students (student_id, password)
                VALUES (?, ?)
                ON CONFLICT (student_id) DO UPDATE
                SET password = ?
                RETURNING id;
            """,
                (student_id, password, password),
            ).fetchone()

            if db_res is None:
                db_con.rollback()
                abort(400, help="Unknown error")
            db_con.commit()

            db_con.execute(
                """
                INSERT INTO Student_Sessions(owner_id, session_id, login_date)
                VALUES (?, ?, ?);
            """,
                (db_res["id"], "offline_mode", datetime.now().isoformat()),
            )
            db_con.commit()

        res = make_response("You entered a blackhole", 200)
        res.set_cookie("SessionID", "offline_mode")
        res.set_cookie("StudentID", student_id)

        return res
