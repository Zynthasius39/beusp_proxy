from flask import make_response
from flask_restful import Resource


class ReadAnnounce(Resource):
    """Read Announce

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Read Announce Endpoint
        Reads announce pop-up, which changes absolutely nothing. \
        Middle response just sets BEU_STUD_AR=1 to skip announcement, \
        and we are already skipping those.
        ---
        tags:
          - Operations
        responses:
            200:
                description: Success
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
        """
        return make_response("", 200)
