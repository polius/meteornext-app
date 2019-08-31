import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Servers:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._environments = imp.load_source('environments', '{}/models/deployments/environments.py'.format(credentials['path'])).Environments(credentials)
        self._servers = imp.load_source('servers', '{}/models/deployments/servers.py'.format(credentials['path'])).Servers(credentials)

    def blueprint(self):
        # Init blueprint
        servers_blueprint = Blueprint('servers', __name__, template_folder='servers')

        @servers_blueprint.route('/deployments/servers', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def servers_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            server_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['group_id'])
            elif request.method == 'POST':
                return self.post(user['group_id'], server_json)
            elif request.method == 'PUT':
                return self.put(user['group_id'], server_json)
            elif request.method == 'DELETE':
                return self.delete(user['group_id'], server_json)

        return servers_blueprint

    def get(self, group_id):
        return jsonify({'data': {'servers': self._servers.get(group_id), 'environments': self._environments.get(group_id)}}), 200

    def post(self, group_id, data):
        if self._servers.exist(group_id, data):
            return jsonify({'message': 'This server currently exists'}), 400
        else:
            self._servers.post(group_id, data)
            return jsonify({'message': 'Server added successfully'}), 200

    def put(self, group_id, data):
        if self._servers.exist(group_id, data):
            return jsonify({'message': 'This new server name currently exists'}), 400
        else:
            self._servers.put(group_id, data)
            return jsonify({'message': 'Server edited successfully'}), 200

    def delete(self, group_id, data):
        for server in data:
            self._servers.delete(group_id, server)
        return jsonify({'message': 'Selected servers deleted successfully'}), 200

    def remove(self, group_id):
        self._servers.remove(group_id)