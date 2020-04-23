from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.monitoring.monitoring
import models.monitoring.monitoring_settings

class Monitoring:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._monitoring = models.monitoring.monitoring.Monitoring(sql)
        self._monitoring_settings = models.monitoring.monitoring_settings.Monitoring_Settings(sql)

    def blueprint(self):
        # Init blueprint
        monitoring_blueprint = Blueprint('monitoring', __name__, template_folder='monitoring')

        @monitoring_blueprint.route('/monitoring', methods=['GET', 'PUT'])
        @jwt_required
        def monitoring_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            monitoring_json = request.get_json()

            # Check user privileges
            if not user['monitoring_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user['group_id'])
            elif request.method == 'PUT':
                return self.put(user['group_id'], monitoring_json)

        @monitoring_blueprint.route('/monitoring/settings', methods=['PUT'])
        @jwt_required
        def monitoring_settings_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['monitoring_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            monitoring_json = request.get_json()

            # Update servers list
            self._monitoring_settings.put(user, monitoring_json)
            return jsonify({'message': 'Settings saved'}), 200

        return monitoring_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id):
        server_id = request.args['server_id'] if 'server_id' in request.args else None
        if server_id:
            return jsonify({'data': self._monitoring.get(group_id, server_id)}), 200
        else:
            servers = self._monitoring.get_servers(group_id)
            settings = self._monitoring_settings.get(group_id)
            return jsonify({'servers': servers, 'settings': settings}), 200

    def put(self, group_id, data):
        self._monitoring.put(user['group_id'], data)
        return jsonify({'message': 'Servers saved'}), 200