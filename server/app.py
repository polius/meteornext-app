import os
import secrets
import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from flask_compress import Compress
from flask_jwt_extended import (JWTManager, jwt_required)
import routes.setup

# App Version
version = '1.00-beta.0'

# Instantiate Flask App
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JSON_SORT_KEYS'] = False

# JWT Config
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
routes.setup.Setup(app, URL_PREFIX)

# Enable CORS
CORS(app)

# Health endpoint
@app.route("/api/health")
def health_method():
    return ''

# Version endpoint
@app.route('/api/version', methods=['GET'])
@jwt_required()
def version_method():
    return jsonify({'version': version}), 200

# Debug endpoint (to be deleted)
@app.route("/api/debug")
def debug_method():
    import socket
    import uuid
    from flask import jsonify
    return jsonify({'uuid': uuid.getnode(), 'ip': socket.gethostbyname(socket.gethostname())}), 200

# Run with python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=False)
