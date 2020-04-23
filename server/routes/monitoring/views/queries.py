from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.monitoring.monitoring

class Queries:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._monitoring = models.monitoring.monitoring.Monitoring(sql)

    def blueprint(self):
        # Init blueprint
        monitoring_queries_blueprint = Blueprint('monitoring_queries', __name__, template_folder='monitoring_queries')

        @monitoring_queries_blueprint.route('/monitoring/queries', methods=['GET', 'PUT'])
        @jwt_required
        def monitoring_queries_method():
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

        return monitoring_queries_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id):
        servers = self._monitoring.get_servers(group_id)
        return jsonify({'servers': servers, 'settings': settings}), 200

    def put(self, group_id, data):
        self._monitoring.put(user['group_id'], data)
        return jsonify({'message': 'Servers saved'}), 200