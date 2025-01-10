import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
import time
import json
import re
import aiohttp
from flask import Flask, jsonify, make_response
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS
from config import *
from controller.aiohttp import make_request, wrapper
from middleman import parser
import secrets
import requests

app = Flask(__name__)
api = Api(app)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://10.0.10.75:5173"}})
SESSIONS = {}

tms_pages = {
    "home": "home",
    "grades": "grades",
    "faq": "faq",
    "announces": "elan",
    "deps": "viewdeps",
    "transcript": "transkript",
}

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
                            example: SessionID=8c3589030a3854dc98100b0eeaa0ff67f1ba384895dbd6138dfabj25220694f9;
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

        resourceParser = None
        try:
            resourceParser = getattr(parser, f"{resource}Parser")
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
                    "User-Agent": userAgent,
                }
            }))
        middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            readMsgs(args.get("SessionID"), parser.msgParser2(middleResponse.get("text")))
            middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            abort(412, help="Bad request from root server")

        if not middleResponse["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(middleResponse.get("text")):
            abort(401, help="Session invalid or has expired")

        page = resourceParser(middleResponse.get("text"))
        res = make_response(jsonify(page), 200)

        if resource == "home":
            res.set_cookie("ImgID", page.get("home").get("image"), httponly=False, secure=False, samesite="Lax")

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
                    "User-Agent": userAgent,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            }))
        middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            readMsgs(args.get("SessionID"), parser.msgParser2(middleResponse.get("text")))
            middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            abort(412, help="Bad request from root server")

        if not middleResponse["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(middleResponse.get("text")):
            abort(401, help="Session invalid or has expired")

        ajax = json.loads(middleResponse.get("text"))
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
                "data": f"ajx=1&mod=grades&action=GetGrades&yt={year}#{semester}&{round(time.time())}",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": userAgent,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            }))
        middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            readMsgs(args.get("SessionID"), parser.msgParser2(middleResponse.get("text")))
            middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            abort(412, help="Bad request from root server")

        if not middleResponse["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(middleResponse.get("text")):
            abort(401, help="Session invalid or has expired")

        ajax = json.loads(middleResponse.get("text"))
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
                    "User-Agent": userAgent,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            }))
        middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            readMsgs(args.get("SessionID"), parser.msgParser2(middleResponse.get("text")))
            middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            abort(412, help="Bad request from root server")

        if not middleResponse["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(middleResponse.get("text")):
            abort(401, help="Session invalid or has expired")

        if not middleResponse.get("text").find("No section found.") == -1:
            abort(400, help="No section found")

        page = jsonify(parser.attendanceParser2(middleResponse.get("text")))
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
                    "User-Agent": userAgent,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            }))
        middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            readMsgs(args.get("SessionID"), parser.msgParser2(middleResponse.get("text")))
            middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            abort(412, help="Bad request from root server")

        if not middleResponse["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(middleResponse.get("text")):
            abort(401, help="Session invalid or has expired")

        ajax = json.loads(middleResponse.get("text"))
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
                    "User-Agent": userAgent,
                }
            }))
        middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            readMsgs(args.get("SessionID"), parser.msgParser2(middleResponse.get("text")))
            middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            abort(412, help="Bad request from root server")

        if not middleResponse["status"] == 200:
            abort(412, help="Bad request from gateway")

        if parser.isExpired(middleResponse.get("text")):
            abort(401, help="Session invalid or has expired")

        page = jsonify(parser.depsParser2(middleResponse.get("text")))
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
                    "User-Agent": userAgent,
                }
            }))
        middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            readMsgs(args.get("SessionID"), parser.msgParser2(middleResponse.get("text")))
            middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            abort(412, help="Bad request from root server")

        if not middleResponse["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(middleResponse.get("text")):
            abort(401, help="Session invalid or has expired")

        page = parser.programParser2(middleResponse.get("text"))

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
                    "User-Agent": userAgent,
                }
            }))
        middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            readMsgs(args.get("SessionID"), parser.msgParser2(middleResponse.get("text")))
            middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            abort(412, help="Bad request from root server")

        if not middleResponse["status"] == 200:
            abort(412, help="Bad request from gateway")

        if parser.isExpired(middleResponse.get("text")):
            abort(401, help="Session invalid or has expired")

        results = readMsgs(args.get("SessionID"), parser.msgParser(middleResponse.get("text")))

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

        middleResponse = requests.get(
            f"{ROOT}stud_photo.php?ses={args.get("ImgID")}",
            headers = {
                "Host": HOST,
                "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                "User-Agent": userAgent,
            },
            timeout = 10
        )

        if not middleResponse.status_code == 200:
            abort(412, help="Bad request from gateway")

        res = make_response(middleResponse.content)
        res.headers.set("Content-Type", "image/png")
        res.headers.set("Content-Length", len(middleResponse.content))

        return res


