from flask import make_response
from flask_restful import Resource

from ...services.email import verify_email


class BotVerify(Resource):
    """BeuTMSBot Verification

    Flask-RESTFUL resource
    """

    # @api.representation("text/html")
    def get(self, code):
        # pylint: disable=R0915
        """
        Bot Verify Endpoint
        ---
        summary: Verification step
        description: Validate code and complete subscription step.
        produces:
          - text/html
        parameters:
          - name: code
            in: path
            required: true
            example: home
            schema:
                type: string
        responses:
            200:
                description: Return response in HTML
                content:
                    text/html:
                        schema:
                            type: string
            404:
                description: Bot is not active
            500:
                description: Problem with database
        """
        res = make_response(verify_email(code))
        return res
