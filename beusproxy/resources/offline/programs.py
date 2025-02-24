from flask_restful import Resource

from ...common.utils import demo_response


class Program(Resource):
    """Programs

    Flask-RESTFUL resource
    """

    def get(self, *_, **__):
        """
        Programs Endpoint
        Returns the given program.
        ---
        tags:
          - Resource
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
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/Program"
            400:
                description: Bad response
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
        """
        return demo_response("program")
