from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.monitoring.monitoring

class Parameters:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._monitoring = models.monitoring.monitoring.Monitoring(sql, self._license)

    def blueprint(self):
        # Init blueprint
        monitoring_parameters_blueprint = Blueprint('monitoring_parameters', __name__, template_folder='monitoring_parameters')

        @monitoring_parameters_blueprint.route('/monitoring/parameters', methods=['GET', 'PUT'])
        @jwt_required()
        def monitoring_parameters_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['monitoring_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'PUT':
                return self.put(user)

        return monitoring_parameters_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        parameters = self._monitoring.get_parameters(user)
        return jsonify({'data': parameters}), 200

    def put(self, user):
        self._monitoring.put_parameters(user, request.get_json())
        return jsonify({'message': 'Servers saved'}), 200