class Auth(Resource):
    def post(self):
        """
        Auth Endpoint
        ---
        summary: Returns Set-Cookie header.
        description: Authenticates and returns a SessionID to be used in API.
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
                        example: 210987654
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
                            example: SessionID=8c3589030a3854dc98100b0eeaa0ff67f1ba384895dbd6138dfabj25220694f9;
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

        sessid = secrets.token_hex(32)
        print(f"Student {student_id} has logged in")
        SESSIONS[student_id] = {"student_id": student_id, "sessid": sessid}

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
                    "User-Agent": userAgent,
                }
            }))
        middleResponse = request()

        if not middleResponse["status"] == 302:
            abort(400, help="Bad credentials")

        cookies = middleResponse.get("headers").get("Set-Cookie")

        if not cookies:
            abort(412, "Couldn't get the cookies")

        for header in cookies.replace(" ", "").split(";"):
            if not header.find("PHPSESSID") == -1:
                sessid = header.split("=")[1]

        middleResponse = make_response("", 200)
        middleResponse.set_cookie("SessionID", sessid, httponly=False, secure=False, samesite="Lax", max_age=3600)
        middleResponse.set_cookie("StudentID", student_id, httponly=False, secure=False, samesite="Lax", max_age=3600)

        return middleResponse


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
        args = rp.parse_args()

        def request():
            return asyncio.run(wrapper(
            {
                "method": "GET",
                "url": f"{ROOT}logout.php",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": userAgent,
                }
            }))
        middleResponse = request()

        if not middleResponse["status"] == 302:
            abort(400, help="Couldn't logout")

        middleResponse = make_response("", 200)
        middleResponse.set_cookie("SessionID", "", httponly=False, secure=False, samesite="Lax")
        middleResponse.set_cookie("StudentID", "", httponly=False, secure=False, samesite="Lax")

        return middleResponse


class Verify(Resource):

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
        args = rp.parse_args()

        def request():
            return asyncio.run(wrapper(
            {
                "method": "POST",
                "url": ROOT,
                "data": f"ajx=1",
                "headers": {
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": userAgent,
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            }))
        middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            readMsgs(args.get("SessionID"), parser.msgParser2(middleResponse.get("text")))
            middleResponse = request()

        if parser.isThereMsg(middleResponse.get("text")):
            abort(412, help="Bad request from root server")

        if not middleResponse["status"] == 200:
            abort(412, help="Bad request from root server")

        if parser.isExpired(middleResponse.get("text")):
            abort(401, help="Session invalid or has expired")

        return ""


def readAnnounce(sessid):
    asyncio.run(wrapper(
    {
        "method": "POST",
        "url": f"{ROOT}stud_announce.php",
        "data": "btnRead=Oxudum",
        "headers": {
            "Host": HOST,
            "Cookie": f"PHPSESSID={sessid}; ",
            "User-Agent": userAgent,
        }
    }))

def readMsgs(sessid, msg_ids):
    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def wrapper(requests):
                async with aiohttp.ClientSession() as session:
                    tasks = [make_request(session, req) for req in requests]
                    return await asyncio.gather(*tasks)

        requests = [
        {
            "method": "POST",
            "url": ROOT,
            "data": f"ajx=1&mod=msg&action=ShowReceivedMessage&sm_id={id}",
            "headers": {
                "Host": HOST,
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": f"PHPSESSID={sessid}; ",
                "User-Agent": userAgent,
            }
        } for id in msg_ids]
        return loop.run_until_complete(wrapper(requests))

    with ThreadPoolExecutor() as executor:
        results = executor.submit(thread_target).result()

    return results

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
