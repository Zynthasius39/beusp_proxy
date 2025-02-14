from flask import make_response
from flask_restful import Resource, reqparse, abort

from ..config import ROOT, HOST, USER_AGENT
from ..context import c


class Settings(Resource):
    """Settings Endpoint"""

    def post(self):
        """
        Settings Endpoint
        ---
        summary: Changes settings.
        parameters:
        - name: body
          in: body
          description: Language
          required: true
          schema:
            properties:
                lang:
                    type: string
                    description: Language
                    example: EN
                    required: false
        responses:
            200:
                description: Success
            400:
                description: Invalid Language
        """
        rp = reqparse.RequestParser()
        rp.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        rp.add_argument(
            "lang",
            type=str,
        )
        args = rp.parse_args()

        if args.get("lang") and args.get("lang").upper() in langs:
            mid_res = c.get("httpc").request(
                "GET",
                ROOT,
                params={
                    "mod": "setting",
                    "a": "update_interface_lang",
                    "lang": args.get("lang"),
                },
                headers={
                    "Host": HOST,
                    "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                    "User-Agent": USER_AGENT,
                },
            )
            if not mid_res.status:
                abort(400, help="Invalid Language")

        return make_response("", 200)


langs = ["AZ", "EN"]
