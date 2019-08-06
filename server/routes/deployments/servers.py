import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    servers_blueprint = Blueprint('servers', __name__, template_folder='servers')

    # Init models
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
    environments = imp.load_source('environments', '{}/models/deployments/environments.py'.format(credentials['path'])).Environments(credentials)
    regions = imp.load_source('regions', '{}/models/deployments/regions.py'.format(credentials['path'])).Regions(credentials)
    servers = imp.load_source('servers', '{}/models/deployments/servers.py'.format(credentials['path'])).Servers(credentials)

    @servers_blueprint.route('/deployments/servers', methods=['GET','POST','PUT','DELETE'])
    @jwt_required
    def servers_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Get User
        user = users.get(get_jwt_identity())

        # Get Request Json
        server = request.get_json()

        if request.method == 'GET':
            return jsonify({'data': {'servers': servers.get(user[0]['group_id']), 'environments': environments.get(user[0]['group_id'])}}), 200

        elif request.method == 'POST':
            if servers.exist(user[0]['group_id'], {'environment': server['environment'], 'region': server['region'], 'name': server['name']}):
                return jsonify({'message': 'This server currently exists'}), 400
            else:
                servers.post(user[0]['group_id'], server)
                return jsonify({'message': 'Server added successfully'}), 200

        elif request.method == 'PUT':
            if not servers.exist(user[0]['group_id'], {'environment': server['environment'], 'region': server['region'], 'name': server['current_name']}):
                return jsonify({'message': 'This server does not exist'}), 400
            elif server['current_name'] != server['name'] and servers.exist(user[0]['group_id'], {'environment': server['environment'], 'region': server['region'], 'name': server['name']}):
                return jsonify({'message': 'This new server name currently exists'}), 400
            else:
                servers.put(user[0]['group_id'], server)
                return jsonify({'message': 'Server edited successfully'}), 200

        elif request.method == 'DELETE':
            servers.delete(user[0]['group_id'], server)
            return jsonify({'message': 'Selected servers deleted successfully'}), 200

    return servers_blueprint