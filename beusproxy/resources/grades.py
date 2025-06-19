import time

import requests
from flask import current_app as app
from flask import jsonify, make_response
from flask_restful import Resource, abort, reqparse
from requests import RequestException

from .. import parser
from ..common.utils import is_expired
from ..config import HOST, ROOT, USER_AGENT, API_INTERNAL_HOSTNAME, REQUEST_TIMEOUT


class Grades(Resource):
    """Grades

    Flask-RESTFUL resource
    """

    def get(self, year, semester):
        """
        Grades Endpoint
        Returns grades in given semester.
        ---
        tags:
          - Resource
        parameters:
          - name: year
            in: path
            required: true
            example: 2022
            type: number
          - name: semester
            in: path
            required: true
            example: 1
            type: number
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: object
                            additionalProperties:
                                $ref: "#/components/schemas/CourseGrade"
                            example:
                                BA108:
                                    absents: 2
                                    act1: 15
                                    act2: 12.6
                                    addfinal: -1
                                    att: 10
                                    courseName: Principles of Entrepreneurship
                                    ects: 3
                                    final: 50
                                    iw: 10
                                    l: ""
                                    m: 4
                                    n: 3
                                    refinal: -1
                                    sum: 98
                                    year: 2022
                                    semester: 1
                                ECON163:
                                    absents: 0
                                    act1: 13.5
                                    act2: 15
                                    addfinal: -1
                                    att: 10
                                    courseName: Engineering Economics
                                    ects: 9
                                    final: 38
                                    iw: 10
                                    l: ""
                                    m: 4
                                    n: 3
                                    refinal: -1
                                    sum: 87
                                    year: 2022
                                    semester: 1
            400:
                description: Bad response
            401:
                description: Unauthorized
            502:
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
            mid_res = requests.request(
                "POST",
                ROOT,
                data={
                    "ajx": 1,
                    "mod": "grades",
                    "action": "GetGrades",
                    "yt": f"{year}#{semester}",
                    round(time.time()): "",
                },
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                },
                timeout=REQUEST_TIMEOUT,
            )

            if not mid_res.status_code == 200:
                abort(502, help="Bad response from root server")

        except RequestException as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")
        if is_expired(mid_res.text):
            abort(401, help="Session invalid or has expired")

        ajax = mid_res.json()
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

        page = jsonify(parser.grades2(text))
        res = make_response(page, 200)
        return res


class GradesAll(Resource):
    """All Grades

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Grades Endpoint
        Returns all grades.
        ---
        tags:
          - Resource
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: object
                            additionalProperties:
                                $ref: "#/components/schemas/CourseGrade"
                            example:
                                BA108:
                                    absents: 2
                                    act1: 15
                                    act2: 12.6
                                    addfinal: -1
                                    att: 10
                                    courseName: Principles of Entrepreneurship
                                    ects: 3
                                    final: 50
                                    iw: 10
                                    l: ""
                                    m: 4
                                    n: 3
                                    refinal: -1
                                    sum: 98
                                    year: 2022
                                    semester: 1
                                ECON163:
                                    absents: 0
                                    act1: 13.5
                                    act2: 15
                                    addfinal: -1
                                    att: 10
                                    courseName: Engineering Economics
                                    ects: 9
                                    final: 38
                                    iw: 10
                                    l: ""
                                    m: 4
                                    n: 3
                                    refinal: -1
                                    sum: 87
                                    year: 2022
                                    semester: 1
            400:
                description: Bad response
            401:
                description: Unauthorized
            502:
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
            mid_res = requests.request(
                "POST",
                ROOT,
                data={
                    "ajx": 1,
                    "mod": "grades",
                    "action": "GetGrades",
                    "yt": "1#1",
                    round(time.time()): "",
                },
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                },
                timeout=REQUEST_TIMEOUT,
            )

            if not mid_res.status_code == 200:
                abort(502, help="Bad response from root server")

        except RequestException as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        if is_expired(mid_res.text):
            abort(401, help="Session invalid or has expired")

        ajax = mid_res.json()
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

        page = jsonify(parser.grades2(text))
        res = make_response(page, 200)
        return res


class GradesLatest(Resource):
    """Latest Grades

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Grades Endpoint
        Returns latest grades semester.
        ---
        tags:
          - Resource
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: object
                            additionalProperties:
                                $ref: "#/components/schemas/CourseGrade"
                            example:
                                BA108:
                                    absents: 2
                                    act1: 15
                                    act2: 12.6
                                    addfinal: -1
                                    att: 10
                                    courseName: Principles of Entrepreneurship
                                    ects: 3
                                    final: 50
                                    iw: 10
                                    l: ""
                                    m: 4
                                    n: 3
                                    refinal: -1
                                    sum: 98
                                    year: 2022
                                    semester: 1
                                ECON163:
                                    absents: 0
                                    act1: 13.5
                                    act2: 15
                                    addfinal: -1
                                    att: 10
                                    courseName: Engineering Economics
                                    ects: 9
                                    final: 38
                                    iw: 10
                                    l: ""
                                    m: 4
                                    n: 3
                                    refinal: -1
                                    sum: 87
                                    year: 2022
                                    semester: 1
            400:
                description: Bad response
            401:
                description: Unauthorized
            502:
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
            mid_res = requests.request(
                "GET",
                f"{API_INTERNAL_HOSTNAME}resource/grades",
                headers={
                    "Host": HOST,
                    "Cookie": f"SessionID={args.get("SessionID")};",
                    "User-Agent": USER_AGENT,
                },
                timeout=REQUEST_TIMEOUT,
            )

            mid_json = mid_res.json()
            if not mid_res.status_code == 200:
                return mid_json, mid_res.status_code

            year, semester = (
                mid_json["entries"][-1]["year"],
                mid_json["entries"][-1]["semester"],
            )

            if not mid_json.get("entries"):
                abort(502, help="Bad response from root server")

            mid_res = requests.request(
                "GET",
                f"{API_INTERNAL_HOSTNAME}resource/grades/{year}/{semester}",
                headers={
                    "Host": HOST,
                    "Cookie": f"SessionID={args.get("SessionID")};",
                    "User-Agent": USER_AGENT,
                },
                timeout=REQUEST_TIMEOUT
            )

            mid_json = mid_res.json()
            if not mid_res.status_code == 200:
                return mid_json, mid_res.status_code
        except RequestException as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        res = make_response(mid_json, 200)
        return res
