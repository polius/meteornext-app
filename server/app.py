# -*- coding: utf-8 -*-
import os
import sys
import json
import uuid
import datetime
import argparse
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from cron import Cron
import routes.setup

# Start Parser
parser = argparse.ArgumentParser(description='Meteor Next Server')
parser.add_argument('--setup', required=False, action='store_true', dest='setup', help='Start the configuration wizard')
args = parser.parse_args()

# Instantiate Flask App
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JWT_SECRET_KEY'] = '1T20PQAsDE37efH4APvJpgaV1rJse7bkl8+BfoSTLSM='  # Using Docker: os.environ.get('SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=8)  # days = 1
jwt = JWTManager(app)

# Instantiate & Register Settings Blueprint
setup = routes.setup.Setup(args, app)
app.register_blueprint(setup.blueprint())

# Enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

# Run with python
if __name__ == '__main__':
    BIND = setup.getBind()
    host = BIND[:BIND.find(':')]
    port = BIND[BIND.find(':')+1:]
    app.run(host=host, port=port, debug=False)

# Start cron
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    Cron(sql)
