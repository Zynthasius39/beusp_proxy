from flask_restful import Resource

from ...common.utils import demo_response


class Program(Resource):
    """Programs

    Flask-RESTFUL resource
    """

    def get(self, *_, **__):
        """
        Programs Endpoint
        ---
        summary: Returns the given program.
        parameters:
          - name: code
            in: path
            required: true
            example: 10106
            type: integer
          - name: year
            in: path
            required: true
            example: 2022
            type: integer
        responses:
            200:
                description: Success
            400:
                description: Bad request
            401:
                description: Unauthorized
            404:
                description: Not Found
            412:
                description: Bad response from root server
        """
        return demo_response("program")
