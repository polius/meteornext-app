import sys
import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import utils
import models.admin.users
import models.inventory.regions
import models.inventory.servers

class Regions:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._regions = models.inventory.regions.Regions(sql)
        self._servers = models.inventory.servers.Servers(sql)

    def blueprint(self):
        # Init blueprint
        regions_blueprint = Blueprint('regions', __name__, template_folder='regions')       

        @regions_blueprint.route('/inventory/regions', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def regions_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            region_json = request.get_json()

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled'] or (request.method != 'GET' and region_json['shared'] and not user['owner']):
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user['id'], user['group_id'], user['inventory_secured'] and not user['owner'])
            elif request.method == 'POST':
                return self.post(user['id'], user['group_id'], region_json)
            elif request.method == 'PUT':
                return self.put(user['id'], user['group_id'], region_json)
            elif request.method == 'DELETE':
                return self.delete(user['group_id'])

        @regions_blueprint.route('/inventory/regions/test', methods=['POST'])
        @jwt_required
        def regions_test_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            region_json = request.get_json()

            # Get Region
            if ('region' in region_json):
                region = self._regions.get(user['id'], user['group_id'], region_json['region'])
                if len(region) == 0:
                    return jsonify({'message': "Can't test the SSH connection. Invalid region provided."}), 400
                else:
                    region = region[0]
            else:
                region = region_json

            # Check SSH Connection
            try:
                u = utils.Utils(region)
                u.check_ssh()
            except Exception as e:
                return jsonify({'message': str(e)}), 400

            return jsonify({'message': 'Connection Successful'}), 200

        return regions_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user_id, group_id, secured):
        regions = self._regions.get(user_id, group_id)
        if secured:
            regions_secured = []
            for r in regions:
                if r['shared']:
                    regions_secured.append({"id": r['id'], "name": r['name'], "ssh_tunnel": r['ssh_tunnel'], "shared": r['shared']})
                else:
                    regions_secured.append(r)
            return jsonify({'data': regions_secured}), 200
        return jsonify({'data': regions}), 200

    def post(self, user_id, group_id, data):
        if self._regions.exist(user_id, group_id, data):
            return jsonify({'message': 'This region currently exists'}), 400

        # Create new Region
        self._regions.post(user_id, group_id, data)
        return jsonify({'message': 'Region added successfully'}), 200

    def put(self, user_id, group_id, data):
        if self._regions.exist(user_id, group_id, data):
            return jsonify({'message': 'This new region name currently exists'}), 400

        # Edit Region
        self._regions.put(user_id, group_id, data)
        return jsonify({'message': 'Region edited successfully'}), 200

    def delete(self, group_id):
        data = json.loads(request.args['regions'])
        # Check inconsistencies
        for region in data:
            if self._servers.exist_by_region(group_id, region):
                return jsonify({'message': "The selected regions have servers"}), 400

        for region in data:
            self._regions.delete(group_id, region)
        return jsonify({'message': 'Selected regions deleted successfully'}), 200

    def remove(self, group_id):
        self._regions.remove(group_id)