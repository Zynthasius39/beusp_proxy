import os

from flask import make_response
from flask_restful import Resource, abort, reqparse

from ...config import DEMO_FOLDER


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
            "ImgID",
            type=str,
            help="Invalid imgid",
            location="cookies",
            required=True,
        )
        rp.parse_args()

        photo_file = os.path.join(DEMO_FOLDER, "studphoto.jpg")
        if not os.path.exists(photo_file):
            abort(503, help="Demo Student's Photo doesn't exist")

        with open(photo_file, "rb") as f:
            img = f.read()

        res = make_response(img, 200)
        res.headers.set("Content-Type", "image/jpg")
        res.headers.set("Content-Length", len(img))

        return res
