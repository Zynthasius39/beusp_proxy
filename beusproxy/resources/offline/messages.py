from flask_restful import Resource

from ...common.utils import demo_response


class Msg(Resource):
    """Messages

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Messages Endpoint
        Returns all messages.
        ---
        tags:
          - Resource
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                $ref: "#/components/schemas/Message"
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
        """
        return demo_response("msg")
