from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import utils
import models.admin.users
import models.deployments.environments
import models.deployments.regions
import models.deployments.servers

class Servers:
    def __init__(self, app, sql):
        self._app = app
        # Init models
        self._users = models.admin.users.Users(sql)
        self._environments = models.deployments.environments.Environments(sql)
        self._regions = models.deployments.regions.Regions(sql)
        self._servers = models.deployments.servers.Servers(sql)

    def license(self, value):
        self._license = value

    def blueprint(self):
        # Init blueprint
        servers_blueprint = Blueprint('servers', __name__, template_folder='servers')

        @servers_blueprint.route('/deployments/servers', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def servers_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_edit']:
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

        @servers_blueprint.route('/deployments/servers/test', methods=['POST'])
        @jwt_required
        def servers_test_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            server_json = request.get_json()

            # Get Server Region
            r = self._regions.get_by_server(user['group_id'], server_json['region'])

            # Init Utils Class
            connection = r[0] if r[0]['cross_region'] else None
            u = utils.Utils(self._app, connection)

            # Check SQL Connection
            try:
                u.check_sql(server_json)
            except Exception as e:
                return jsonify({'message': "Can't connect to the Server"}), 400

            return jsonify({'message': 'Connection Successful'}), 200

        return servers_blueprint

    ####################
    # Internal Methods #
    ####################
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