import requests
from flask import current_app as app
from flask import jsonify, make_response
from flask_restful import Resource, abort, reqparse
from requests import RequestException

from .. import parser
from ..common.utils import is_expired
from ..config import HOST, ROOT, USER_AGENT, REQUEST_TIMEOUT


class Program(Resource):
    """Programs

    Flask-RESTFUL resource
    """

    def get(self, code, year):
        """
        Programs Endpoint
        Returns the given program.
        ---
        tags:
          - Resource
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
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Program"
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
                ROOT,
                params={
                    "mod": "progman",
                    "pc": code,
                    "py": year,
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

            mid_res = mid_res.text
        except RequestException as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")
        if is_expired(mid_res):
            abort(401, help="errorApiUnauthorized")

        page = parser.program2(mid_res)

        if not page:
            abort(404, help="Not Found")
        res = make_response(jsonify(page), 200)
        return res
