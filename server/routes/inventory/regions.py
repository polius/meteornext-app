import sys
import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import connectors.base
import models.admin.users
import models.inventory.regions

class Regions:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._regions = models.inventory.regions.Regions(sql)

    def blueprint(self):
        # Init blueprint
        regions_blueprint = Blueprint('regions', __name__, template_folder='regions')       

        @regions_blueprint.route('/inventory/regions', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def regions_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            region = request.get_json()

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user, region)
            elif request.method == 'PUT':
                return self.put(user, region)
            elif request.method == 'DELETE':
                return self.delete(user)

        @regions_blueprint.route('/inventory/regions/test', methods=['POST'])
        @jwt_required()
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
            if 'region' in region_json:
                region = self._regions.get(user['id'], user['group_id'], region_json['region'])
                if len(region) == 0:
                    return jsonify({'message': "Can't test the SSH connection. Invalid region provided."}), 400
                region = region[0]
            else:
                region = region_json
                if 'id' in region:
                    region_origin = self._regions.get(user['id'], user['group_id'], region['id'])
                    region['key'] = region_origin[0]['key'] if region['key'] == '<ssh_key>' else region['key']

            # Check SSH Connection
            try:
                sql = connectors.base.Base({'ssh': region, 'sql': {'engine': 'MySQL'}})
                sql.test_ssh()
            except Exception as e:
                return jsonify({'message': str(e)}), 400

            return jsonify({'message': 'Connection Successful'}), 200

        return regions_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        regions = self._regions.get(user['id'], user['group_id'])
        # Protect SSH Private Key
        for region in regions:
            region['key'] = '<ssh_key>' if region['key'] is not None else None
        # Check Inventory Secured
        if user['inventory_secured'] and not user['owner']:
            regions_secured = []
            for r in regions:
                if r['shared']:
                    regions_secured.append({"id": r['id'], "name": r['name'], "ssh_tunnel": r['ssh_tunnel'], "key": r['key'], "shared": r['shared']})
                else:
                    regions_secured.append(r)
            return jsonify({'data': regions_secured}), 200
        return jsonify({'data': regions}), 200

    def post(self, user, region):
        # Check privileges
        if region['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check region exists
        if self._regions.exist(user['id'], user['group_id'], region):
            return jsonify({'message': 'This region name currently exists'}), 400
        # Parse private key
        if region['ssh_tunnel'] and region['key'] == '<ssh_key>':
            origin = self._regions.get(user['id'], user['group_id'], region['id'])[0]
            region['key'] = origin['key'] if region['key'] == '<ssh_key>' else region['key']
        # Add region
        self._regions.post(user['id'], user['group_id'], region)
        return jsonify({'message': 'Region added successfully'}), 200

    def put(self, user, region):
        # Check privileges
        if region['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check region exists
        if self._regions.exist(user['id'], user['group_id'], region):
            return jsonify({'message': 'This region name currently exists'}), 400
        # Edit region
        self._regions.put(user['id'], user['group_id'], region)
        return jsonify({'message': 'Region edited successfully'}), 200

    def delete(self, user):
        regions = json.loads(request.args['regions'])
        # Check inconsistencies
        for region in regions:
            if self._regions.exist_in_server(user['id'], user['group_id'], region):
                return jsonify({'message': "The selected regions have servers"}), 400
        # Check privileges
        for region in regions:
            region = self._regions.get(user['id'], user['group_id'], region)
            if len(region) > 0 and region[0]['shared'] and not user['owner']:
                return jsonify({'message': "Insufficient privileges"}), 401
        # Delete regions
        for region in regions:
            self._regions.delete(user['id'], user['group_id'], region)
        return jsonify({'message': 'Selected regions deleted successfully'}), 200
