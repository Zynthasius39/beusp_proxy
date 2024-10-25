from flask import Flask, jsonify, request, make_response, render_template
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS
from session.tms import TMSession, SessionException
import json

app = Flask(__name__) 
api = Api(app)
CORS(app, origins=["*"])

SESSION = None;

@api.representation('text/html')
def output_html(data, code, headers=None):
    pass

class Index(Resource):
    """Main Endpoint

    Returns:
        _type_: _description_
    """
    
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('mod', type=str, help="Invalid page")
        # res = make_response(SESSION.get('?mod=' + args.get('mod')))
        res = make_response(SESSION.get('?mod=home'))
        res.headers['Content-Type'] = 'text/html'
        return res

class Auth(Resource):
    """Auth Endpoint

    Returns:
        201: Authenticated
        401: Bad credentials
        502: Bad response
    """
    
    def post(self): 
        global SESSION
        parser = reqparse.RequestParser()
        parser.add_argument('student_id', required=True, help="Missing the credential parameter in the JSON body")
        parser.add_argument('password', required=True, help="Missing the credential parameter in the JSON body")
        args = parser.parse_args()
        SESSION = TMSession(args.get('student_id'), args.get('password'))
        try:
            SESSION.auth()
        except SessionException as e:
            if (e.error_code == 10):
                abort(401)
            else:
                abort(502)
        return '', 201

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

api.add_resource(Index, '/')
api.add_resource(Auth, '/auth')
api.add_resource(LogOut, '/logout')