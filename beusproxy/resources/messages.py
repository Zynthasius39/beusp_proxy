import requests
from flask import current_app as app
from flask import jsonify, make_response
from flask_restful import Resource, abort, reqparse
from requests import RequestException

from .. import parser
from ..common.utils import is_expired, read_msgs
from ..config import HOST, ROOT, USER_AGENT, REQUEST_TIMEOUT


class Msg(Resource):
    """Messages

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Messages Endpoint
        Returns all messages.
        ---
        tags:
          - Resource
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                $ref: "#/components/schemas/Message"
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

        msgs = []
        try:
            mid_res = requests.request(
                "GET",
                ROOT,
                params={
                    "mod": "msg",
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

            if is_expired(mid_res):
                abort(401, help="errorApiUnauthorized")

            msgs_raw = read_msgs(args.get("SessionID"), parser.msg(mid_res))
            msgs = [parser.msg2(msg_raw) for msg_raw in msgs_raw]

        except RequestException as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        res = make_response(jsonify(msgs), 200)
        return res
