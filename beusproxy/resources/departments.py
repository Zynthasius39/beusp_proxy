
from flask import current_app as app, jsonify, make_response
from flask_restful import Resource, abort, reqparse

from .. import parser
from ..common.utils import is_expired
from ..config import HOST, ROOT, USER_AGENT
from ..context import c
from ..services.httpclient import HTTPClientError


class Deps(Resource):
    """Departments

    Flask-RESTFUL resource
    """

    def get(self, depCode):
        """
        Departments Endpoint
        ---
        summary: Returns the given department.
        parameters:
          - name: depCode
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
                                $ref: "#/components/schemas/Program"
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
        """
        # TODO: Fix all deps, programs, courses
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
                "GET",
                ROOT,
                params={
                    "mod": "viewdeps",
                    "d": depCode,
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

        page = jsonify(parser.deps2(mid_res))
        res = make_response(page, 200)
        return res
