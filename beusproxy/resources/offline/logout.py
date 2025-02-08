from flask import make_response
from flask_restful import Resource


class LogOut(Resource):
    """Logout

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
        return make_response("Spaghettified", 200)
