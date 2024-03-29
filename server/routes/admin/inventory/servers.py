from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user
import json
import copy

import connectors.base
import models.admin.users
import models.admin.inventory.inventory
import models.admin.inventory.regions
import models.admin.inventory.servers
import routes.admin.settings

class Servers:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._inventory = models.admin.inventory.inventory.Inventory(sql)
        self._regions = models.admin.inventory.regions.Regions(sql)
        self._servers = models.admin.inventory.servers.Servers(sql, self._license)
        # Init routes
        self._settings = routes.admin.settings.Settings(self._license, sql)

    def blueprint(self):
        # Init blueprint
        admin_servers_blueprint = Blueprint('admin_servers', __name__, template_folder='admin_servers')

        @admin_servers_blueprint.route('/admin/inventory/servers', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def admin_servers_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(user)
            elif request.method == 'PUT':
                return self.put(user)
            elif request.method == 'DELETE':
                return self.delete()

        @admin_servers_blueprint.route('/admin/inventory/servers/test', methods=['POST'])
        @jwt_required()
        def admin_servers_test_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            server_json = request.get_json()

            # Get Region
            region = self._regions.get(region_id=server_json['region_id'])
            if len(region) == 0:
                return jsonify({'message': "Can't test the connection. Invalid region provided."}), 400
            else:
                region = region[0]

            # Get server
            server = server_json['server']
            if 'id' in server:
                server_origin = self._servers.get(server_id=server['id'])
                server['ssl_client_key'] = server_origin[0]['ssl_client_key'] if server['ssl_client_key'] == '<ssl_client_key>' else server['ssl_client_key']
                server['ssl_client_certificate'] = server_origin[0]['ssl_client_certificate'] if server['ssl_client_certificate'] == '<ssl_client_certificate>' else server['ssl_client_certificate']
                server['ssl_ca_certificate'] = server_origin[0]['ssl_ca_certificate'] if server['ssl_ca_certificate'] == '<ssl_ca_certificate>' else server['ssl_ca_certificate']

            # Check SQL Connection
            try:
                conf = {}
                conf['ssh'] = {'enabled': region['ssh_tunnel'], 'hostname': region['hostname'], 'port': region['port'], 'username': region['username'], 'password': region['password'], 'key': region['key']}
                conf['sql'] = server
                sql = connectors.base.Base(conf)
                sql.test_sql()
            except Exception as e:
                return jsonify({'message': str(e)}), 400

            return jsonify({'message': 'Connection Successful'}), 200

        return admin_servers_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        # Get args
        group_id = request.args['group_id'] if 'group_id' in request.args else None
        server_id = request.args['server_id'] if 'server_id' in request.args else None
        user_id = request.args['user_id'] if 'user_id' in request.args else None
        # Get servers
        servers = self._servers.get(group_id=group_id, server_id=server_id, user_id=user_id)
        # Protect SSL Keys
        for server in servers:
            server['ssl_client_key'] = '<ssl_client_key>' if server['ssl_client_key'] is not None else None
            server['ssl_client_certificate'] = '<ssl_client_certificate>' if server['ssl_client_certificate'] is not None else None
            server['ssl_ca_certificate'] = '<ssl_ca_certificate>' if server['ssl_ca_certificate'] is not None else None
        # Return data
        return jsonify({'servers': servers}), 200

    def post(self, user):
        # Get data
        server = request.get_json()
        # Check group & user
        if not self._inventory.exist_group(server['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not server['shared'] and not self._inventory.exist_user(server['group_id'], server['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check server exists
        server2 = copy.deepcopy(server)
        if 'id' in server:
            del server2['id']
        if self._servers.exist(server2):
            return jsonify({'message': 'This server name currently exists'}), 400
        # Parse ssl
        if server['ssl'] and (server['ssl_client_key'] == '<ssl_client_key>' or server['ssl_client_certificate'] == '<ssl_client_certificate>' or server['ssl_ca_certificate'] == '<ssl_ca_certificate>'):
            origin = self._servers.get(server_id=server['id'])[0]
            server['ssl_client_key'] = origin['ssl_client_key'] if server['ssl_client_key'] == '<ssl_client_key>' else server['ssl_client_key']
            server['ssl_client_certificate'] = origin['ssl_client_certificate'] if server['ssl_client_certificate'] == '<ssl_client_certificate>' else server['ssl_client_certificate']
            server['ssl_ca_certificate'] = origin['ssl_ca_certificate'] if server['ssl_ca_certificate'] == '<ssl_ca_certificate>' else server['ssl_ca_certificate']
        # Add server
        self._servers.post(user, server)
        return jsonify({'message': 'Server added'}), 200

    def put(self, user):
        # Get data
        server = request.get_json()
        # Check group & user
        if not self._inventory.exist_group(server['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not server['shared'] and not self._inventory.exist_user(server['group_id'], server['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check server exists
        if self._servers.exist(server):
            return jsonify({'message': 'This server name currently exists'}), 400
        # Check usage
        if 'check' in server and server['check'] is True:
            origin = self._servers.get(server_id=server['id'])[0]
            exist_in_environment = self._servers.exist_in_environment(server['id'])
            exist_in_client = self._servers.exist_in_client(server['id'])
            if ('D' in origin['usage'] and 'D' not in server['usage'] and exist_in_environment) or ('C' in origin['usage'] and 'C' not in server['usage'] and exist_in_client):
                return jsonify({'message': 'This server exists in some environments or clients. Are you sure to proceed?'}), 202
        # Edit server
        self._servers.put(user, server)
        return jsonify({'message': 'Server edited'}), 200

    def delete(self):
        servers = json.loads(request.args['servers'])
        # Check inconsistencies
        if 'check' in request.args and json.loads(request.args['check']) is True:
            for server in servers:
                exist_in_environment = self._servers.exist_in_environment(server)
                exist_in_client = self._servers.exist_in_client(server)
                if exist_in_environment or exist_in_client:
                    return jsonify({'message': "The selected servers are included in some environments or clients. Are you sure to proceed?"}), 202
        # Delete servers
        for server in servers:
            self._servers.delete(server)
        return jsonify({'message': 'Selected servers deleted'}), 200
