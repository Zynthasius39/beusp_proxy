from flask_restful import Resource

from ...common.utils import demo_response

class Status(Resource):
    """Root server status."""
    def get(self):
        """
        Status Endpoint
        ---
        summary: Returns the status of root server and statistics.
        responses:
            200:
                description: Success
            502:
                description: Bad response from root server
        """
        return demo_response("status")
