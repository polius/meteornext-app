import os
import sys
import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import utils
import models.admin.users
import models.admin.settings

class Settings:
    def __init__(self, app, settings, sql):
        self._app = app
        self._settings_conf = settings
        self._sql = sql
        # Init models
        self._users = models.admin.users.Users(sql)
        self._settings = models.admin.settings.Settings(sql)

    def license(self, value):
        self._license = value

    def blueprint(self):
        # Init blueprint
        settings_blueprint = Blueprint('settings', __name__, template_folder='settings')

        @settings_blueprint.route('/admin/settings', methods=['GET','PUT'])
        @jwt_required
        def settings_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

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
                return self.put(user['id'], settings_json)

        return settings_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        # Init Settings
        settings = {}
        s = self._settings.get()

        # Get License Settings
        settings['license'] = self._settings_conf['license']

        # Get SQL Settings
        settings['sql'] = self._settings_conf['sql']

        # Get Logs & Security Settings
        settings['logs'] = {}
        settings['security'] = {}
        for i in s:
            if i['name'] in ['LOGS', 'SECURITY']:
                settings[i['name'].lower()] = json.loads(i['value'])

        # Return Settings
        return jsonify({'data': settings}), 200

    def put(self, user_id, data):
        # Check logs path permissions
        if data['name'] == 'logs':
            u = utils.Utils()
            if not u.check_local_path(json.loads(data['value'])['local']['path']):
                return jsonify({'message': 'The local logs path has no write permissions'}), 400
        
        # Convert Setting name to uppercase
        data['name'] = data['name'].upper()

        # Edit logs settings
        self._settings.post(user_id, data)
        return jsonify({'message': 'Changes saved successfully'}), 200
