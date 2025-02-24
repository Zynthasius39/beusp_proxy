from flask_restful import Resource

from ...common.utils import demo_response


class AttendanceBySemester(Resource):
    """Attendance by year and semester

    Flask-RESTFUL resource
    """

    def get(self, *_, **__):
        """Gotta save your attendance for holidays
        Returns attendance in given semester.
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
            example: 2
            type: number
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: object
                            additionalProperties:
                                $ref: "#/components/schemas/CourseAttendance"
                            example:
                                BA108:
                                    absent: 1
                                    absentPercent: 7
                                    atds: 13
                                    courseEducator: John Doe
                                    courseName: Principles of Entrepreneurship
                                    credit: 1+1+0
                                    hours: 15
                                    limit: 3.75
                                ECON163:
                                    absent: 0
                                    absentPercent: 0
                                    atds: 14
                                    courseEducator: John Doe
                                    courseName: Engineering Economics
                                    credit: 1+1+0
                                    hours: 15
                                    limit: 3.75
            400:
                description: Bad response
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
        Returns attendance for given course
        ---
        tags:
          - Resource
        parameters:
          - name: course_code
            in: path
            required: true
            example: 58120
            type: number
            format: int32
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            $ref: "#/components/schemas/CourseAttendanceDetailed"
            400:
                description: Bad response
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
        """
        return demo_response("attendance2")
