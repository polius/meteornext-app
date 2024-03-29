import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.admin.inventory.inventory
import models.admin.inventory.environments
import routes.admin.settings

class Environments:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._inventory = models.admin.inventory.inventory.Inventory(sql)
        self._environments = models.admin.inventory.environments.Environments(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(self._license, sql)

    def blueprint(self):
        # Init blueprint
        admin_environments_blueprint = Blueprint('admin_environments', __name__, template_folder='admin_environments')

        @admin_environments_blueprint.route('/admin/inventory/environments', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def admin_environments_method():
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

        @admin_environments_blueprint.route('/admin/inventory/environments/servers', methods=['GET'])
        @jwt_required()
        def admin_environment_servers_method():
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

            # Check params
            if 'group_id' not in request.args:
                return jsonify({'message': 'Missing "group_id" parameter'}), 400

            # Get environments servers
            owner_id = None if 'owner_id' not in request.args else request.args['owner_id']
            servers = self._environments.get_servers(request.args['group_id'], owner_id)
            environment_servers = self._environments.get_environment_servers(request.args['group_id'], owner_id)
            return jsonify({'servers': servers, 'environment_servers': environment_servers})

        return admin_environments_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        # Get data
        group_id = request.args['group_id'] if 'group_id' in request.args else None
        user_id = request.args['user_id'] if 'user_id' in request.args else None
        environments = self._environments.get(group_id=group_id, user_id=user_id)
        # Return request
        return jsonify({'environments': environments}), 200

    def post(self, user):
        # Get data
        environment = request.get_json()
        # Check group & user
        if not self._inventory.exist_group(environment['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not environment['shared'] and not self._inventory.exist_user(environment['group_id'], environment['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check environment exists
        if self._environments.exist(environment):
            return jsonify({'message': 'This environment name currently exists'}), 400
        # Add environment
        self._environments.post(user, environment)
        return jsonify({'message': 'Environment added'}), 200

    def put(self, user):
        # Get data
        environment = request.get_json()
        # Check group & user
        if not self._inventory.exist_group(environment['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not environment['shared'] and not self._inventory.exist_user(environment['group_id'], environment['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check environment exists
        if self._environments.exist(environment):
            return jsonify({'message': 'This environment name currently exists'}), 400
        # Edit environment
        self._environments.put(user, environment)
        return jsonify({'message': 'Environment edited'}), 200

    def delete(self):
        environments = json.loads(request.args['environments'])
        # Delete environments
        for environment in environments:
            self._environments.delete(environment)
        return jsonify({'message': 'Selected environments deleted'}), 200
