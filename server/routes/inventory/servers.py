from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user
import json
import copy

import connectors.base
import models.admin.users
import models.inventory.regions
import models.inventory.servers

class Servers:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._regions = models.inventory.regions.Regions(sql)
        self._servers = models.inventory.servers.Servers(sql, self._license)

    def blueprint(self):
        # Init blueprint
        servers_blueprint = Blueprint('servers', __name__, template_folder='servers')

        @servers_blueprint.route('/inventory/servers', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def servers_method():
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
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user)
            elif request.method == 'PUT':
                return self.put(user)
            elif request.method == 'DELETE':
                return self.delete(user)

        @servers_blueprint.route('/inventory/servers/test', methods=['POST'])
        @jwt_required()
        def servers_test_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            server_json = request.get_json()

            # Get Region
            region = self._regions.get(user['id'], user['group_id'], server_json['region'])
            if len(region) == 0:
                return jsonify({'message': "Can't test the connection. Invalid region provided."}), 400
            region = region[0]

            # Get Server
            if type(server_json['server']) is dict:
                server = server_json['server']
                if 'id' in server_json['server']:
                    server_origin = self._servers.get(user['id'], user['group_id'], server_json['server']['id'])
                    server['ssl_client_key'] = server_origin[0]['ssl_client_key'] if server['ssl_client_key'] == '<ssl_client_key>' else server['ssl_client_key']
                    server['ssl_client_certificate'] = server_origin[0]['ssl_client_certificate'] if server['ssl_client_certificate'] == '<ssl_client_certificate>' else server['ssl_client_certificate']
                    server['ssl_ca_certificate'] = server_origin[0]['ssl_ca_certificate'] if server['ssl_ca_certificate'] == '<ssl_ca_certificate>' else server['ssl_ca_certificate']
            else:
                server_origin = self._servers.get(user['id'], user['group_id'], server_json['server'])
                if len(server_origin) == 0:
                    return jsonify({'message': "Can't test the connection. Invalid server provided."}), 400
                server = server_origin[0]

            # Check SQL Connection
            try:
                conf = {}
                conf['ssh'] = {'enabled': region['ssh_tunnel'], 'hostname': region['hostname'], 'port': region['port'], 'username': region['username'], 'password': region['password'], 'key': region['key']}
                conf['sql'] = {'engine': server['engine'], 'hostname': server['hostname'], 'port': server['port'], 'username': server['username'], 'password': server['password'], 'ssl': server['ssl'], 'ssl_client_key': server['ssl_client_key'], 'ssl_client_certificate': server['ssl_client_certificate'], 'ssl_ca_certificate': server['ssl_ca_certificate'], 'ssl_verify_ca': server['ssl_verify_ca']}
                sql = connectors.base.Base(conf)
                sql.test_sql()
            except Exception as e:
                return jsonify({'message': str(e)}), 400

            return jsonify({'message': 'Connection Successful'}), 200

        return servers_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        # Get servers
        servers = self._servers.get(user['id'], user['group_id'], request.args['server_id']) if 'server_id' in request.args else self._servers.get(user['id'], user['group_id'])
        # Protect SSL Keys
        for server in servers:
            server['ssl_client_key'] = '<ssl_client_key>' if server['ssl_client_key'] is not None else None
            server['ssl_client_certificate'] = '<ssl_client_certificate>' if server['ssl_client_certificate'] is not None else None
            server['ssl_ca_certificate'] = '<ssl_ca_certificate>' if server['ssl_ca_certificate'] is not None else None
        # Check Inventory Secured
        servers_secured = []
        for s in servers:
            if s['secured']:
                servers_secured.append({"id": s['id'], "name": s['name'], "region_id": s['region_id'], "region": s['region'], "version": s['version'], "shared": s['shared'], "secured": s['secured'], "region_shared": s['region_shared'], "region_secured": s['region_secured'], "usage": s['usage'], "active": s['active'], "ssh": s['ssh'], "ssl": s['ssl']})
            else:
                servers_secured.append(s)
        return jsonify({'data': servers_secured}), 200

    def post(self, user):
        # Get data
        server = request.get_json()
        # Check privileges
        if server['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check region authority
        if len(self._regions.get(user['id'], user['group_id'], server['region_id'])) == 0:
            return jsonify({'message': 'This region does not belong to the user'}), 400
        # Check server exists
        server2 = copy.deepcopy(server)
        if 'id' in server:
            del server2['id']
        if self._servers.exist(user['id'], user['group_id'], server2):
            return jsonify({'message': 'This server name currently exists'}), 400
        # Parse ssl
        if server['ssl'] and (server['ssl_client_key'] == '<ssl_client_key>' or server['ssl_client_certificate'] == '<ssl_client_certificate>' or server['ssl_ca_certificate'] == '<ssl_ca_certificate>'):
            origin = self._servers.get(user['id'], user['group_id'], server['id'])[0]
            server['ssl_client_key'] = origin['ssl_client_key'] if server['ssl_client_key'] == '<ssl_client_key>' else server['ssl_client_key']
            server['ssl_client_certificate'] = origin['ssl_client_certificate'] if server['ssl_client_certificate'] == '<ssl_client_certificate>' else server['ssl_client_certificate']
            server['ssl_ca_certificate'] = origin['ssl_ca_certificate'] if server['ssl_ca_certificate'] == '<ssl_ca_certificate>' else server['ssl_ca_certificate']
        # Add server
        self._servers.post(user['id'], user['group_id'], server)
        return jsonify({'message': 'Server added'}), 200

    def put(self, user):
        # Get data
        server = request.get_json()
        # Check server
        check = self._servers.get(user['id'], user['group_id'], server['id'])
        if len(check) == 0:
            return jsonify({'message': "The server does not exist in your inventory"}), 400
        # Check privileges
        if check[0]['secured'] or (server['shared'] and not user['owner']):
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check server exists
        if self._servers.exist(user['id'], user['group_id'], server):
            return jsonify({'message': 'This server name currently exists'}), 400
        # Check region authority
        if len(self._regions.get(user['id'], user['group_id'], server['region_id'])) == 0:
            return jsonify({'message': 'This region does not belong to the user'}), 400
        # Check usage
        if 'check' in server and server['check'] is True:
            origin = self._servers.get(user['id'], user['group_id'], server['id'])[0]
            exist_in_environment = self._servers.exist_in_environment(user['id'], user['group_id'], server['id'])
            exist_in_client = self._servers.exist_in_client(user['id'], user['group_id'], server['id'])
            if ('D' in origin['usage'] and 'D' not in server['usage'] and exist_in_environment) or ('C' in origin['usage'] and 'C' not in server['usage'] and exist_in_client):
                return jsonify({'message': 'This server exists in some environments or clients. Are you sure to proceed?'}), 202
        # Edit server
        self._servers.put(user['id'], user['group_id'], server)
        return jsonify({'message': 'Server edited'}), 200

    def delete(self, user):
        servers = json.loads(request.args['servers'])
        # Check privileges
        for server in servers:
            server = self._servers.get(user['id'], user['group_id'], server)
            if len(server) > 0 and server[0]['secured'] or (server[0]['shared'] and not user['owner']):
                return jsonify({'message': "Insufficient privileges"}), 401
        # Check inconsistencies
        if 'check' in request.args and json.loads(request.args['check']) is True:
            for server in servers:
                exist_in_environment = self._servers.exist_in_environment(user['id'], user['group_id'], server)
                exist_in_client = self._servers.exist_in_client(user['id'], user['group_id'], server)
                if exist_in_environment or exist_in_client:
                    return jsonify({'message': "The selected servers are included in some environments or clients. Are you sure to proceed?"}), 202
        # Delete servers
        for server in servers:    
            self._servers.delete(user['id'], user['group_id'], server)
        return jsonify({'message': 'Selected servers deleted'}), 200
