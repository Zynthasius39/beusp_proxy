import requests
from flask import current_app as app
from flask import jsonify, make_response
from flask_restful import Resource, abort, reqparse
from requests import RequestException

from .. import parser
from ..common.utils import is_expired
from ..config import HOST, ROOT, USER_AGENT, REQUEST_TIMEOUT


class Deps(Resource):
    """Departments

    Flask-RESTFUL resource
    """

    def get(self, dep_code):
        """
        Departments Endpoint
        Returns the given department.
        ---
        tags:
          - Resource
        parameters:
          - name: dep_code
            description: Department Code
            in: path
            required: true
            example: DEP_IT_PROG
            type: string
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                $ref: "#/components/schemas/DepartmentPrograms"
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
                    "mod": "viewdeps",
                    "d": dep_code,
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
            abort(401, help="Session invalid or has expired")

        page = jsonify(parser.deps2(mid_res))
        res = make_response(page, 200)
        return res
