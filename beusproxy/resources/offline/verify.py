from flask import make_response
from flask_restful import Resource, reqparse


class Verify(Resource):
    """Session Verification

    Flask-RESTFUL resource
    """

    def post(self):
        """
        LogOut Endpoint
        ---
        summary: Logs out given SessionID.
        description: Logs out the SessionID used in API.
        responses:
            200:
                description: Logged out
            400:
                description: Couldn't log out
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
