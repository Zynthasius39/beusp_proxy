from flask_restful import Resource

from ...common.utils import demo_response


class Grades(Resource):
    """Grades

    Flask-RESTFUL resource
    """

    def get(self, *_, **__):
        """
        Grades Endpoint
        Returns grades in given semester.
        ---
        tags:
          - Resource
        parameters:
          - name: year
            in: path
            required: true
            example: 2022
            type: number
          - name: semester
            in: path
            required: true
            example: 1
            type: number
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: object
                            additionalProperties:
                                $ref: "#/components/schemas/CourseGrade"
                            example:
                                BA108:
                                    absents: 2
                                    act1: 15
                                    act2: 12.6
                                    addfinal: -1
                                    att: 10
                                    courseName: Principles of Entrepreneurship
                                    ects: 3
                                    final: 50
                                    iw: 10
                                    l: ""
                                    m: 4
                                    n: 3
                                    refinal: -1
                                    sum: 98
                                    year: 2022
                                    semester: 1
                                ECON163:
                                    absents: 0
                                    act1: 13.5
                                    act2: 15
                                    addfinal: -1
                                    att: 10
                                    courseName: Engineering Economics
                                    ects: 9
                                    final: 38
                                    iw: 10
                                    l: ""
                                    m: 4
                                    n: 3
                                    refinal: -1
                                    sum: 87
                                    year: 2022
                                    semester: 1
            400:
                description: Bad response
            401:
                description: Unauthorized
            502:
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
        Returns all grades.
        ---
        tags:
          - Resource
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: object
                            additionalProperties:
                                $ref: "#/components/schemas/CourseGrade"
                            example:
                                BA108:
                                    absents: 2
                                    act1: 15
                                    act2: 12.6
                                    addfinal: -1
                                    att: 10
                                    courseName: Principles of Entrepreneurship
                                    ects: 3
                                    final: 50
                                    iw: 10
                                    l: ""
                                    m: 4
                                    n: 3
                                    refinal: -1
                                    sum: 98
                                    year: 2022
                                    semester: 1
                                ECON163:
                                    absents: 0
                                    act1: 13.5
                                    act2: 15
                                    addfinal: -1
                                    att: 10
                                    courseName: Engineering Economics
                                    ects: 9
                                    final: 38
                                    iw: 10
                                    l: ""
                                    m: 4
                                    n: 3
                                    refinal: -1
                                    sum: 87
                                    year: 2022
                                    semester: 1
            400:
                description: Bad response
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
        """
        return demo_response("grades_all")
