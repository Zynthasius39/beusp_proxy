from concurrent.futures.thread import ThreadPoolExecutor

import asyncio
import datetime
import json
import random
import secrets
import sqlite3
import time
import aiohttp
import requests

from flask import Flask, jsonify, make_response, g
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS

from controller.aiohttp import make_request, wrapper
from config import HOST, ROOT, user_agent
from middleman import parser


app = Flask(__name__)
api = Api(app)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://10.0.10.75:5173"}})

tms_pages = {
    "home": "home",
    "grades": "grades",
    "faq": "faq",
    "announces": "elan",
    "deps": "viewdeps",
    "transcript": "transkript",
}

def get_db():
    """Get a SQLite database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect("beusp.db")
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

class Res(Resource):

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
            res_parser = getattr(parser, f"{resource}Parser")
        except AttributeError:
            abort(404)

        def request():
            return asyncio.run(wrapper(
            {
                "method": "POST",
                "url": f"{ROOT}?mod={tms_pages[resource]}",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": user_agent,
                }
            }))
        mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            read_msgs(args.get("SessionID"), parser.msgParser2(mid_res.get("text")))
            mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            abort(412, help="Bad request from root server")

        if not mid_res["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(mid_res.get("text")):
            abort(401, help="Session invalid or has expired")

        page = res_parser(mid_res.get("text"))
        res = make_response(jsonify(page), 200)

        if resource == "home":
            res.set_cookie("ImgID",
                           page.get("home").get("image"),
                           httponly=False,
                           secure=False,
                           samesite="Lax")

        return res


class GradesAll(Resource):

    def get(self):
        """
        Grades Endpoint
        ---
        summary: Returns all grades.
        responses:
            200:
                description: Success
            400:
                description: Bad request
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

        def request():
            return asyncio.run(wrapper(
            {
                "method": "POST",
                "url": ROOT,
                "data": f"ajx=1&mod=grades&action=GetGrades&yt=1#1&{round(time.time())}",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": user_agent,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            }))
        mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            read_msgs(args.get("SessionID"), parser.msgParser2(mid_res.get("text")))
            mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            abort(412, help="Bad request from root server")

        if not mid_res["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(mid_res.get("text")):
            abort(401, help="Session invalid or has expired")

        ajax = json.loads(mid_res.get("text"))
        if int(ajax["CODE"]) < 1:
            abort(400, help=f"Proxy server returned CODE {ajax["CODE"]}")

        text = ajax["DATA"]
        if not text.find("There aren't any registered section for the selected year-term.") == -1:
            abort(400, help="There aren't any registered section for the selected year-term")

        page = jsonify(parser.gradesParser2(text))
        res = make_response(page, 200)
        return res


class Grades(Resource):

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
                description: Bad request
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

        def request():
            return asyncio.run(wrapper(
            {
                "method": "POST",
                "url": ROOT,
                "data": "ajx=1&mod=grades&action=GetGrades"
                f"&yt={year}#{semester}&{round(time.time())}",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": user_agent,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            }))
        mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            read_msgs(args.get("SessionID"), parser.msgParser2(mid_res.get("text")))
            mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            abort(412, help="Bad request from root server")

        if not mid_res["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(mid_res.get("text")):
            abort(401, help="Session invalid or has expired")

        ajax = json.loads(mid_res.get("text"))
        if int(ajax["CODE"]) < 1:
            abort(400, help=f"Proxy server returned CODE {ajax["CODE"]}")

        text = ajax["DATA"]
        if not text.find("There aren't any registered section for the selected year-term.") == -1:
            abort(400, help="There aren't any registered section for the selected year-term")

        page = jsonify(parser.gradesParser2(text))
        res = make_response(page, 200)
        return res


class AttendanceBySemester(Resource):

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
                description: Bad request
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

        def request():
            return asyncio.run(wrapper(
            {
                "method": "POST",
                "url": ROOT,
                "data": f"ajx=1&mod=ejurnal&action=getCourses&ysem={year}#{semester}",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": user_agent,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            }))
        mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            read_msgs(args.get("SessionID"), parser.msgParser2(mid_res.get("text")))
            mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            abort(412, help="Bad request from root server")

        if not mid_res["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(mid_res.get("text")):
            abort(401, help="Session invalid or has expired")

        if not mid_res.get("text").find("No section found.") == -1:
            abort(400, help="No section found")

        page = jsonify(parser.attendanceParser2(mid_res.get("text")))
        res = make_response(page, 200)
        return res


class AttendanceByCourse(Resource):

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
                description: Bad request
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

        def request():
            return asyncio.run(wrapper(
            {
                "method": "POST",
                "url": ROOT,
                "data": f"ajx=1&mod=ejurnal&action=viewCourse&derst={course}",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": user_agent,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            }))
        mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            read_msgs(args.get("SessionID"), parser.msgParser2(mid_res.get("text")))
            mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            abort(412, help="Bad request from root server")

        if not mid_res["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(mid_res.get("text")):
            abort(401, help="Session invalid or has expired")

        ajax = json.loads(mid_res.get("text"))
        if int(ajax["CODE"]) < 1:
            abort(400, help=ajax["DATA"])

        page = jsonify(parser.attendanceParser3(ajax["DATA"]))
        res = make_response(page, 200)
        return res


class Deps(Resource):
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

        def request():
            return asyncio.run(wrapper(
            {
                "method": "GET",
                "url": f"{ROOT}?mod=viewdeps&d={code}",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": user_agent,
                }
            }))
        mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            read_msgs(args.get("SessionID"), parser.msgParser2(mid_res.get("text")))
            mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            abort(412, help="Bad request from root server")

        if not mid_res["status"] == 200:
            abort(412, help="Bad request from gateway")

        if parser.isExpired(mid_res.get("text")):
            abort(401, help="Session invalid or has expired")

        page = jsonify(parser.depsParser2(mid_res.get("text")))
        res = make_response(page, 200)
        return res


class Program(Resource):
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
                description: Bad request
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

        def request():
            return asyncio.run(wrapper(
            {
                "method": "GET",
                "url": f"{ROOT}?mod=progman&pc={code}&py={year}",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": user_agent,
                }
            }))
        mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            read_msgs(args.get("SessionID"), parser.msgParser2(mid_res.get("text")))
            mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            abort(412, help="Bad request from root server")

        if not mid_res["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(mid_res.get("text")):
            abort(401, help="Session invalid or has expired")

        page = parser.programParser2(mid_res.get("text"))

        if not page:
            abort(404, help="Not Found")
        res = make_response(jsonify(page), 200)
        return res


class Msg(Resource):
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

        def request():
            return asyncio.run(wrapper(
            {
                "method": "GET",
                "url": f"{ROOT}?mod=msg",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": user_agent,
                }
            }))
        mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            read_msgs(args.get("SessionID"), parser.msgParser2(mid_res.get("text")))
            mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            abort(412, help="Bad request from root server")

        if not mid_res["status"] == 200:
            abort(412, help="Bad request from gateway")

        if parser.isExpired(mid_res.get("text")):
            abort(401, help="Session invalid or has expired")

        results = read_msgs(args.get("SessionID"), parser.msgParser(mid_res.get("text")))

        msgs = []
        for res in results:
            if res["status"] == 200:
                msgs.append(parser.msgParser2(res.get("text")))

        res = make_response(jsonify(msgs), 200)
        return res


class StudPhoto(Resource):
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

        mid_res = requests.get(
            f"{ROOT}stud_photo.php?ses={args.get("ImgID")}",
            headers = {
                "Host": HOST,
                "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                "User-Agent": user_agent,
            },
            timeout = 10
        )

        if not mid_res.status_code == 200:
            abort(412, help="Bad request from gateway")

        res = make_response(mid_res.content)
        res.headers.set("Content-Type", "image/png")
        res.headers.set("Content-Length", len(mid_res.content))

        return res


class Auth(Resource):
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

        # Authenticate the student_id with session_id
        def request():
            return asyncio.run(wrapper(
            {
                "method": "POST",
                "url": f"{ROOT}auth.php",
                "data": f"username={student_id}&password={password}&LogIn=",
                "headers": {
                    "Host": HOST,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cookie": f"PHPSESSID={sessid}; ",
                    "User-Agent": user_agent,
                }
            }))
        mid_res = request()

        # Respond with 400 if it was not redirected.
        if not mid_res["status"] == 302:
            abort(400, help="Bad credentials")

        app.logger.info("Student %s has logged in", student_id)
        cookies = mid_res.get("headers").get("Set-Cookie")

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
        db_res = db_cur.execute("""
            REPLACE INTO Students(id, student_id, password)
            VALUES ((
                SELECT id FROM Students
                WHERE student_id = ?
            ), ?, ?)
            RETURNING id;
        """, (student_id, student_id, password)).fetchone()

        if db_res is None:
            db_con.rollback()
            db_con.close()
            abort(400, help="Unknown error")
        db_con.commit()

        # Pushing new session_id
        db_cur.execute("""
            INSERT INTO Student_Sessions(owner_id, session_id, last_login)
            VALUES (?, ?, ?);
        """, (db_res["id"], sessid, datetime.datetime.now().isoformat()))
        db_con.commit()
        db_con.close()

        # Sending out freshly baked cookies
        mid_res = make_response("", 200)
        mid_res.set_cookie("SessionID",
                           sessid,
                           httponly=False,
                           secure=False,
                           samesite="Lax",
                           max_age=3600)
        mid_res.set_cookie("StudentID",
                           student_id,
                           httponly=False,
                           secure=False,
                           samesite="Lax",
                           max_age=3600)

        return mid_res


class LogOut(Resource):

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
        db_res = db_cur.execute("""
            SELECT ss.owner_id FROM Student_Sessions ss
            INNER JOIN Students s
            ON ss.owner_id = s.id
            WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
            LIMIT 1;
        """, (args.get("StudentID"), args.get("SessionID"))).fetchone()
        if db_res is None:
            db_con.close()
            abort(400, help="Couldn't logout")

        # Querying all sessions with ids which are not logged out yet
        owner_id = db_res["owner_id"]
        db_res = db_cur.execute("""
            SELECT ss.session_id FROM Student_Sessions ss
            WHERE ss.owner_id = ? AND ss.logged_out = 0;
        """, (owner_id, )).fetchall()
        if len(db_res) == 0:
            db_con.close()
            abort(400, help="Couldn't logout")

        # Updating database all sessions with fetched ids
        db_cur.execute("""
            UPDATE Student_Sessions
            SET logged_out = 1
            WHERE owner_id = ?
        """, (owner_id, ))
        db_con.commit()
        db_con.close()

        # Logging out of all sessions with fetched session_ids
        session_ids = list(map(lambda row: row["session_id"], db_res))
        def thread_target():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def n_wrapper(rqsts):
                async with aiohttp.ClientSession() as session:
                    tasks = [make_request(session, req) for req in rqsts]
                    return await asyncio.gather(*tasks)

            rqsts = [
            {
                "method": "GET",
                "url": f"{ROOT}logout.php",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={session_id}; BEU_STUD_AR=1; ",
                    "User-Agent": user_agent,
                }
            } for session_id in session_ids]
            return loop.run_until_complete(n_wrapper(rqsts))

        with ThreadPoolExecutor() as executor:
            executor.submit(thread_target)

        app.logger.info("Student %s has logged out", args.get("StudentID"))

        # Getting rid of spoiled cookies.
        mid_res = make_response("", 200)
        mid_res.set_cookie("SessionID", "", httponly=False, secure=False, samesite="Lax")
        mid_res.set_cookie("StudentID", "", httponly=False, secure=False, samesite="Lax")

        return mid_res


class Verify(Resource):

    def post(self):
        """
        LogOut Endpoint
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

        def request():
            return asyncio.run(wrapper(
            {
                "method": "POST",
                "url": ROOT,
                "data": "ajx=1",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": user_agent,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            }))
        mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            read_msgs(args.get("SessionID"), parser.msgParser2(mid_res.get("text")))
            mid_res = request()

        if parser.isThereMsg(mid_res.get("text")):
            abort(412, help="Bad request from root server")

        if not mid_res["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(mid_res.get("text")):
            abort(401, help="Session invalid or has expired")

        return make_response("", 200)


class Bot(Resource):
    def get(self):
        """
        Bot Endpoint
        ---
        summary: Bot status
        description: Gets Bot status for current user.
        responses:
            200:
                description: Bot status
            400:
                description: Invalid credentials
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
        db_res = db_cur.execute("""
            SELECT ss.owner_id, s.active_telegram_id, s.active_discord_id, s.active_email_id
            FROM Student_Sessions ss
            INNER JOIN Students s
            ON ss.owner_id = s.id
            WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
            LIMIT 1;
        """, (args.get("StudentID"), args.get("SessionID"))).fetchone()
        if db_res is None:
            db_con.close()
            abort(401, help="Session invalid or has expired")

        subscriptions = {}
        owner_id = db_res["owner_id"]

        if db_res is not None:
            if db_res["active_telegram_id"] is not None:
                db_sub_res = db_cur.execute("""
                    SELECT ts.telegram_username FROM Telegram_Subscribers ts
                    INNER JOIN Students s
                    ON ts.telegram_id = s.active_telegram_id
                    WHERE s.id = ?;
                """, (owner_id, )).fetchone()
                if db_sub_res is not None:
                    subscriptions["telegram_username"] = db_sub_res["telegram_username"]
            if db_res["active_discord_id"] is not None:
                db_sub_res = db_con.cursor().execute("""
                    SELECT ds.discord_webhook_url FROM Discord_Subscribers ds
                    INNER JOIN Students s ON ds.discord_id = s.active_discord_id 
                    WHERE s.id = ?;  
                """, (owner_id, )).fetchone()
                if db_sub_res is not None:
                    subscriptions["discord_webhook_url"] = db_sub_res["discord_webhook_url"]
            if db_res["active_email_id"] is not None:
                db_sub_res = db_con.cursor().execute("""
                    SELECT es.email FROM Email_Subscribers es
                    INNER JOIN Students s ON es.email_id = s.active_email_id
                    WHERE s.id = ?;
                """, (owner_id, )).fetchone()
                if db_sub_res is not None:
                    subscriptions["email"] = db_sub_res["email"]

        db_con.close()
        return {"subscriptions": subscriptions}


    def put(self):
        """
        Bot Endpoint
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
                    telegram_username:
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
                description: Bot status
            400:
                description: Invalid credentials
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
            "telegram_username",
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
        db_res = db_con.cursor().execute("""
            SELECT ss.owner_id
            FROM Student_Sessions ss
            INNER JOIN Students s
            ON ss.owner_id = s.id
            WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
            LIMIT 1;
            """, (args.get("StudentID"), args.get("SessionID"))).fetchone()

        if db_res is None:
            db_con.close()
            abort(401, help="Session invalid or has expired")

        owner_id = db_res["owner_id"]
        if args.get("telegram_username") is not None:
            code = verify_code_gen(6)
            db_con.cursor().execute("""
                INSERT INTO Verifications
                (owner_id, verify_code, verify_item, verify_date, verify_service)
                VALUES(?, ?, ?, ?, 0);
            """, (owner_id, code, args.get("telegram_username"), datetime.datetime.now().isoformat()))
            db_con.commit()
            db_con.close()
            return {"telegram_code": code}, 204
        if args.get("discord_webhook_url") is not None:
            db_sub_res = db_con.cursor().execute("""
                INSERT INTO Discord_Subscribers(owner_id, discord_webhook_url)
                VALUES(?, ?)
                RETURNING discord_id;
            """, (owner_id, args.get("discord_webhook_url"))).fetchone()
            if db_sub_res is None:
                db_con.rollback()
                db_con.close()
                abort(400, help="Unknown error")
            db_con.commit()
            db_con.cursor().execute("""
                UPDATE Students
                SET active_discord_id = ?
                WHERE id = ?;
            """, (db_sub_res["discord_id"], owner_id))
            db_con.commit()
            db_con.close()
            return make_response("", 201)
        if args.get("email") is not None:
            code = verify_code_gen(6)
            db_con.cursor().execute("""
                INSERT INTO Verifications
                (owner_id, verify_code, verify_item, verify_date, verify_service)
                VALUES(?, ?, ?, ?, 1);
            """, (owner_id, code, args.get("email"), datetime.datetime.now().isoformat()))
            db_con.commit()
            db_con.close()
            return make_response("", 204)

        db_con.close()
        return '', 200


    def delete(self):
        """
        Bot Endpoint
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
                    telegram_username:
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
            200:
                description: Unsubscribed
            204:
                description: Nothing to do
            400:
                description: Cannot find the subscription
            401:
                description: Invalid credentials
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
            "telegram_username",
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
        db_res = db_cur.execute("""
            SELECT ss.owner_id, s.active_telegram_id, s.active_discord_id, s.active_email_id
            FROM Student_Sessions ss
            INNER JOIN Students s
            ON ss.owner_id = s.id
            WHERE s.student_id = ? AND ss.session_id = ? AND ss.logged_out = 0
            LIMIT 1;
            """, (args.get("StudentID"), args.get("SessionID"))).fetchone()

        if db_res is None:
            db_con.close()
            abort(401, help="Session invalid or has expired")
        owner_id = db_res["owner_id"]

        if db_res["active_telegram_id"] is not None and args.get("telegram_username") is not None:
            db_sub_res = db_cur.execute("""
                UPDATE Students
                SET active_telegram_id = NULL
                WHERE id = ? AND
                active_telegram_id = (
                    SELECT ts.telegram_id
                    FROM Telegram_Subscribers ts
                    WHERE ts.owner_id = ? AND ts.telegram_username = ?
                    ORDER BY ts.telegram_id DESC
                    LIMIT 1
                );
            """, (owner_id, owner_id, args.get("telegram_username")))
            if not db_sub_res.rowcount > 0:
                db_con.rollback()
                db_con.close()
                abort(400, help="Couldn't find the subscription")
            db_con.commit()
            db_con.close()
            return make_response("", 200)
        if db_res["active_discord_id"] is not None and args.get("discord_webhook_url") is not None:
            db_sub_res = db_cur.execute("""
                UPDATE Students
                SET active_discord_id = NULL
                WHERE id = ? AND
                active_discord_id = (
                    SELECT ds.discord_id
                    FROM Discord_Subscribers ds
                    WHERE ds.owner_id = ? AND ds.discord_webhook_url = ?
                    ORDER BY ds.discord_id DESC
                    LIMIT 1
                );
            """, (owner_id, owner_id, args.get("discord_webhook_url")))
            if not db_sub_res.rowcount > 0:
                db_con.rollback()
                db_con.close()
                abort(400, help="Couldn't find the subscription")
            db_con.commit()
            db_con.close()
            return make_response("", 200)
        if db_res["active_email_id"] is not None and args.get("email") is not None:
            db_sub_res = db_cur.execute("""
                UPDATE Students
                SET active_email_id = NULL
                WHERE id = ? AND
                active_email_id = (
                    SELECT es.email_id
                    FROM Email_Subscribers es
                    WHERE es.owner_id = ? AND es.email = ?
                    ORDER BY es.email_id DESC
                    LIMIT 1
                );
            """, (owner_id, owner_id, args.get("email")))
            if not db_sub_res.rowcount > 0:
                db_con.rollback()
                db_con.close()
                abort(400, help="Couldn't find the subscription")
            db_con.commit()
            db_con.close()
            return make_response("", 200)

        if (args.get("telegram_username") is not None or
            args.get("discord_webhook_url") is not None or
            args.get("email") is not None):
            abort(400, help="Couldn't find the subscription")

        db_con.close()
        return '', 204


def read_announce(sessid):
    asyncio.run(wrapper(
    {
        "method": "POST",
        "url": f"{ROOT}stud_announce.php",
        "data": "btnRead=Oxudum",
        "headers": {
            "Host": HOST,
            "Cookie": f"PHPSESSID={sessid}; ",
            "User-Agent": user_agent,
        }
    }))

def read_msgs(sessid, msg_ids):
    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def n_wrapper(rqsts):
            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session, req) for req in rqsts]
                return await asyncio.gather(*tasks)

        rqsts = [
        {
            "method": "POST",
            "url": ROOT,
            "data": f"ajx=1&mod=msg&action=ShowReceivedMessage&sm_id={id}",
            "headers": {
                "Host": HOST,
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": f"PHPSESSID={sessid}; ",
                "User-Agent": user_agent,
            }
        } for id in msg_ids]
        return loop.run_until_complete(n_wrapper(rqsts))

    with ThreadPoolExecutor() as executor:
        results = executor.submit(thread_target).result()

    return results

def verify_code_gen(length):
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

api.add_resource(Msg, "/api/resource/msg")
api.add_resource(Res, "/api/resource/<resource>")
api.add_resource(GradesAll, "/api/resource/grades/all")
api.add_resource(Grades, "/api/resource/grades/<int:year>/<int:semester>")
api.add_resource(AttendanceByCourse, "/api/resource/attendance/<int:course>")
api.add_resource(AttendanceBySemester, "/api/resource/attendance/<int:year>/<int:semester>")
api.add_resource(Deps, "/api/resource/deps/<code>")
api.add_resource(Program, "/api/resource/program/<int:code>/<int:year>")
api.add_resource(Auth, "/api/auth")
api.add_resource(LogOut, "/api/logout")
api.add_resource(Verify, "/api/verify")
api.add_resource(StudPhoto, "/api/studphoto")
api.add_resource(Bot, "/api/bot")
