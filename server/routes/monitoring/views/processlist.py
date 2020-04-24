from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.monitoring.monitoring

class Processlist:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._monitoring = models.monitoring.monitoring.Monitoring(sql)

    def blueprint(self):
        # Init blueprint
        monitoring_processlist_blueprint = Blueprint('monitoring_processlist', __name__, template_folder='monitoring_processlist')

        @monitoring_processlist_blueprint.route('/monitoring/processlist', methods=['GET', 'PUT', 'DELETE'])
        @jwt_required
        def monitoring_processlist_method():
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
                return self.get(user)
            elif request.method == 'PUT':
                return self.put(user, monitoring_json)
            elif request.method == 'DELETE':
                return self.delete(user)

        return monitoring_processlist_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        processlist = self._monitoring.get_processlist(user)
        return jsonify({'data': processlist}), 200

    def put(self, user, data):
        self._monitoring.put_processlist(user, data)
        return jsonify({'message': 'Servers saved'}), 200

    def delete(self, user):
        self._monitoring.deactivate_processlist(user)
        return jsonify({'message': 'Processlist deactivated'}), 200