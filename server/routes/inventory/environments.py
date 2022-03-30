import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.inventory.environments
import models.inventory.regions

class Environments:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._environments = models.inventory.environments.Environments(sql, license)
        self._regions = models.inventory.regions.Regions(sql)

    def blueprint(self):
        # Init blueprint
        environments_blueprint = Blueprint('environments', __name__, template_folder='environments')

        @environments_blueprint.route('/inventory/environments', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def environments_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user)
            elif request.method == 'PUT':
                return self.put(user)
            elif request.method == 'DELETE':
                return self.delete(user)

        @environments_blueprint.route('/inventory/environments/list', methods=['GET'])
        @jwt_required()
        def environments_list_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled'] and request.method != 'GET':
                return jsonify({'message': 'Insufficient Privileges'}), 401
            
            # Get environments list
            return jsonify({'data': self._environments.get(user['id'], user['group_id'])})

        return environments_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        # Get data
        environments = self._environments.get(user['id'], user['group_id'])
        environment_servers = self._environments.get_environment_servers(user['id'], user['group_id'])
        servers = self._environments.get_servers(user['id'], user['group_id'])
        # Return request
        return jsonify({'environments': environments, 'environment_servers': environment_servers, 'servers': servers}), 200

    def post(self, user):
        # Get data
        environment = request.get_json()
        # Check privileges
        if environment['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check environment exists
        if self._environments.exist(user['id'], user['group_id'], environment):
            return jsonify({'message': 'This environment name currently exists'}), 400
        # Check Shared environment doesn't have a personal server
        if environment['shared'] == 1 and not self._environments.valid(user['id'], environment):
            return jsonify({'message': 'Shared environments cannot contain personal servers'}), 400
        # Add environment
        self._environments.post(user['id'], user['group_id'], environment)
        return jsonify({'message': 'Environment added'}), 200

    def put(self, user):
        # Get data
        environment = request.get_json()
        # Check environment
        check = self._environments.get(user['id'], user['group_id'], environment['id'])
        if len(check) == 0:
            return jsonify({'message': "The environment does not exist in your inventory"}), 400
        # Check privileges
        if check[0]['secured'] or (environment['shared'] and not user['owner']):
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check environment exists
        if self._environments.exist(user['id'], user['group_id'], environment):
            return jsonify({'message': 'This environment name currently exists'}), 400
        # Check Shared environment doesn't have a personal server
        if environment['shared'] == 1 and not self._environments.valid(user['id'], environment):
            return jsonify({'message': 'Shared environments cannot contain personal servers'}), 400
        # Edit environment
        self._environments.put(user['id'], user['group_id'], environment)
        return jsonify({'message': 'Environment edited'}), 200

    def delete(self, user):
        environments = json.loads(request.args['environments'])
        # Check privileges
        for environment in environments:
            environment = self._environments.get(user['id'], user['group_id'], environment)
            if len(environment) > 0 and environment[0]['secured'] or (environment[0]['shared'] and not user['owner']):
                return jsonify({'message': "Insufficient privileges"}), 401
        # Delete environments
        for environment in environments:
            self._environments.delete(environment)
        return jsonify({'message': 'Selected environments deleted'}), 200
