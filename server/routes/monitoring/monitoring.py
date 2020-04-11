from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.monitoring.monitoring

class Monitoring:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._monitoring = models.monitoring.monitoring.Monitoring(sql)

    def blueprint(self):
        # Init blueprint
        monitoring_blueprint = Blueprint('monitoring', __name__, template_folder='monitoring')

        @monitoring_blueprint.route('/monitoring/monitoring', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def monitoring_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            monitoring_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['group_id'])
            elif request.method == 'POST':
                return self.post(user['id'], user['group_id'], monitoring_json)
            elif request.method == 'PUT':
                return self.put(user['id'], user['group_id'], monitoring_json)

        return monitoring_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id):
        return jsonify({'data': self._monitoring.get(group_id)}), 200

    def post(self, user_id, group_id, data):
        self._monitoring.post(user_id, group_id, data)
        return jsonify({'message': 'Monitoring configuration added successfully'}), 200

    def put(self, user_id, group_id, data):
        self._monitoring.put(user_id, group_id, data)
        return jsonify({'message': 'Monitoring configuration edited successfully'}), 200
