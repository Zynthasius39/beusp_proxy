import secrets
from datetime import datetime

from flask import current_app as app, make_response
from flask_restful import Resource, abort, reqparse

from ..config import HOST, ROOT, USER_AGENT
from ..common.utils import get_db
from ..context import c
from ..services.httpclient import HTTPClientError


class Auth(Resource):
    """Authenticate

    Flask-RESTFUL resource
    """

    def post(self):
        """
        Auth Endpoint
        ---
        summary: Returns Set-Cookie header.
        description: Authenticates and returns a SessionID to be used in API. \
            If there is no record of the student/educator in the database, \
            StudentID gets registered, assuming user has agreed the ToS \
            which is usually shown in the login page.
        parameters:
          - name: body
            in: body
            required: yes
            description: JSON parameters.
            schema:
                properties:
                    student_id:
                        type: string
                        description: Student ID to login as
                        example: 220987654
                    password:
                        type: string
                        description: Password of the Student
                        example: S3CR3T_P4SSW0RD
        responses:
            200:
                description: Authenticated
                headers:
                    Set-Cookie:
                        schema:
                            type: string
                            example: SessionID=8c3589030a3854d... (32 char);
            400:
                description: Invalid credentials
            401:
                description: Bad credentials
            403:
                description: Not implemented
            502:
                description: Bad response from root server
        """
        httpc = c.get("httpc")
        rp = reqparse.RequestParser()
        rp.add_argument(
            "student_id",
            required=True,
            help="Missing the credential parameter in the JSON body",
        )
        rp.add_argument(
            "password",
            required=True,
            help="Missing the credential parameter in the JSON body",
        )
        args = rp.parse_args()

        student_id = args.get("student_id")
        password = args.get("password")

        if not student_id or not password:
            abort(400, help="Invalid credentials")

        # Generate secure session_id
        sessid = secrets.token_hex(32)

        try:
            # Authenticate the student_id with session_id
            mid_res = httpc.request(
                "POST",
                f"{ROOT}auth.php",
                data=f"username={student_id}&password={password}&LogIn=",
                headers={
                    "Host": HOST,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cookie": f"PHPSESSID={sessid}; ",
                    "User-Agent": USER_AGENT,
                },
                allow_redirects=False,
            )

        except HTTPClientError as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        # Respond with 400 if it was not redirected.
        if mid_res.status == 200:
            abort(400, help="Bad credentials")

        if not mid_res.status == 302:
            abort(502, help="Bad response from root server")

        app.logger.info("Student %s has logged in", student_id)
        cookies = mid_res.headers.get("Set-Cookie")

        # Preventing unusual behaviour of the root server.
        if not cookies:
            app.logger.error("Couldn't get the cookies")
            abort(502, help="Bad response from root server")

        # Eating cookies...
        for header in cookies.replace(" ", "").split(";"):
            if not header.find("PHPSESSID") == -1:
                sessid = header.split("=")[1]

        with get_db() as db_con:
            db_cur = db_con.cursor()

            # Update student information, adding new student
            # if it's not present who hopefully read the ToS.
            db_res = db_cur.execute(
                """
                REPLACE INTO Students(id, student_id, password)
                VALUES ((
                    SELECT id FROM Students
                    WHERE student_id = ?
                ), ?, ?)
                RETURNING id;
            """,
                (student_id, student_id, password),
            ).fetchone()

            if db_res is None:
                db_con.rollback()
                abort(400, help="Unknown error")
            db_con.commit()

            # Pushing new session_id
            db_cur.execute(
                """
                INSERT INTO Student_Sessions(owner_id, session_id, login_date)
                VALUES (?, ?, ?);
            """,
                (db_res["id"], sessid, datetime.now().isoformat()),
            )
            db_con.commit()

        # Sending out freshly baked cookies
        mid_res = make_response("", 200)
        mid_res.set_cookie(
            "SessionID",
            sessid,
            httponly=False,
            secure=False,
            samesite="Lax",
        )
        mid_res.set_cookie(
            "StudentID",
            student_id,
            httponly=False,
            secure=False,
            samesite="Lax",
        )

        return mid_res
