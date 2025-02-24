from flask import current_app as app
from flask import jsonify, make_response
from flask_restful import Resource, abort, reqparse

from .. import parser
from ..common.utils import is_expired, read_msgs
from ..config import HOST, ROOT, USER_AGENT
from ..context import c
from ..services.httpclient import HTTPClientError


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

        msgs = []
        try:
            mid_res = httpc.request(
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
            )

            if not mid_res.status == 200:
                abort(502, help="Bad response from root server")

            mid_res = httpc.cr_text(mid_res)

            if is_expired(mid_res):
                abort(401, help="Session invalid or has expired")

            results = read_msgs(httpc, args.get("SessionID"), parser.msg(mid_res))

            for res in results:
                if res.status == 200:
                    msgs.append(parser.msg2(httpc.cr_text(res)))
        except HTTPClientError as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        res = make_response(jsonify(msgs), 200)
        return res
