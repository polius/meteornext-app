import os
import re
import sys
import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import utils
import models.admin.users
import models.admin.settings

class Settings:
    def __init__(self, app, sql, license, settings=None):
        self._app = app
        self._sql = sql
        self._license = license
        self._settings_conf = settings
        # Init models
        self._users = models.admin.users.Users(sql)
        self._settings = models.admin.settings.Settings(sql)

    def blueprint(self):
        # Init blueprint
        settings_blueprint = Blueprint('settings', __name__, template_folder='settings')

        @settings_blueprint.route('/admin/settings', methods=['GET','PUT'])
        @jwt_required
        def settings_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Security (Administration URL)
            if not self.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

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

        # Get current Domain URL from Security
        regex = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
        r = re.search(regex, request.url_root)
        ip = r['host'] + ':' + r['port'] if len(r['port']) > 0 else r['host']
        settings['security']['current'] = ip

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

    def check_url(self):
        security = self._settings.get(setting_name='security')
        if len(security) > 0 and json.loads(security[0]['value'])['url'] != '':
            regex = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
            # Current URL
            r = re.search(regex, request.url_root)
            current_url = r['host'] + ':' + r['port'] if len(r['port']) > 0 else r['host']
            # Administration URL
            r = re.search(regex, json.loads(security[0]['value'])['url'])
            admin_url = r['host'] + ':' + r['port'] if len(r['port']) > 0 else r['host']
            # Check URLs
            if current_url != admin_url:
                return False
        return True
