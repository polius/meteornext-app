import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.deployments
import models.inventory.environments
import models.inventory.regions

class Environments:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._deployments = models.deployments.deployments.Deployments(sql)
        self._environments = models.inventory.environments.Environments(sql)
        self._regions = models.inventory.regions.Regions(sql)

    def blueprint(self):
        # Init blueprint
        environments_blueprint = Blueprint('environments', __name__, template_folder='environments')

        @environments_blueprint.route('/inventory/environments', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def environments_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            environment_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['group_id'])
            elif request.method == 'POST':
                return self.post(user['id'], user['group_id'], environment_json)
            elif request.method == 'PUT':
                return self.put(user['id'], user['group_id'], environment_json)
            elif request.method == 'DELETE':
                return self.delete(user['group_id'])

        @environments_blueprint.route('/inventory/environments/list', methods=['GET'])
        @jwt_required
        def environments_list_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['inventory_enabled'] and request.method != 'GET':
                return jsonify({'message': 'Insufficient Privileges'}), 401
            
            # Get environments list
            return jsonify({'data': self._environments.get(user['group_id'])})

        return environments_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id):
        return jsonify({'environments': self._environments.get(group_id), 'environment_servers': self._environments.get_environment_servers(group_id), 'servers': self._environments.get_servers(group_id)}), 200
        # return jsonify({'environments': self._environments.get(group_id), 'servers': self._environments.get_servers(group_id)}), 200

    def post(self, user_id, group_id, data):
        if self._environments.exist(group_id, data):
            return jsonify({'message': 'This environment currently exists'}), 400
        else:
            self._environments.post(user_id, group_id, data)
            return jsonify({'message': 'Environment added successfully'}), 200

    def put(self, user_id, group_id, data):
        if self._environments.exist(group_id, data):
            return jsonify({'message': 'This new environment currently exists'}), 400
        else:
            self._environments.put(user_id, group_id, data)
            return jsonify({'message': 'Environment edited successfully'}), 200

    def delete(self, group_id):
        data = json.loads(request.args['environments'])
        # Check inconsistencies
        exist = True
        for environment in data:
            exist &= not self._deployments.existByEnvironment(environment)
        if not exist:
            return jsonify({'message': "The selected environments have related deployments"}), 400

        for environment in data:
            self._environments.delete(group_id, environment)
        return jsonify({'message': 'Selected environments deleted successfully'}), 200
    
    def remove(self, group_id):
        self._environments.remove(group_id)