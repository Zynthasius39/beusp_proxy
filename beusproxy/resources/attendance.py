import json

from flask import current_app as app, jsonify, make_response
from flask_restful import Resource, abort, reqparse

from .. import parser
from ..config import HOST, ROOT, USER_AGENT
from ..common.utils import is_expired
from ..context import c
from ..services.httpclient import HTTPClientError


class AttendanceBySemester(Resource):
    """Attendance by year and semester

    Flask-RESTFUL resource
    """

    def get(self, year, semester):
        """Gotta save your attendance for holidays
        Returns attendance in given semester.
        ---
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
                content:
                    application/json:
                        schema:
                            type: object
                            additionalProperties:
                                $ref: "#/components/schemas/CourseAttendance"
                            example:
                                BA108:
                                    absent: 1
                                    absentPercent: 7
                                    atds: 13
                                    courseEducator: John Doe
                                    courseName: Principles of Entrepreneurship and Introduction to Business
                                    credit: 1+1+0
                                    hours: 15
                                    limit: 3.75
                                ECON163:
                                    absent: 0
                                    absentPercent: 0
                                    atds: 14
                                    courseEducator: John Doe
                                    courseName: Engineering Economics
                                    credit: 1+1+0
                                    hours: 15
                                    limit: 3.75
            400:
                description: Bad response
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
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
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "POST",
                ROOT,
                data={
                    "ajx": 1,
                    "mod": "ejurnal",
                    "action": "getCourses",
                    "ysem": f"{year}#{semester}",
                },
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)
        except HTTPClientError as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        if is_expired(mid_res):
            abort(401, help="Session invalid or has expired")

        if not mid_res.find("No section found.") == -1:
            abort(400, help="No section found")

        page = jsonify(parser.attendance2(mid_res))
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
            format: int32
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/CourseAttendanceDetailed"
            400:
                description: Bad response
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
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
        args = rp.parse_args()

        try:
            mid_res = httpc.request(
                "POST",
                ROOT,
                data={
                    "ajx": 1,
                    "mod": "ejurnal",
                    "action": "viewCourse",
                    "derst": course,
                },
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                },
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)
        except HTTPClientError as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")
        if is_expired(mid_res):
            abort(401, help="Session invalid or has expired")

        ajax = json.loads(mid_res)
        if int(ajax["CODE"]) < 1:
            abort(400, help=ajax["DATA"])

        page = jsonify(parser.attendance3(ajax["DATA"]))
        res = make_response(page, 200)
        return res
