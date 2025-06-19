import requests
from flask import current_app as app
from flask import make_response
from flask_restful import Resource, abort, reqparse
from requests import RequestException

from ..config import HOST, ROOT, USER_AGENT, REQUEST_TIMEOUT


class StudPhoto(Resource):
    """Student Photo

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Student Photo Endpoint
        Returns student photo in jpeg format, as root server intends.
        ---
        tags:
          - Resource
        description: Returns student photo.
            You need to fetch home resource first to set
            ImgID cookie before using this endpoint.
        responses:
            200:
                description: Retrieved
                content:
                    image/jpeg:
                        schema:
                            type: string
                            format: binary
                            example: ""
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
        rp.add_argument(
            "ImgID",
            type=str,
            help="Invalid imgid",
            location="cookies",
            required=True,
        )
        args = rp.parse_args()

        try:
            mid_res = requests.request(
                "GET",
                f"{ROOT}stud_photo.php",
                params={
                    "ses": args.get("ImgID"),
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

            mid_res = mid_res.content
        except RequestException as ce:
            app.logger.error(ce)
            abort(502, help="Bad response from root server")

        res = make_response(mid_res)
        res.headers.set("Content-Type", "image/png")
        res.headers.set("Content-Length", len(mid_res))
        return res
