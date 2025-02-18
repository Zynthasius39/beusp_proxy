from flask_restful import Resource

from ...common.utils import demo_response


class Deps(Resource):
    """Departments

    Flask-RESTFUL resource
    """

    def get(self, *_, **__):
        """
        Departments Endpoint
        ---
        summary: Returns the given department.
        parameters:
          - name: dep_code
            description: Department Code
            in: path
            required: true
            example: DEP_IT_PROG
            type: string
        responses:
            200:
                description: Success
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                $ref: "#/components/schemas/DepartmentPrograms"
            401:
                description: Unauthorized
            502:
                description: Bad response from root server
        """
        return demo_response("deps2")
