from flask import make_response
from flask_restful import Resource, reqparse


class Verify(Resource):
    """Session Verification

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Session Verify Endpoint
        Verify session.
        ---
        tags:
          - Authorization
        description: Check if session is still valid.
        responses:
            200:
                description: Verify successful
            401:
                description: Couldn't verify
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
        rp.parse_args()

        return make_response("", 200)
