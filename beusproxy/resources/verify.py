import requests
from flask import current_app as app
from flask import make_response
from flask_restful import Resource, abort, reqparse
from requests import RequestException

from ..common.utils import is_expired
from ..config import HOST, ROOT, USER_AGENT, REQUEST_TIMEOUT


class Verify(Resource):
    """Session Verification

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Session Verify Endpoint
        Verify session.
        ---
        tags:
          - Authorization
        description: Check if session is still valid.
        responses:
            200:
                description: Verify successful
            401:
                description: Couldn't verify
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
                data={"ajx": 1},
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

        return make_response("", 200)
