import json
import random
import secrets
import sqlite3
import time
from datetime import datetime
from smtplib import SMTPException

from aiohttp import ClientError, ClientResponseError
from flask import current_app as app, jsonify, make_response, request, g
from flask_restful import reqparse, abort, Resource

from beusproxy.config import (
    BOT_EMAIL,
    DATABASE,
    HOST,
    ROOT,
    USER_AGENT,
)
from beusproxy.middleman import parser
from beusproxy.context import httpc, emailc, tgc
from beusproxy.services.httpclient import HTTPClient
from beusproxy.services.discord import is_webhook
from beusproxy.services.email import is_email, verify_email


tms_pages = {
    "home": "home",
    "grades": "grades",
    "faq": "faq",
    "announces": "elan",
    "deps": "viewdeps",
    "transcript": "transkript",
}


def get_db():
    """Get a database connection.
    Create one if doesn't exist in appcontext.
    """
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


class Res(Resource):
    """Resource

    Flask-RESTFUL resource
    """

    def get(self, resource):
        """
        Resource Endpoint
        ---
        summary: Returns specified resource.
        parameters:
          - name: resource
            in: path
            required: true
            example: home
            schema:
                type: string
        responses:
            201:
                description: Success
                headers:
                    Cookie:
                        schema:
                            type: string
                            example: SessionID=8c3589030a3854d... (32 char);
            400:
                description: Invalid Page
            401:
                description: Unauthorized
            412:
                description: Bad response from root server
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        res_parser = None
        try:
            res_parser = getattr(parser, f"{resource}_parser")
        except AttributeError:
            abort(404)

        try:
            mid_res = httpc.request(
                "POST",
                f"{ROOT}?mod={tms_pages[resource]}",
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)
        except (ClientError, ClientResponseError) as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        if parser.is_expired(mid_res):
            abort(401, help="Session invalid or has expired")

        page = res_parser(mid_res)
        res = make_response(jsonify(page), 200)

        if resource == "home":
            res.set_cookie(
                "ImgID",
                page.get("home").get("image"),
                httponly=False,
                secure=False,
                samesite="Lax",
            )

        return res


class GradesAll(Resource):
    """All Grades

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Grades Endpoint
        ---
        summary: Returns all grades.
        responses:
            200:
                description: Success
            400:
                description: Bad response
            401:
                description: Unauthorized
            412:
                description: Bad response from root server
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "POST",
                ROOT,
                data=f"ajx=1&mod=grades&action=GetGrades&yt=1#1&{round(time.time())}",
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)
        except (ClientError, ClientResponseError) as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        if parser.is_expired(mid_res):
            abort(401, help="Session invalid or has expired")

        ajax = json.loads(mid_res)
        if int(ajax["CODE"]) < 1:
            abort(400, help=f"Proxy server returned CODE {ajax["CODE"]}")

        text = ajax["DATA"]
        if (
            not text.find(
                "There aren't any registered section for the selected year-term."
            )
            == -1
        ):
            abort(
                400,
                help="There aren't any registered section for the selected year-term",
            )

        page = jsonify(parser.grades2_parser(text))
        res = make_response(page, 200)
        return res


class Grades(Resource):
    """Grades

    Flask-RESTFUL resource
    """

    def get(self, year, semester):
        """
        Grades Endpoint
        ---
        summary: Returns grades in given semester.
        parameters:
          - name: year
            in: path
            required: true
            example: 2022
            type: number
          - name: semester
            in: path
            required: true
            example: 1 / 2
            type: number
        responses:
            200:
                description: Success
            400:
                description: Bad response
            401:
                description: Unauthorized
            412:
                description: Bad response from root server
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "POST",
                ROOT,
                data="ajx=1&mod=grades&action=GetGrades"
                f"&yt={year}#{semester}&{round(time.time())}",
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)
        except (ClientError, ClientResponseError) as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")
        if parser.is_expired(mid_res):
            abort(401, help="Session invalid or has expired")

        ajax = json.loads(mid_res)
        if int(ajax["CODE"]) < 1:
            abort(400, help=f"Proxy server returned CODE {ajax["CODE"]}")

        text = ajax["DATA"]
        if (
            not text.find(
                "There aren't any registered section for the selected year-term."
            )
            == -1
        ):
            abort(
                400,
                help="There aren't any registered section for the selected year-term",
            )

        page = jsonify(parser.grades2_parser(text))
        res = make_response(page, 200)
        return res


class AttendanceBySemester(Resource):
    """Attendance by year and semester

    Flask-RESTFUL resource
    """

    def get(self, year, semester):
        """
        Attendance Endpoint
        ---
        summary: Returns attendance in given semester.
        parameters:
          - name: year
            in: path
            required: true
            example: 2022
            type: number
          - name: semester
            in: path
            required: true
            example: 2
            type: number
        responses:
            200:
                description: Success
            400:
                description: Bad response
            401:
                description: Unauthorized
            412:
                description: Bad response from root server
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "POST",
                ROOT,
                data=f"ajx=1&mod=ejurnal&action=getCourses&ysem={year}#{semester}",
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)
        except (ClientError, ClientResponseError) as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        if parser.is_expired(mid_res):
            abort(401, help="Session invalid or has expired")

        if not mid_res.find("No section found.") == -1:
            abort(400, help="No section found")

        page = jsonify(parser.attendance2_parser(mid_res))
        res = make_response(page, 200)
        return res


