from flask import Flask, jsonify, request, make_response, render_template
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS
from flasgger import Swagger
from session.sp import SPSession, SessionException
import json

app = Flask(__name__) 
swagger = Swagger(app)
api = Api(app)
CORS(app, origins=["*"])

# SESSION = None;
SESSION = SPSession("220106041", "KWUMADIHIH9uh0")
SESSION.phpsessid = "fs40fpojcam0ciao6khsqu9kl9"
SESSION.protectedSess = "fs4**********************"

class Index(Resource):
    
    def get(self):
        """
        Main Endpoint
        ---
        parameters:
          - in: path
            name: page
            type: string
        responses:
            201:
                description: Success
        """
        if (not SESSION):
            abort(502)
        parser = reqparse.RequestParser()
        parser.add_argument('page',
            type=str,
            help="Invalid page",
            location='args')
        args = parser.parse_args()
        page = SESSION.get(args.get('page'))
        # print(page)
        res = make_response({"A": args.get('page')}, 200)
        # res.headers['Content-Type'] = 'text/html'
        return res

class Auth(Resource):
    def post(self): 
        """
        Auth Endpoint
        ---
        parameters:
          - name: body
            in: body
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
            201:
                description: Authenticated
            401:
                description: Bad credentials
            502:
                description: Bad response
        """
        global SESSION
        parser = reqparse.RequestParser()
        parser.add_argument('student_id', required=True, help="Missing the credential parameter in the JSON body")
        parser.add_argument('password', required=True, help="Missing the credential parameter in the JSON body")
        args = parser.parse_args()
        SESSION = SPSession(args.get('student_id'), args.get('password'))
        # try:
            # SESSION.auth()
        # except SessionException as e:
            # if (e.error_code == 10):
                # abort(401)
            # else:
                # abort(502)
        response = make_response('', 201)
        response.headers['Set-Cookie'] = "PHPSESSID=" + SESSION.phpsessid
        return response

class LogOut(Resource):
    """LogOut Endpoint
    
    Returns:
        200: Logged out
        502: Bad response
    """
    
    def get(self):
        try:
            SESSION.logout()
        except SessionException as e:
            abort(502)
        return '', 200

api.add_resource(Index, '/get')
api.add_resource(Auth, '/auth')
api.add_resource(LogOut, '/logout')