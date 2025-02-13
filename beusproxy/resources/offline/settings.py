from flask_restful import Resource


class Settings(Resource):
    """Settings Endpoint"""

    def post(self):
        """
        Settings Endpoint
        ---
        summary: Changes settings.
        parameters:
        - name: body
          in: body
          description: Language
          required: true
          schema:
            properties:
                lang:
                    type: string
                    description: Language
                    example: EN
                    required: false
        responses:
            200:
                description: Success
            502:
                description: Bad response from root server
        """
        return "I definitely saved your changes (wupheli)."
