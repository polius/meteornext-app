import sys
import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import connectors.base
import models.admin.users
import models.admin.inventory.inventory
import models.admin.inventory.regions
import routes.admin.settings

class Regions:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._inventory = models.admin.inventory.inventory.Inventory(sql)
        self._regions = models.admin.inventory.regions.Regions(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(self._license, sql)

    def blueprint(self):
        # Init blueprint
        admin_regions_blueprint = Blueprint('admin_regions', __name__, template_folder='admin_regions')       

        @admin_regions_blueprint.route('/admin/inventory/regions', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def admin_regions_method():
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

        @admin_regions_blueprint.route('/admin/inventory/regions/test', methods=['POST'])
        @jwt_required()
        def admin_regions_test_method():
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
            region_json = request.get_json()
            if 'id' in region_json:
                region_origin = self._regions.get(region_id=region_json['id'])
                region_json['key'] = region_origin[0]['key'] if region_json['key'] == '<ssh_key>' else region_json['key']

            # Check SSH Connection
            try:
                sql = connectors.base.Base({'ssh': region_json, 'sql': {'engine': 'MySQL'}})
                sql.test_ssh()
            except Exception as e:
                return jsonify({'message': str(e)}), 400

            return jsonify({'message': 'Connection Successful'}), 200

        return admin_regions_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        # Get args
        region_id = request.args['id'] if 'id' in request.args else None
        group_id = request.args['group_id'] if 'group_id' in request.args else None
        owner_id = request.args['owner_id'] if 'owner_id' in request.args else None
        user_id = request.args['user_id'] if 'user_id' in request.args else None
        # Get regions
        regions = self._regions.get(group_id=group_id, owner_id=owner_id, region_id=region_id, user_id=user_id)
        # Protect SSH Private Key
        for region in regions:
            region['key'] = '<ssh_key>' if region['key'] is not None else None
        # Return data
        return jsonify({'regions': regions}), 200

    def post(self, user):
        # Get data
        region = request.get_json()
        # Check group & user
        if not self._inventory.exist_group(region['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not region['shared'] and not self._inventory.exist_user(region['group_id'], region['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check region exists
        if self._regions.exist(region):
            return jsonify({'message': 'This region name currently exists'}), 400
        # Parse private key
        if region['ssh_tunnel'] and region['key'] == '<ssh_key>':
            origin = self._regions.get(region_id=region['id'])[0]
            region['key'] = origin['key'] if region['key'] == '<ssh_key>' else region['key']
        # Add region
        self._regions.post(user, region)
        return jsonify({'message': 'Region added'}), 200

    def put(self, user):
        # Get data
        region = request.get_json()
        # Check group & user
        if not self._inventory.exist_group(region['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not region['shared'] and not self._inventory.exist_user(region['group_id'], region['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check region exists
        if self._regions.exist(region):
            return jsonify({'message': 'This region name currently exists'}), 400
        # Edit region
        self._regions.put(user, region)
        return jsonify({'message': 'Region edited'}), 200

    def delete(self):
        regions = json.loads(request.args['regions'])
        # Check inconsistencies
        for region in regions:
            if self._regions.exist_in_server(region):
                return jsonify({'message': "The selected regions have servers"}), 400
        # Delete regions
        for region in regions:
            self._regions.delete(region)
        return jsonify({'message': 'Selected regions deleted'}), 200
