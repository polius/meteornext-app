import os
import datetime
import secrets
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_compress import Compress
import routes.setup

# Instantiate Flask App
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JWT_SECRET_KEY'] = secrets.token_urlsafe(nbytes=64)
app.secret_key = app.config['JWT_SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=12)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = 'SECURE' in os.environ and os.environ['SECURE'] == 'True'
app.config['JWT_COOKIE_SAMESITE'] = 'Strict'
jwt = JWTManager(app)

# Compress Flask application's responses with gzip, deflate or brotli
Compress(app)

# Instantiate & Register Settings Blueprint
URL_PREFIX = "/api"
setup = routes.setup.Setup(app, URL_PREFIX)
app.register_blueprint(setup.blueprint(), url_prefix=URL_PREFIX)

# Enable CORS
CORS(app)

# Run with python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=False)
