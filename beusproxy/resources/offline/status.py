from flask_restful import Resource

from ...common.utils import demo_response


class Status(Resource):
    """Root server status."""

    def get(self):
        """
        Status Endpoint
        Returns the status of root server and statistics. \
        Advanced status also retrieves and hashes static files of root \
        server to verify if any modification is present.
        ---
        tags:
          - Operations
        parameters:
        - name: advanced
          in: query
          description: Advanced status
          required: false
          schema:
            type: boolean
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: object
                            properties:
                                students_registered:
                                    type: integer
                                    format: int32
                                    example: 2
                                subscriptions:
                                    type: integer
                                    format: int32
                                    example: 5
                                root_server_is_up:
                                    type: boolean
                                    example: true
                                sha256sums:
                                    type: array
                                    items:
                                        type: string
                                        example: 1d750059806e36fa731f0b045e284\
                                        4bf52e150a404ab01ac5224dc7e10bbf040 general.js
                            required:
                             - students_registered
                             - subscriptions
                             - root_server_is_up
            502:
                description: Bad response from root server
        """
        return demo_response("status")
