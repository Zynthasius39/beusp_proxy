import json
import time

from aiohttp import ClientError, ClientResponseError
from flask import current_app as app, jsonify, make_response
from flask_restful import Resource, abort, reqparse

from .. import parser
from ..config import HOST, ROOT, USER_AGENT
from ..common.utils import is_expired
from ..context import c


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
        if is_expired(mid_res):
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

        if is_expired(mid_res):
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

        page = jsonify(parser.grades2(text))
        res = make_response(page, 200)
        return res
