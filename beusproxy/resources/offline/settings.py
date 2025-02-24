from flask_restful import Resource


class Settings(Resource):
    """Settings Endpoint"""

    def post(self):
        """
        Settings Endpoint
        Changes settings.
        ---
        tags:
          - Operations
        requestBody:
          description: Language
          required: true
          content:
            application/json:
              schema:
                properties:
                    lang:
                        type: string
                        description: Language
                        example: en
                        required: false
        responses:
            200:
                description: Success
            400:
                description: Invalid Language
        """
        return "I definitely saved your changes (wupheli)."
