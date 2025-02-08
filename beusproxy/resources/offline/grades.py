from flask_restful import Resource

from ...common.utils import demo_response


class Grades(Resource):
    """Grades

    Flask-RESTFUL resource
    """

    def get(self, *_, **__):
        """
        Grades Endpoint
        ---
        summary: Returns grades in given semester.
        parameters:
          - name: year
            in: path
            required: true
            example: 2022
            type: number
          - name: semester
            in: path
            required: true
            example: 1 / 2
            type: number
        responses:
            200:
                description: Success
            400:
                description: Bad request
            401:
                description: Unauthorized
            412:
                description: Bad response from root server
        """
        return demo_response("grades2")


class GradesAll(Resource):
    """All Grades

    Flask-RESTFUL resource
    """

    def get(self):
        """
        Grades Endpoint
        ---
        summary: Returns grades in given semester.
        responses:
            200:
                description: Success
            400:
                description: Bad request
            401:
                description: Unauthorized
            412:
                description: Bad response from root server
        """
        return demo_response("grades_all")
