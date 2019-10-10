import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Logs:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._logs = imp.load_source('logs', '{}/models/deployments/logs.py'.format(credentials['path'])).Logs(credentials)

    def blueprint(self):
        # Init blueprint
        logs_blueprint = Blueprint('logs', __name__, template_folder='logs')

        @logs_blueprint.route('/deployments/logs', methods=['GET','PUT'])
        @jwt_required
        def logs_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            logs_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['group_id'])
            elif request.method == 'PUT':
                return self.put(user['group_id'], logs_json)

        return logs_blueprint

    def get(self, group_id):
        return jsonify({'data': self._logs.get(group_id)}), 200

    def put(self, group_id, data):
        if not self._logs.exist(group_id):
            self._logs.post(group_id, data)
        else:
            self._logs.put(group_id, data)
        return jsonify({'message': 'Changes saved successfully'}), 200

    def delete(self, group_id):
        self._logs.delete(group_id)