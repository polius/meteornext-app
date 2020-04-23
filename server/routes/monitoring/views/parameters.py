from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.monitoring.monitoring

class Parameters:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._monitoring = models.monitoring.monitoring.Monitoring(sql)

    def blueprint(self):
        # Init blueprint
        monitoring_parameters_blueprint = Blueprint('monitoring_parameters', __name__, template_folder='monitoring_parameters')

        @monitoring_parameters_blueprint.route('/monitoring/parameters', methods=['GET', 'PUT'])
        @jwt_required
        def monitoring_parameters_method():
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

        return monitoring_parameters_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id):
        parameters = self._monitoring.get_parameters(group_id)
        return jsonify({'data': parameters}), 200

    def put(self, group_id, data):
        self._monitoring.put_parameters(group_id, data)
        return jsonify({'message': 'Servers saved'}), 200