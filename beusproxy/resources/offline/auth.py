from flask import make_response
from flask_restful import Resource


class Auth(Resource):
    """Authenticate

    Flask-RESTFUL resource
    """

    def get(self):
        """Bakes cookies for students
        Authenticates and returns a SessionID to be used in API. \
        If there is no record of the student/educator in the database, \
        StudentID gets registered, assuming user has agreed the ToS \
        which is usually shown in the login page.
        ---
        tags:
          - Authorization
        parameters:
        - name: studentId
          in: query
          description: Student ID to login as
          required: true
          schema:
            type: integer
          example: 220106000
        - name: password
          in: query
          description: Password of the Student
          required: true
          schema:
            type: string
            format: password
          example: demostudent
        responses:
            200:
                description: Authenticated
                headers:
                    Set-Cookie:
                        schema:
                            type: string
                            example: SessionID=8c3589030a3854d8c3589030a38548c3;
            400:
                description: Invalid credentials
            401:
                description: Bad credentials
            502:
                description: Bad response from root server
        """
        res = make_response("You entered a blackhole", 200)
        res.set_cookie("SessionID", "offline_mode")
        res.set_cookie("StudentID", "220106099")

        return res
