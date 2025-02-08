from flask_restful import Resource

from ...common.utils import demo_response


class Msg(Resource):
    """Messages

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Messages Endpoint
        ---
        summary: Returns all messages.
        responses:
            200:
                description: Success
            401:
                description: Unauthorized
            404:
                description: Not Found
            412:
                description: Bad response from root server
        """
        return demo_response("msg")
