from aiohttp import ClientError, ClientResponseError
from flask import current_app as app, make_response
from flask_restful import Resource, abort, reqparse

from ..config import HOST, ROOT, USER_AGENT
from ..common.utils import is_expired
from ..context import c


class Verify(Resource):
    """Session Verification

    Flask-RESTFUL resource
    """

    def post(self):
        """
        Session Verify Endpoint
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
                data="ajx=1",
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

        return make_response("", 200)