class AttendanceByCourse(Resource):
    """Attendance by course

    Flask-RESTFUL resource
    """

    def get(self, course):
        """
        Attendance Endpoint
        ---
        summary: Returns attendance in given semester.
        parameters:
          - name: course
            in: path
            required: true
            example: 58120
            type: number
        responses:
            200:
                description: Success
            400:
                description: Bad response
            401:
                description: Unauthorized
            412:
                description: Bad response from root server
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "POST",
                ROOT,
                data=f"ajx=1&mod=ejurnal&action=viewCourse&derst={course}",
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)
        except (ClientError, ClientResponseError) as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")
        if parser.is_expired(mid_res):
            abort(401, help="Session invalid or has expired")

        ajax = json.loads(mid_res)
        if int(ajax["CODE"]) < 1:
            abort(400, help=ajax["DATA"])

        page = jsonify(parser.attendance3_parser(ajax["DATA"]))
        res = make_response(page, 200)
        return res


class Deps(Resource):
    """Departments

    Flask-RESTFUL resource
    """

    def get(self, code):
        """
        Departments Endpoint
        ---
        summary: Returns the given department.
        parameters:
          - name: code
            in: path
            required: true
            example: DEP_IT_PROG
            type: string
        responses:
            200:
                description: Success
            401:
                description: Unauthorized
            412:
                description: Bad response from root server
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "GET",
                f"{ROOT}?mod=viewdeps&d={code}",
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)
        except (ClientError, ClientResponseError) as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")
        if parser.is_expired(mid_res):
            abort(401, help="Session invalid or has expired")

        page = jsonify(parser.deps2_parser(mid_res))
        res = make_response(page, 200)
        return res


class Program(Resource):
    """Programs

    Flask-RESTFUL resource
    """

    def get(self, code, year):
        """
        Programs Endpoint
        ---
        summary: Returns the given program.
        parameters:
          - name: code
            in: path
            required: true
            example: 10106
            type: integer
          - name: year
            in: path
            required: true
            example: 2022
            type: integer
        responses:
            200:
                description: Success
            400:
                description: Bad response
            401:
                description: Unauthorized
            404:
                description: Not Found
            412:
                description: Bad response from root server
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "GET",
                f"{ROOT}?mod=progman&pc={code}&py={year}",
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)
        except (ClientError, ClientResponseError) as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")
        if parser.is_expired(mid_res):
            abort(401, help="Session invalid or has expired")

        page = parser.program2_parser(mid_res)

        if not page:
            abort(404, help="Not Found")
        res = make_response(jsonify(page), 200)
        return res


class Msg(Resource):
    """Messages

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Messages Endpoint
        ---
        summary: Returns all messages.
        responses:
            200:
                description: Success
            401:
                description: Unauthorized
            404:
                description: Not Found
            412:
                description: Bad response from root server
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "GET",
                f"{ROOT}?mod=msg",
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)

            if parser.is_expired(mid_res):
                abort(401, help="Session invalid or has expired")

            results = read_msgs(
                httpc, args.get("SessionID"), parser.msg_parser(mid_res)
            )

            msgs = []
            for res in results:
                if res.status == 200:
                    msgs.append(parser.msg2_parser(httpc.cr_text(res)))
        except (ClientError, ClientResponseError) as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        res = make_response(jsonify(msgs), 200)
        return res


