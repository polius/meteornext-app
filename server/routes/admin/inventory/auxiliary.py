from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user
import json
import copy

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
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username']})
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
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            auxiliary_json = request.get_json()

            # Get region info
            region = self._regions.get(region_id=auxiliary_json['region'])
            if len(region) == 0:
                return jsonify({'message': "Can't test the connection. Invalid region provided."}), 400

            # Get auxiliary
            auxiliary = auxiliary_json
            if 'id' in auxiliary:
                auxiliary_origin = self._auxiliary.get(auxiliary_id=auxiliary['id'])
                auxiliary['ssl_client_key'] = auxiliary_origin[0]['ssl_client_key'] if auxiliary['ssl_client_key'] == '<ssl_client_key>' else auxiliary['ssl_client_key']
                auxiliary['ssl_client_certificate'] = auxiliary_origin[0]['ssl_client_certificate'] if auxiliary['ssl_client_certificate'] == '<ssl_client_certificate>' else auxiliary['ssl_client_certificate']
                auxiliary['ssl_ca_certificate'] = auxiliary_origin[0]['ssl_ca_certificate'] if auxiliary['ssl_ca_certificate'] == '<ssl_ca_certificate>' else auxiliary['ssl_ca_certificate']

            # Build Auxiliary Data
            ssh = {'enabled': region[0]['ssh_tunnel'], 'hostname': region[0]['hostname'], 'port': region[0]['port'], 'username': region[0]['username'], 'password': region[0]['password'], 'key': region[0]['key']}
            sql = {"engine": auxiliary['engine'], "hostname": auxiliary['hostname'], "port": auxiliary['port'], "username": auxiliary['username'], "password": auxiliary['password'], "ssl": auxiliary['ssl'], "ssl_client_key": auxiliary['ssl_client_key'], "ssl_client_certificate": auxiliary['ssl_client_certificate'], "ssl_ca_certificate": auxiliary['ssl_ca_certificate'], "ssl_verify_ca": auxiliary['ssl_verify_ca']}

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
        # Get args
        user_id = request.args['user_id'] if 'user_id' in request.args else None
        group_id = request.args['group_id'] if 'group_id' in request.args else None
        # Get auxiliary
        auxiliary = self._auxiliary.get(group_id=group_id, user_id=user_id)
        # Protect SSL Keys
        for aux in auxiliary:
            aux['ssl_client_key'] = '<ssl_client_key>' if aux['ssl_client_key'] is not None else None
            aux['ssl_client_certificate'] = '<ssl_client_certificate>' if aux['ssl_client_certificate'] is not None else None
            aux['ssl_ca_certificate'] = '<ssl_ca_certificate>' if aux['ssl_ca_certificate'] is not None else None
        # Return data
        return jsonify({'auxiliary': auxiliary}), 200

    def post(self, user):
        # Get data
        auxiliary = request.get_json()
        # Check group & user
        if not self._inventory.exist_group(auxiliary['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not auxiliary['shared'] and not self._inventory.exist_user(auxiliary['group_id'], auxiliary['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check auxiliary exists
        auxiliary2 = copy.deepcopy(auxiliary)
        if 'id' in auxiliary2:
            del auxiliary2['id']
        if self._auxiliary.exist(auxiliary2):
            return jsonify({'message': 'This auxiliary name currently exists'}), 400
        # Add auxiliary
        self._auxiliary.post(user, auxiliary)
        return jsonify({'message': 'Auxiliary connection added'}), 200

    def put(self, user):
        # Get data
        auxiliary = request.get_json()
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
        return jsonify({'message': 'Auxiliary connection edited'}), 200

    def delete(self):
        data = json.loads(request.args['auxiliary'])
        # Delete auxiliary
        for auxiliary in data:
            self._auxiliary.delete(auxiliary)
        return jsonify({'message': 'Selected auxiliary connections deleted'}), 200
