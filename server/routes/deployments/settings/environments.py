from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.environments
import models.deployments.regions

class Environments:
    def __init__(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._environments = models.deployments.environments.Environments(sql)
        self._regions = models.deployments.regions.Regions(sql)

    def blueprint(self):
        # Init blueprint
        environments_blueprint = Blueprint('environments', __name__, template_folder='environments')

        @environments_blueprint.route('/deployments/environments', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def environments_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_edit'] and request.method != 'GET':
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            environment_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['group_id'])
            elif request.method == 'POST':
                return self.post(user['group_id'], environment_json)
            elif request.method == 'PUT':
                return self.put(user['group_id'], environment_json)
            elif request.method == 'DELETE':
                return self.delete(user['group_id'], environment_json)

        return environments_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id):
        return jsonify({'data': self._environments.get(group_id)}), 200

    def post(self, group_id, data):
        if self._environments.exist(group_id, data):
            return jsonify({'message': 'This environment currently exists'}), 400
        else:
            self._environments.post(group_id, data)
            return jsonify({'message': 'Environment added successfully'}), 200

    def put(self, group_id, data):
        if self._environments.exist(group_id, data):
            return jsonify({'message': 'This new environment currently exists'}), 400
        else:
            self._environments.put(group_id, data)
            return jsonify({'message': 'Environment edited successfully'}), 200

    def delete(self, group_id, data):
        # Check inconsistencies
        for environment in data:
            if self._regions.exist_by_environment(group_id, environment):
                return jsonify({'message': "The environment '" + environment['name'] + "' has attached regions"}), 400

        for environment in data:
            self._environments.delete(group_id, environment)
        return jsonify({'message': 'Selected environments deleted successfully'}), 200
    
    def remove(self, group_id):
        self._environments.remove(group_id)