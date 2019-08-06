import os
import json
import uuid
import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import routes.login
import routes.admin.groups
import routes.admin.users
import routes.deployments.environments
import routes.deployments.regions
import routes.deployments.servers

# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JWT_SECRET_KEY'] = '1T20PQAsDE37efH4APvJpgaV1rJse7bkl8+BfoSTLSM='  # Using Docker: os.environ.get('SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)  # days = 1
jwt = JWTManager(app)

# load mysql credentials
credentials = {}
with open('credentials.json') as file_open:
    credentials = json.load(file_open)
    credentials['path'] = os.path.dirname(os.path.abspath(__file__))

# Init all blueprints
login = routes.login.construct_blueprint(credentials)
groups = routes.admin.groups.construct_blueprint(credentials)
users = routes.admin.users.construct_blueprint(credentials)
environments = routes.deployments.environments.construct_blueprint(credentials)
regions = routes.deployments.regions.construct_blueprint(credentials)
servers = routes.deployments.servers.construct_blueprint(credentials)

# instantiate all routes
app.register_blueprint(login)
app.register_blueprint(groups)
app.register_blueprint(users)
app.register_blueprint(environments)
app.register_blueprint(regions)
app.register_blueprint(servers)

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')

if __name__ == '__main__':
    app.run(host='0.0.0.0')