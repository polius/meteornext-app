import sys
import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import connectors.base
import models.admin.users
import models.admin.inventory.inventory
import models.admin.inventory.regions
import models.admin.inventory.servers
import routes.admin.settings

class Regions:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._inventory = models.admin.inventory.inventory.Inventory(sql)
        self._regions = models.admin.inventory.regions.Regions(sql)
        self._servers = models.admin.inventory.servers.Servers(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        admin_regions_blueprint = Blueprint('admin_regions', __name__, template_folder='admin_regions')       

        @admin_regions_blueprint.route('/admin/inventory/regions', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def admin_regions_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            region = request.get_json()

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(user, region)
            elif request.method == 'PUT':
                return self.put(user, region)
            elif request.method == 'DELETE':
                return self.delete()

        @admin_regions_blueprint.route('/admin/inventory/regions/test', methods=['POST'])
        @jwt_required
        def admin_regions_test_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            region_json = request.get_json()

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
        group_id = request.args['group_id'] if 'group_id' in request.args else None
        return jsonify({'regions': self._regions.get(group_id=group_id)}), 200

    def post(self, user, region):
        # Check group & user
        if not self._inventory.exist_group(region['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not region['shared'] and not self._inventory.exist_user(region['group_id'], region['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check region exists
        if self._regions.exist(region):
            return jsonify({'message': 'This region name currently exists'}), 400
        # Add region
        self._regions.post(user, region)
        return jsonify({'message': 'Region added successfully'}), 200

    def put(self, user, region):
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
        return jsonify({'message': 'Region edited successfully'}), 200

    def delete(self):
        regions = json.loads(request.args['regions'])
        # Check inconsistencies
        for region in regions:
            if self._servers.exist_by_region(region):
                return jsonify({'message': "The selected regions have servers"}), 400
        # Delete regions
        for region in regions:
            self._regions.delete(region)
        return jsonify({'message': 'Selected regions deleted successfully'}), 200
