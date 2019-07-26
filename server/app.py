import os
import uuid
import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from routes.deployments import deployments
from routes.login import login

# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JWT_SECRET_KEY'] = '1T20PQAsDE37efH4APvJpgaV1rJse7bkl8+BfoSTLSM='  # Using Docker: os.environ.get('SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)
jwt = JWTManager(app)

# instantiate all routes
app.register_blueprint(deployments)
app.register_blueprint(login)

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')

if __name__ == '__main__':
    app.run(host='0.0.0.0')