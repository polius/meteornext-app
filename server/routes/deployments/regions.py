import imp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Regions:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._environments = imp.load_source('environments', '{}/models/deployments/environments.py'.format(credentials['path'])).Environments(credentials)
        self._regions = imp.load_source('regions', '{}/models/deployments/regions.py'.format(credentials['path'])).Regions(credentials)
        self._servers = imp.load_source('servers', '{}/models/deployments/servers.py'.format(credentials['path'])).Servers(credentials)

    def blueprint(self):
        # Init blueprint
        regions_blueprint = Blueprint('regions', __name__, template_folder='regions')       

        @regions_blueprint.route('/deployments/regions', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def regions_method():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User Group ID
            group_id = self._users.get(get_jwt_identity())[0]['group_id']

            # Get Request Json
            region_json = request.get_json()

            if request.method == 'GET':
                return self.get(group_id)
            elif request.method == 'POST':
                return self.post(group_id, region_json)
            elif request.method == 'PUT':
                return self.put(group_id, region_json)
            elif request.method == 'DELETE':
                return self.delete(group_id, region_json)

        @regions_blueprint.route('/deployments/regions/list', methods=['POST'])
        @jwt_required
        def regions_list_method():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User
            user = self._users.get(get_jwt_identity())

            # Get Request Json
            data = request.get_json()

            # Return Regions By User Environment
            return jsonify({'data': self._regions.get_by_environment(user[0]['group_id'], data)}), 200

        return regions_blueprint

    def get(self, group_id):
        return jsonify({'data': {'regions': self._regions.get(group_id), 'environments': self._environments.get(group_id)}}), 200

    def post(self, group_id, data):
        if self._regions.exist(group_id, data):
            return jsonify({'message': 'This region currently exists'}), 400
        else:
            self._regions.post(group_id, data)
            return jsonify({'message': 'Region added successfully'}), 200

    def put(self, group_id, data):
        if self._regions.exist(group_id, data):
            return jsonify({'message': 'This new region name currently exists'}), 400
        else:
            self._regions.put(group_id, data)
            return jsonify({'message': 'Region edited successfully'}), 200

    def delete(self, group_id, data):
        # Check inconsistencies
        for region in data:
            if self._servers.exist_by_region(group_id, region):
                return jsonify({'message': "The region '" + region['name'] + "' has attached servers"}), 400

        for region in data:
            self._regions.delete(group_id, region)
        return jsonify({'message': 'Selected regions deleted successfully'}), 200

    def remove(self, group_id):
        self._regions.remove(group_id)