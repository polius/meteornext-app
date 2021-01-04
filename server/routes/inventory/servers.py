from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import json
import utils
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
        @jwt_required
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
        @jwt_required
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

            # Init Utils Class
            connection = region if region['ssh_tunnel'] else None
            u = utils.Utils(connection)

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
                u.check_sql(server)
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
                    servers_secured.append({"id": s['id'], "name": s['name'], "region": s['region'], "engine": s['engine'], "version": s['version'], "shared": s['shared'], "region_shared": s['region_shared']})
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
            return jsonify({'message': 'This server currently exists'}), 400
        # Add server
        self._servers.post(user['id'], user['group_id'], server)
        return jsonify({'message': 'Server added successfully'}), 200

    def put(self, user, server):
        # Check privileges
        if server['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check server exists
        if self._servers.exist(user['id'], user['group_id'], server):
            return jsonify({'message': 'This new server name currently exists'}), 400
        # Edit server
        self._servers.put(user['id'], user['group_id'], server)
        return jsonify({'message': 'Server edited successfully'}), 200

    def delete(self, user):
        servers = json.loads(request.args['servers'])
        # Check inconsistencies
        for server in servers:
            if self._servers.exist_in_environment(user['group_id'], server):
                return jsonify({'message': "The server '{}' is included in the environment '{}'".format(exist[0]['server_name'], exist[0]['environment_name'])}), 400
        # Check privileges
        for server in servers:
            server = self._servers.get(user['id'], user['group_id'], server)
            if len(server) > 0 and server[0]['shared'] and not user['owner']:
                return jsonify({'message': "Insufficient privileges"}), 401
        # Delete servers
        for server in servers:    
            self._servers.delete(user['group_id'], server)
        return jsonify({'message': 'Selected servers deleted successfully'}), 200

    def remove(self, group_id):
        self._servers.remove(group_id)
