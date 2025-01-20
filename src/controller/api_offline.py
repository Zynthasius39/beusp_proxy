import json
import os

from flask import Flask, make_response
from flask_restful import Api, Resource, abort, reqparse
from flask_cors import CORS
from flasgger import Swagger

from middleman import parser_offline



app = Flask(__name__)
api = Api(app)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://10.0.10.75:5173"}})
FLASGGER_ENABLED = os.getenv("SWAGGER_ENABLED", "false").lower() == "true"

if FLASGGER_ENABLED:
    app.config["SWAGGER"] = {
        "title": "Baku Engineering University: TMS/PMS - Rest API",
        "uiversion": 3,
    }

    swagger = Swagger(app)


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
        res_parser = None
        try:
            res_parser = getattr(parser_offline, f"{resource}_parser_offline")
        except AttributeError:
            abort(404)

        page = json.loads(res_parser())
        res = make_response(page, 200)

        if resource == "home":
            res.set_cookie("ImgID", "offline_img_id",
                           httponly=False,
                           secure=False,
                           samesite="Lax")

        return res


class GradesAll(Resource):
    """All Grades

    Flask-RESTFUL resource
    """

    def get(self):
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
        return json.loads(parser_offline.grades_all_parser_offline())


class Grades(Resource):
    """Grades

    Flask-RESTFUL resource
    """

    def get(self, _, __):
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
        return json.loads(parser_offline.grades2_parser_offline())


class AttendanceBySemester(Resource):
    """Attendance by year and semester

    Flask-RESTFUL resource
    """

    def get(self, _, __):
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
        return json.loads(parser_offline.attendance2_parser_offline())


class AttendanceByCourse(Resource):
    """Attendance by course

    Flask-RESTFUL resource
    """

    def get(self, _):
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
        return json.loads(parser_offline.attendance3_parser_offline())


class Deps(Resource):
    """Departments

    Flask-RESTFUL resource
    """

    def get(self, _):
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
        return json.loads(parser_offline.deps2_parser_offline())


class Program(Resource):
    """Programs

    Flask-RESTFUL resource
    """

    def get(self, _, __):
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
        return json.loads(parser_offline.program_parser_offline())


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
        return json.loads(parser_offline.msg_parser_offline())


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
            "ImgID",
            type=str,
            help="Invalid imgid",
            location="cookies",
            required=True,
        )
        rp.parse_args()

        with open("demo/studphoto.jpg", "rb") as f:
            img = f.read()

        res = make_response(img, 200)
        res.headers.set("Content-Type", "image/jpg")
        res.headers.set("Content-Length", len(img))

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
        res = make_response("You entered a blackhole", 200)
        res.set_cookie("SessionID", "offline_mode")
        res.set_cookie("StudentID", "220106099")

        return res


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
        return make_response("Spaghettified", 200)


class Verify(Resource):
    """Session Verification

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
        rp.parse_args()

        return ""

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