class StudPhoto(Resource):
    """Student Photo

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Student Photo Endpoint
        ---
        summary: Returns student photo.
        description: Returns student photo.
        responses:
            200:
                description: Retrieved
            401:
                description: Unauthorized
            412:
                description: Bad response from root server
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
            "ImgID",
            type=str,
            help="Invalid imgid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "GET",
                f"{ROOT}stud_photo.php?ses={args.get("ImgID")}",
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_read(mid_res)
        except (ClientError, ClientResponseError) as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        res = make_response(mid_res)
        res.headers.set("Content-Type", "image/png")
        res.headers.set("Content-Length", len(mid_res))
        return res


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
            412:
                description: Bad response from root server
        """
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

        except ClientError as ce:
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
            abort(412, help="Couldn't get the cookies")

        # Eating cookies...
        for header in cookies.replace(" ", "").split(";"):
            if not header.find("PHPSESSID") == -1:
                sessid = header.split("=")[1]

        db_con = get_db()
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
            db_con.close()
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
        db_con.close()

        # Sending out freshly baked cookies
        mid_res = make_response("", 200)
        mid_res.set_cookie(
            "SessionID",
            sessid,
            httponly=False,
            secure=False,
            samesite="Lax",
            max_age=3600,
        )
        mid_res.set_cookie(
            "StudentID",
            student_id,
            httponly=False,
            secure=False,
            samesite="Lax",
            max_age=3600,
        )

        return mid_res


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

        db_con = get_db()
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
            db_con.close()
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
            db_con.close()
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
        db_con.close()

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
        except ClientError as ce:
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


