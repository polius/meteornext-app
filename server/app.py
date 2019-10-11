import os
import json
import uuid
import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import routes.login
import routes.profile
import routes.admin.settings
import routes.admin.groups
import routes.admin.users
import routes.deployments.settings.environments
import routes.deployments.settings.regions
import routes.deployments.settings.servers
import routes.deployments.settings.auxiliary
import routes.deployments.settings.slack
import routes.deployments.deployments
import routes.deployments.views.basic
import routes.deployments.views.pro

# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JWT_SECRET_KEY'] = '1T20PQAsDE37efH4APvJpgaV1rJse7bkl8+BfoSTLSM='  # Using Docker: os.environ.get('SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=2)  # days = 1
jwt = JWTManager(app)

# load mysql credentials
credentials = {}
with open('credentials.json') as file_open:
    credentials = json.load(file_open)
    credentials['path'] = os.path.dirname(os.path.abspath(__file__))

# Init all blueprints
login = routes.login.Login(credentials).blueprint()
profile = routes.profile.Profile(credentials).blueprint()
settings = routes.admin.settings.Settings(credentials).blueprint()
groups = routes.admin.groups.Groups(credentials).blueprint()
users = routes.admin.users.Users(credentials).blueprint()
environments = routes.deployments.settings.environments.Environments(credentials).blueprint()
regions = routes.deployments.settings.regions.Regions(credentials).blueprint()
servers = routes.deployments.settings.servers.Servers(credentials).blueprint()
auxiliary = routes.deployments.settings.auxiliary.Auxiliary(credentials).blueprint()
slack = routes.deployments.settings.slack.Slack(credentials).blueprint()
deployments = routes.deployments.deployments.Deployments(credentials).blueprint()
deployments_basic = routes.deployments.views.basic.Basic(credentials).blueprint()
deployments_pro = routes.deployments.views.pro.Pro(credentials).blueprint()

# instantiate all routes
app.register_blueprint(login)
app.register_blueprint(profile)
app.register_blueprint(settings)
app.register_blueprint(groups)
app.register_blueprint(users)
app.register_blueprint(environments)
app.register_blueprint(regions)
app.register_blueprint(servers)
app.register_blueprint(auxiliary)
app.register_blueprint(slack)
app.register_blueprint(deployments)
app.register_blueprint(deployments_basic)
app.register_blueprint(deployments_pro)

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')

if __name__ == '__main__':
    app.run(host='0.0.0.0')