from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
import json

import connectors.base
import models.admin.users
import models.admin.inventory.inventory
import models.admin.inventory.auxiliary
import models.admin.inventory.regions
import routes.admin.settings

class Auxiliary:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._inventory = models.admin.inventory.inventory.Inventory(sql)
        self._auxiliary = models.admin.inventory.auxiliary.Auxiliary(sql)
        self._regions = models.admin.inventory.regions.Regions(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        admin_auxiliary_blueprint = Blueprint('admin_auxiliary', __name__, template_folder='admin_auxiliary')

        @admin_auxiliary_blueprint.route('/admin/inventory/auxiliary', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def admin_auxiliary_method():
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
            auxiliary = request.get_json()

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(user, auxiliary)
            elif request.method == 'PUT':
                return self.put(user, auxiliary)
            elif request.method == 'DELETE':
                return self.delete()

        @admin_auxiliary_blueprint.route('/admin/inventory/auxiliary/test', methods=['POST'])
        @jwt_required()
        def admin_auxiliary_test_method():
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
            auxiliary_json = request.get_json()

            # Get region info
            region = self._regions.get(region_id=auxiliary_json['region'])
            if len(region) == 0:
                return jsonify({'message': "Can't test the connection. Invalid region provided."}), 400

            # Build Auxiliary Data
            ssh = {'enabled': region[0]['ssh_tunnel'], 'hostname': region[0]['hostname'], 'port': region[0]['port'], 'username': region[0]['username'], 'password': region[0]['password'], 'key': region[0]['key']}
            sql = {"engine": auxiliary_json['engine'], "hostname": auxiliary_json['hostname'], "port": auxiliary_json['port'], "username": auxiliary_json['username'], "password": auxiliary_json['password']}

            # Check SQL Connection
            try:
                sql = connectors.base.Base({'ssh': ssh, 'sql': sql})
                sql.test_sql()
            except Exception as e:
                return jsonify({'message': str(e)}), 400

            return jsonify({'message': 'Connection Successful'}), 200

        return admin_auxiliary_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        group_id = request.args['group_id'] if 'group_id' in request.args else None
        return jsonify({'auxiliary': self._auxiliary.get(group_id=group_id)}), 200

    def post(self, user, auxiliary):
        # Check group & user
        if not self._inventory.exist_group(auxiliary['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not auxiliary['shared'] and not self._inventory.exist_user(auxiliary['group_id'], auxiliary['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check auxiliary exists
        if self._auxiliary.exist(auxiliary):
            return jsonify({'message': 'This auxiliary name currently exists'}), 400
        # Add auxiliary
        self._auxiliary.post(user, auxiliary)
        return jsonify({'message': 'Auxiliary connection added successfully'}), 200

    def put(self, user, auxiliary):
        # Check group & user
        if not self._inventory.exist_group(auxiliary['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not auxiliary['shared'] and not self._inventory.exist_user(auxiliary['group_id'], auxiliary['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check auxiliary exists
        if self._auxiliary.exist(auxiliary):
            return jsonify({'message': 'This auxiliary name currently exists'}), 400
        # Edit auxiliary
        self._auxiliary.put(user, auxiliary)
        return jsonify({'message': 'Auxiliary connection edited successfully'}), 200

    def delete(self):
        data = json.loads(request.args['auxiliary'])
        # Delete auxiliary
        for auxiliary in data:
            self._auxiliary.delete(auxiliary)
        return jsonify({'message': 'Selected auxiliary connections deleted successfully'}), 200
