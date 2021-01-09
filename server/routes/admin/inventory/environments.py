import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.deployments
import models.admin.inventory.inventory
import models.admin.inventory.environments
import routes.admin.settings

class Environments:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._deployments = models.deployments.deployments.Deployments(sql)
        self._inventory = models.admin.inventory.inventory.Inventory(sql)
        self._environments = models.admin.inventory.environments.Environments(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        admin_environments_blueprint = Blueprint('admin_environments', __name__, template_folder='admin_environments')

        @admin_environments_blueprint.route('/admin/inventory/environments', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def admin_environments_method():
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
            environment = request.get_json()

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(user, environment)
            elif request.method == 'PUT':
                return self.put(user, environment)
            elif request.method == 'DELETE':
                return self.delete()

        @admin_environments_blueprint.route('/admin/inventory/environments/servers', methods=['GET'])
        @jwt_required
        def admin_environments_list_method():
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

            # Check params
            if 'group' not in request.args:
                return jsonify({'message': 'Missing "group" parameter'}), 400

            # Get environments servers
            return jsonify({'servers': self._environments.get_servers(request.args['group']), 'environment_servers': self._environments.get_environment_servers(request.args['group'])})

        return admin_environments_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        group_id = request.args['group_id'] if 'group_id' in request.args else None
        return jsonify({'environments': self._environments.get(group_id)}), 200

    def post(self, user, environment):
        # Check group & user
        if not self._inventory.exist_group(environment['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not environment['shared'] and not self._inventory.exist_user(environment['group_id'], environment['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check environment exists
        if self._environments.exist(environment):
            return jsonify({'message': 'This environment currently exists'}), 400
        # Add environment
        self._environments.post(user, environment)
        return jsonify({'message': 'Environment added successfully'}), 200

    def put(self, user, environment):
        # Check group & user
        if not self._inventory.exist_group(environment['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not environment['shared'] and not self._inventory.exist_user(environment['group_id'], environment['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check environment exists
        if self._environments.exist(environment):
            return jsonify({'message': 'This new environment currently exists'}), 400
        # Edit environment
        self._environments.put(user, environment)
        return jsonify({'message': 'Environment edited successfully'}), 200

    def delete(self):
        environments = json.loads(request.args['environments'])
        # Check inconsistencies
        exist = True
        for environment in environments:
            exist &= not self._deployments.existByEnvironment(environment)
        if not exist:
            return jsonify({'message': "The selected environments have related deployments"}), 400
        # Delete environments
        for environment in environments:
            self._environments.delete(environment)
        return jsonify({'message': 'Selected environments deleted successfully'}), 200
