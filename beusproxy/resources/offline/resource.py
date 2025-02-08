import os

from flask import make_response
from flask_restful import Resource, abort

from ...config import DEMO_FOLDER
from ...common.utils import demo_response


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
            example: home
            schema:
                type: string
        responses:
            201:
                description: Success
                headers:
                    Cookie:
                        schema:
                            type: string
                            example: SessionID=8c3589030a3854d... (32 char);
            400:
                description: Invalid Page
            401:
                description: Unauthorized
            412:
                description: Bad response from root server
        """
        demo_file = os.path.join(DEMO_FOLDER, f"{resource}.json")
        if not os.path.exists(demo_file):
            abort(404)

        res = make_response(demo_response("program"), 200)

        if resource == "home":
            res.set_cookie(
                "ImgID", "offline_img_id", httponly=False, secure=False, samesite="Lax"
            )

        return res
