import requests
from flask import current_app as app
from flask import jsonify, make_response
from flask_restful import Resource, abort, reqparse
from requests import RequestException

from .. import parser
from ..common.utils import is_expired, is_there_msg, read_msgs
from ..config import HOST, ROOT, USER_AGENT, REQUEST_TIMEOUT


class Res(Resource):
    """Resource

    Flask-RESTFUL resource
    """

    def get(self, resource):
        """
        Resource Endpoint
        Returns specified resource.
        ---
        tags:
          - Resource
        parameters:
          - name: resource
            in: path
            required: true
            description: home, faq, grades, announces, transcript
            example: home
            schema:
                type: string
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            oneOf:
                              - $ref: "#/components/schemas/HomeTable"
                              - $ref: "#/components/schemas/Semesters"
                              - $ref: "#/components/schemas/Transcript"
                              - type: array
                                items:
                                    $ref: "#/components/schemas/FaqItem"
                              - type: array
                                items:
                                    $ref: "#/components/schemas/Message"
                              - type: array
                                items:
                                    $ref: "#/components/schemas/Announce"
            400:
                description: Invalid Page
            401:
                description: Unauthorized
            404:
                description: Resource not found
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

        # Prevent accessing not assigned resources.
        if not tms_pages.get(resource):
            abort(404)

        # Trying to get respective parser function.
        res = None
        try:
            res = getattr(parser, resource)
        except AttributeError:
            abort(404)

        # Retry after reading messages
        mid_res = None
        for i in range(2):
            try:
                mid_res = requests.request(
                    "GET",
                    f"{ROOT}?mod={tms_pages[resource]}",
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

            if is_there_msg(mid_res):
                if i == 1:
                    abort(502, help="Bad response from root server")
                read_msgs(args.get("SessionID"), parser.msg_id(mid_res))
            else:
                break

        page = res(mid_res)
        res = make_response(jsonify(page), 200)

        # Bake ImgID cookie if accessing home resource.
        if resource == "home":
            res.set_cookie(
                "ImgID",
                page.get("image"),
                httponly=False,
                secure=False,
                samesite="Lax",
            )

        return res


tms_pages = {
    "home": "home",
    "grades": "grades",
    "faq": "faq",
    "announces": "elan",
#    "deps": "viewdeps",
    "transcript": "transkript",
}