class Verify(Resource):
    """Session Verification

    Flask-RESTFUL resource
    """

    def post(self):
        """
        Session Verify Endpoint
        ---
        summary: Logs out given SessionID.
        description: Logs out the SessionID used in API.
        responses:
            200:
                description: Verify successful
            401:
                description: Couldn't verify
            412:
                description: Bad response from root server
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "POST",
                ROOT,
                data="ajx=1",
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)
        except (ClientError, ClientResponseError) as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        if parser.is_expired(mid_res):
            abort(401, help="Session invalid or has expired")

        return make_response("", 200)


class Bot(Resource):
    """BeuTMSBot

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Bot Endpoint
        ---
        summary: Bot status
        description: Gets telegram bot and the email used by bot
        responses:
            200:
                description: Bot status
            404:
                description: Bot is not active
        """
        bot = {}

        if BOT_EMAIL:
            bot["bot_email"] = BOT_EMAIL

        try:
            telegram_bot = tgc.get_me()
        except (AssertionError, ClientError, ClientResponseError) as e:
            app.logger.error(e)
            abort(502, help="Bad response from root server")

        if telegram_bot:
            if telegram_bot["result"].get("username"):
                bot["bot_telegram"] = telegram_bot["result"]["username"]

        return bot


class BotSubscribe(Resource):
    """BeuTMSBot Subscribe

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Bot Subscribe Endpoint
        ---
        summary: Bot subcriptions status
        description: Gets a list of subscriptions for current user.
        responses:
            200:
                description: Success
            401:
                description: Session invalid or has expired
            404:
                description: Bot is not active
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

        db_con = get_db()
        db_cur = db_con.cursor()
        db_res = db_cur.execute(
            """
            SELECT ss.owner_id, s.active_telegram_id, s.active_discord_id, s.active_email_id
            FROM Student_Sessions ss
            INNER JOIN Students s
            ON ss.owner_id = s.id
            WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
            LIMIT 1;
        """,
            (args.get("StudentID"), args.get("SessionID")),
        ).fetchone()
        if db_res is None:
            db_con.close()
            abort(401, help="Session invalid or has expired")

        subscriptions = {}
        owner_id = db_res["owner_id"]

        if db_res is not None:
            if db_res["active_telegram_id"] is not None:
                db_sub_res = db_cur.execute(
                    """
                    SELECT ts.telegram_user_id FROM Telegram_Subscribers ts
                    INNER JOIN Students s
                    ON ts.telegram_id = s.active_telegram_id
                    WHERE s.id = ?;
                """,
                    (owner_id,),
                ).fetchone()
                if db_sub_res is not None:
                    subscriptions["telegram_user_id"] = db_sub_res["telegram_user_id"]
            if db_res["active_discord_id"] is not None:
                db_sub_res = (
                    db_con.cursor()
                    .execute(
                        """
                    SELECT ds.discord_webhook_url FROM Discord_Subscribers ds
                    INNER JOIN Students s ON ds.discord_id = s.active_discord_id 
                    WHERE s.id = ?;  
                """,
                        (owner_id,),
                    )
                    .fetchone()
                )
                if db_sub_res is not None:
                    subscriptions["discord_webhook_url"] = db_sub_res[
                        "discord_webhook_url"
                    ]
            if db_res["active_email_id"] is not None:
                db_sub_res = (
                    db_con.cursor()
                    .execute(
                        """
                    SELECT es.email FROM Email_Subscribers es
                    INNER JOIN Students s ON es.email_id = s.active_email_id
                    WHERE s.id = ?;
                """,
                        (owner_id,),
                    )
                    .fetchone()
                )
                if db_sub_res is not None:
                    subscriptions["email"] = db_sub_res["email"]

        db_con.close()
        return {"subscriptions": subscriptions}

    def put(self):
        """
        Bot Subscribe Endpoint
        ---
        summary: Subscribe to Bot
        description: Subscribes the current user.
        parameters:
          - name: subscribe
            in: body
            required: yes
            description: Subscriptions to add.
            schema:
                properties:
                    telegram_user_id:
                        type: string
                        description: Telegram Username
                        example: slaffoe
                    discord_webhook_url:
                        type: string
                        description: Discord Webhook
                        example: https://discord.com/api/webhooks/{token}
                    email:
                        type: string
                        description: E-Mail
                        example: admin@alakx.com
        responses:
            200:
                description: Nothing to do
            201:
                description: Subscribed
            204:
                description: Waiting for verification
            401:
                description: Session invalid or has expired
            404:
                description: Bot is not active
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
        rp.add_argument(
            "telegram",
            type=str,
        )
        rp.add_argument(
            "discord_webhook_url",
            type=str,
        )
        rp.add_argument(
            "email",
            type=str,
        )
        args = rp.parse_args()

        db_con = get_db()
        db_cur = db_con.cursor()
        db_res = db_cur.execute(
            """
            SELECT ss.owner_id
            FROM Student_Sessions ss
            INNER JOIN Students s
            ON ss.owner_id = s.id
            WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
            LIMIT 1;
            """,
            (args.get("StudentID"), args.get("SessionID")),
        ).fetchone()

        if db_res is None:
            db_con.close()
            abort(401, help="Session invalid or has expired")

        owner_id = db_res["owner_id"]
        if args.get("telegram") is not None:
            db_cur.execute(
                """
                UPDATE Verifications
                SET verified = TRUE
                WHERE owner_id = ? AND verified = FALSE AND verify_service = 0;
            """,
                (owner_id,),
            )
            db_con.commit()
            code = verify_code_gen(6)
            db_cur.execute(
                """
                INSERT INTO Verifications
                (owner_id, verify_code, verify_date, verify_service)
                VALUES(?, ?, ?, 0);
            """,
                (
                    owner_id,
                    code,
                    datetime.now().isoformat(),
                ),
            )
            db_con.commit()
            db_con.close()
            return {"telegram_code": code}
        if args.get("discord_webhook_url") is not None:
            if not is_webhook(args.get("discord_webhook_url")):
                abort(400, help="Invalid Discord Webhook URL")
            db_sub_res = db_cur.execute(
                """
                INSERT INTO Discord_Subscribers(owner_id, discord_webhook_url)
                VALUES(?, ?)
                RETURNING discord_id;
            """,
                (owner_id, args.get("discord_webhook_url")),
            ).fetchone()
            if db_sub_res is None:
                db_con.rollback()
                db_con.close()
                abort(400, help="Unknown error")
            db_con.commit()
            db_cur.execute(
                """
                UPDATE Students
                SET active_discord_id = ?
                WHERE id = ?;
            """,
                (db_sub_res["discord_id"], owner_id),
            )
            db_con.commit()
            db_con.close()
            return make_response("", 201)
        if args.get("email") is not None:
            if not is_email(args.get("email")):
                db_con.close()
                abort(400, help="Invalid E-Mail address")
            db_cur.execute(
                """
                UPDATE Verifications
                SET verified = TRUE
                WHERE owner_id = ? AND verified = FALSE AND verify_service = 1;
            """,
                (owner_id,),
            )
            db_con.commit()
            code = verify_code_gen(9)
            db_cur.execute(
                """
                INSERT INTO Verifications
                (owner_id, verify_code, verify_item, verify_date, verify_service)
                VALUES(?, ?, ?, ?, 1);
            """,
                (owner_id, code, args.get("email"), datetime.now().isoformat()),
            )
            db_con.commit()
            db_con.close()
            try:
                emailc.send_verification(args.get("email"), code)
            except SMTPException:
                abort(500)
            return "", 204

        db_con.close()
        return make_response("", 200)

    def delete(self):
        """
        Bot Subscribe Endpoint
        ---
        summary: Unsubscribe to Bot
        description: Unsubscribes the current user.
        parameters:
          - name: unsubscribe
            in: body
            required: yes
            description: Subscriptions to cancel.
            schema:
                properties:
                    telegram_user_id:
                        type: string
                        description: Telegram Username
                        example: slaffoe
                    discord_webhook_url:
                        type: string
                        description: Discord Webhook
                        example: https://discord.com/webhook/{token}
                    email:
                        type: string
                        description: E-Mail
                        example: admin@alakx.com
        responses:
            202:
                description: Nothing to do
            204:
                description: Unsubscribed
            400:
                description: Cannot find the subscription
            401:
                description: Session invalid or has expired
            404:
                description: Bot is not active
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

        db_con = get_db()
        db_cur = db_con.cursor()
        db_res = db_cur.execute(
            """
            SELECT ss.owner_id, s.active_telegram_id, s.active_discord_id, s.active_email_id
            FROM Student_Sessions ss
            INNER JOIN Students s
            ON ss.owner_id = s.id
            WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
            LIMIT 1;
            """,
            (args.get("StudentID"), args.get("SessionID")),
        ).fetchone()

        res = make_response("", 202)

        if db_res is None:
            db_con.close()
            abort(401, help="Session invalid or has expired")

        owner_id = db_res["owner_id"]
        unsub_list = (
            request.get_json().get("unsubscribe")
            if isinstance(request.get_json(), dict)
            else None
        )
        if unsub_list is None:
            db_con.close()
            abort(400, help="Missing unsubscribe array")

        if "telegram" in unsub_list and db_res["active_telegram_id"]:
            db_sub_res = db_cur.execute(
                """
                UPDATE Students
                SET active_telegram_id = NULL
                WHERE id = ?;
            """,
                (owner_id,),
            )
            if not db_sub_res.rowcount > 0:
                db_con.rollback()
                db_con.close()
                abort(400, help="Couldn't find the subscription")
            db_con.commit()
            res = make_response("", 204)
        if "discord" in unsub_list and db_res["active_discord_id"]:
            db_sub_res = db_cur.execute(
                """
                UPDATE Students
                SET active_discord_id = NULL
                WHERE id = ?;
            """,
                (owner_id,),
            )
            if not db_sub_res.rowcount > 0:
                db_con.rollback()
                db_con.close()
                abort(400, help="Couldn't find the subscription")
            db_con.commit()
            res = make_response("", 204)
        if "email" in unsub_list and db_res["active_email_id"]:
            db_sub_res = db_cur.execute(
                """
                UPDATE Students
                SET active_email_id = NULL
                WHERE id = ?;
            """,
                (owner_id,),
            )
            if not db_sub_res.rowcount > 0:
                db_con.rollback()
                db_con.close()
                abort(400, help="Couldn't find the subscription")
            db_con.commit()
            res = make_response("", 204)
        db_con.close()

        if (
            args.get("telegram_user_id") is not None
            or args.get("discord_webhook_url") is not None
            or args.get("email") is not None
        ):
            abort(400, help="Couldn't find the subscription")

        return res


