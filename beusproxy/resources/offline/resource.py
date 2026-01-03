import os

from flask import make_response
from flask_restful import Resource, abort

from ...common.utils import demo_response
from ...config import DEMO_FOLDER


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
                                    $ref: "#/components/schemas/Department"
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
        demo_file = os.path.join(DEMO_FOLDER, f"{resource}.json")
        if not os.path.exists(demo_file):
            abort(404)

        res = make_response(demo_response(resource), 200)

        if resource == "home":
            res.set_cookie(
                "ImgID",
                "offline_img_id",
                httponly=False,
                secure=False,
                # samesite="Lax"
            )

        return res
