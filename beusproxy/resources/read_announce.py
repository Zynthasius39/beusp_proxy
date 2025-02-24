from flask import make_response
from flask_restful import Resource, abort, reqparse

from beusproxy.common.utils import read_announce

from ..context import c
from ..services.httpclient import HTTPClientError


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
        rq = reqparse.RequestParser()
        rq.add_argument(
            "SessionID",
            type=str,
            help="Invalid sessionid",
            location="cookies",
            required=True,
        )
        args = rq.parse_args()

        try:
            read_announce(c.get("httpc"), args.get("SessionID"))
        except HTTPClientError:
            abort(502)

        return make_response("", 200)
