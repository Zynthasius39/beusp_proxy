from flask import make_response
from flask_restful import Resource


class Auth(Resource):
    """Authenticate

    Flask-RESTFUL resource
    """

    def post(self):
        """
        Auth Endpoint
        ---
        summary: Returns Set-Cookie header.
        description: Authenticates and returns a SessionID to be used in API.
        parameters:
          - name: body
            in: body
            required: yes
            description: JSON parameters.
            schema:
                properties:
                    student_id:
                        type: string
                        description: Student ID to login as
                        example: 210987654
                    password:
                        type: string
                        description: Password of the Student
                        example: S3CR3T_P4SSW0RD
        responses:
            200:
                description: Authenticated
                headers:
                    Set-Cookie:
                        schema:
                            type: string
                            example: SessionID=8c3589030a3854d... (32 char);
            400:
                description: Invalid credentials
            401:
                description: Bad credentials
            403:
                description: Not implemented
            502:
                description: Bad response from root server
        """
        res = make_response("You entered a blackhole", 200)
        res.set_cookie("SessionID", "offline_mode")
        res.set_cookie("StudentID", "220106099")

        return res
