# -*- coding: utf-8 -*-
import datetime
import secrets
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import routes.setup

# Instantiate Flask App
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JWT_SECRET_KEY'] = secrets.token_urlsafe(nbytes=64)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=12)
jwt = JWTManager(app)

# Instantiate & Register Settings Blueprint
URL_PREFIX = "/api"
setup = routes.setup.Setup(app, URL_PREFIX)
app.register_blueprint(setup.blueprint(), url_prefix=URL_PREFIX)

# Enable CORS
CORS(app)

# Run with python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=False)
