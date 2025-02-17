from flask import current_app as app, jsonify, make_response
from flask_restful import Resource, abort, reqparse

from .. import parser
from ..config import HOST, ROOT, USER_AGENT
from ..common.utils import is_expired
from ..context import c
from ..services.httpclient import HTTPClientError


class Res(Resource):
    """Resource

    Flask-RESTFUL resource
    """

    def get(self, resource):
        """
        Resource Endpoint
        ---
        summary: Returns specified resource.
        parameters:
          - name: resource
            in: path
            required: true
            description: home, faq, deps, grades, announces, transcript
            example: deps
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
                              - $ref: "#/components/schemas/SemesterTable"
                              - $ref: "#/components/schemas/Transcript"
                              - type: array
                                items:
                                    $ref: "#/components/schemas/FaqItem"
                              - type: array
                                items:
                                    $ref: "#/components/schemas/Message"
                              - type: array
                                items:
                                    $ref: "#/components/schemas/Department"
                              - type: array
                                items:
                                    $ref: "#/components/schemas/Announce"
            400:
                description: Invalid Page
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
        """
        # TODO: Add grades
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

        # Prevent accessing not assigned resources.
        if not tms_pages.get(resource):
            abort(404)

        # Trying to get respective parser function.
        res = None
        try:
            res = getattr(parser, resource)
        except AttributeError:
            abort(404)

        try:
            mid_res = httpc.request(
                "POST",
                f"{ROOT}?mod={tms_pages[resource]}",
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

        page = res(mid_res)
        res = make_response(jsonify(page), 200)

        # Bake ImgID cookie if accessing home resource.
        if resource == "home":
            res.set_cookie(
                "ImgID",
                page.get("home").get("image"),
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
    "deps": "viewdeps",
    "transcript": "transkript",
}
