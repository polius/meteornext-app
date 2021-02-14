from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
import json

import connectors.base
import models.admin.users
import models.inventory.regions
import models.inventory.servers

class Servers:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._regions = models.inventory.regions.Regions(sql)
        self._servers = models.inventory.servers.Servers(sql)

    def blueprint(self):
        # Init blueprint
        servers_blueprint = Blueprint('servers', __name__, template_folder='servers')

        @servers_blueprint.route('/inventory/servers', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def servers_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            server = request.get_json()

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user, server)
            elif request.method == 'PUT':
                return self.put(user, server)
            elif request.method == 'DELETE':
                return self.delete(user)

        @servers_blueprint.route('/inventory/servers/test', methods=['POST'])
        @jwt_required()
        def servers_test_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            server_json = request.get_json()

            # Get Region
            region = self._regions.get(user['id'], user['group_id'], server_json['region'])
            if len(region) == 0:
                return jsonify({'message': "Can't test the connection. Invalid region provided."}), 400
            else:
                region = region[0]

            # Get Server
            if type(server_json['server']) is dict:
                server = server_json['server']
            else:
                server = self._servers.get(user['id'], user['group_id'], server_json['server'])
                if len(server) == 0:
                    return jsonify({'message': "Can't test the connection. Invalid server provided."}), 400
                else:
                    server = server[0]

            # Check SQL Connection
            try:
                conf = {}
                conf['ssh'] = {'enabled': region['ssh_tunnel'], 'hostname': region['hostname'], 'port': region['port'], 'username': region['username'], 'password': region['password'], 'key': region['key']}
                conf['sql'] = {'engine': server['engine'], 'hostname': server['hostname'], 'port': server['port'], 'username': server['username'], 'password': server['password']}
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
        servers = self._servers.get(user['id'], user['group_id'])
        if user['inventory_secured'] and not user['owner']:
            servers_secured = []
            for s in servers:
                if s['shared']:
                    servers_secured.append({"id": s['id'], "name": s['name'], "region_id": s['region_id'], "region": s['region'], "engine": s['engine'], "version": s['version'], "shared": s['shared'], "region_shared": s['region_shared'], "usage": s['usage']})
                else:
                    servers_secured.append(s)
            return jsonify({'data': servers_secured}), 200
        return jsonify({'data': servers}), 200

    def post(self, user, server):
        # Check privileges
        if server['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check server exists
        if self._servers.exist(user['id'], user['group_id'], server):
            return jsonify({'message': 'This server name currently exists'}), 400
        # Add server
        self._servers.post(user['id'], user['group_id'], server)
        return jsonify({'message': 'Server added successfully'}), 200

    def put(self, user, server):
        # Check privileges
        if server['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check server exists
        if self._servers.exist(user['id'], user['group_id'], server):
            return jsonify({'message': 'This server name currently exists'}), 400
        # Check usage
        if 'check' in server and server['check'] is True:
            origin = self._servers.get(user['id'], user['group_id'], server['id'])[0]
            exist_in_environment = self._servers.exist_in_environment(user['id'], user['group_id'], server['id'])
            exist_in_client = self._servers.exist_in_client(user['id'], user['group_id'], server['id'])
            if ('D' in origin['usage'] and 'D' not in server['usage'] and exist_in_environment) or ('C' in origin['usage'] and 'C' not in server['usage'] and exist_in_client):
                return jsonify({'message': 'This server exists in some environments or clients. Are you sure to proceed?'}), 202
        # Edit server
        self._servers.put(user['id'], user['group_id'], server)
        return jsonify({'message': 'Server edited successfully'}), 200

    def delete(self, user):
        servers = json.loads(request.args['servers'])
        # Check privileges
        for server in servers:
            server = self._servers.get(user['id'], user['group_id'], server)
            if len(server) > 0 and server[0]['shared'] and not user['owner']:
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
            self._servers.delete(user['group_id'], server)
        return jsonify({'message': 'Selected servers deleted successfully'}), 200
