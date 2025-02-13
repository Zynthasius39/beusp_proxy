from flask_restful import Resource

from ...common.utils import demo_response


class AttendanceBySemester(Resource):
    """Attendance by year and semester

    Flask-RESTFUL resource
    """

    def get(self, *_, **__):
        """
        Attendance Endpoint
        ---
        summary: Returns attendance in given semester.
        parameters:
          - name: year
            in: path
            required: true
            example: 2022
            type: number
          - name: semester
            in: path
            required: true
            example: 2
            type: number
        responses:
            200:
                description: Success
            400:
                description: Bad request
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
        """
        return demo_response("attendance3")


class AttendanceByCourse(Resource):
    """Attendance by course

    Flask-RESTFUL resource
    """

    def get(self, *_, **__):
        """
        Attendance Endpoint
        ---
        summary: Returns attendance in given semester.
        parameters:
          - name: course
            in: path
            required: true
            example: 58120
            type: number
        responses:
            200:
                description: Success
            400:
                description: Bad request
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
        """
        return demo_response("attendance2")