class BotVerify(Resource):
    """BeuTMSBot Verification

    Flask-RESTFUL resource
    """

    # @api.representation("text/html")
    def get(self, code):
        # pylint: disable=R0915
        """
        Bot Verify Endpoint
        ---
        summary: Verification step
        description: Validate code and complete subscription step.
        produces:
          - text/html
        parameters:
          - name: code
            in: path
            required: true
            example: home
            schema:
                type: string
        responses:
            200:
                description: Return response in HTML
                content:
                    text/html:
                        schema:
                            type: string
            404:
                description: Bot is not active
            500:
                description: Problem with database
        """
        res = make_response(verify_email(code))
        return res


def read_announce(http_client: HTTPClient, sessid):
    """Read announces of student

    Args:
        sessid (str): Student session_id
    """
    http_client.request(
        "POST",
        f"{ROOT}stud_announce.php",
        data="btnRead=Oxudum",
        headers={
            "Host": HOST,
            "Cookie": f"PHPSESSID={sessid}; ",
            "User-Agent": USER_AGENT,
        },
    )


def read_msgs(http_client: HTTPClient, sessid, msg_ids):
    """Read messages of student

    Args:
        sessid (str): Student session_id
        msg_ids (list): List of message ids to be read

    Returns:
        list: List of responses
    """

    return http_client.gather(
        *[
            http_client.request_coro(
                "POST",
                ROOT,
                data=f"ajx=1&mod=msg&action=ShowReceivedMessage&sm_id={id}",
                headers={
                    "Host": HOST,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cookie": f"PHPSESSID={sessid}; ",
                    "User-Agent": USER_AGENT,
                },
            )
            for id in msg_ids
        ]
    )


def verify_code_gen(length):
    """Generate verification code of given length

    Args:
        length (int): Length of desired code

    Returns:
        str: Randomly generated code in given length
    """
    return "".join(str(random.randint(0, 9)) for _ in range(length))
