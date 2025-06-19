import requests
from flask import make_response, current_app as app
from flask_restful import Resource, abort, reqparse
from requests import RequestException

from ..config import HOST, ROOT, USER_AGENT, REQUEST_TIMEOUT


class Settings(Resource):
    """Settings Endpoint"""

    def post(self):
        """
        Settings Endpoint
        Changes settings.
        ---
        tags:
          - Operations
        requestBody:
          description: Language
          required: true
          content:
            application/json:
              schema:
                properties:
                    lang:
                        type: string
                        description: Language
                        example: en
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

        if args.get("lang") and args.get("lang").lower() in langs:
            try:
                mid_res = requests.request(
                    "GET",
                    ROOT,
                    params={
                        "mod": "setting",
                        "a": "update_interface_lang",
                        "lang": args.get("lang").upper(),
                    },
                    headers={
                        "Host": HOST,
                        "Cookie": f"PHPSESSID={args.get("SessionID")}; BEU_STUD_AR=1; ",
                        "User-Agent": USER_AGENT,
                    },
                    timeout=REQUEST_TIMEOUT,
                )
                if mid_res.status_code != 200:
                    abort(400, help="Invalid Language")
            except RequestException as ce:
                app.logger.error(ce)
                abort(502, help="Bad response from root server")

        return make_response("", 200)


langs = ["az", "en"]
