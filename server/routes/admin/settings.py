import os
import sys
import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.admin.settings

class Settings:
    def __init__(self, settings, sql):
        self._settings_conf = settings
        self._sql = sql
        # Init models
        self._users = models.admin.users.Users(sql)
        self._settings = models.admin.settings.Settings(sql)

    def blueprint(self):
        # Init blueprint
        settings_blueprint = Blueprint('settings', __name__, template_folder='settings')

        @settings_blueprint.route('/admin/settings', methods=['GET','PUT'])
        @jwt_required
        def settings_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            settings_json = request.get_json()

            if request.method == 'GET':
                return self.get()
            elif request.method == 'PUT':
                return self.put(settings_json)

        return settings_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        # Init Settings
        settings = {}

        # Get SQL Settings
        settings['sql'] = self._settings_conf['sql']
        settings['sql']['path'] = os.path.dirname(os.path.realpath(__file__)) if sys.argv[0].endswith('.py') else os.path.dirname(sys.executable)
        settings['sql']['path'] += '/settings.json'

        # Get API Settings
        settings['api'] = self._settings_conf['bind']

        # Get Logs Settings
        settings['logs'] = json.loads(self._settings.get()[0]['value'])

        # Return Settings
        return jsonify({'data': settings}), 200

    def put(self, data):
        self._settings.post(data)
        return jsonify({'message': 'Changes saved successfully'}), 200
