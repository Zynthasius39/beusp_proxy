from flask import Flask, jsonify, request 
from flask_restful import reqparse, abort, Api, Resource
from session.tms import TMSession

# creating the flask app 
app = Flask(__name__) 
# creating an API object 
api = Api(app) 

session = None;

parser = reqparse.RequestParser()
parser.add_argument('student_id')
parser.add_argument('password')

class Auth(Resource): 
    def get(self):
        return TODOS

    def post(self): 
        args = parser.parse_args()
        session = TMSession(args['student_id'], args['password'])
        print(session)
        return session.json(), 201

api.add_resource(Auth, '/auth') 

if __name__ == '__main__': 
	app.run(debug = True) 