from flask import Flask, jsonify
from session.tms import TMSession

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'message': 'Welcoem to UBEU!'})

@app.route('/auth', methods=['POST'])
def auth():
    return "salam"
    
if __name__ == '__main__':
    app.run(debug=True)