import imp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Environments:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._environments = imp.load_source('environments', '{}/models/deployments/environments.py'.format(credentials['path'])).Environments(credentials)

    def blueprint(self):
        # Init blueprint
        environments_blueprint = Blueprint('environments', __name__, template_folder='environments')

        @environments_blueprint.route('/deployments/environments', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def environments_method():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User Group ID
            group_id = self._users.get(get_jwt_identity())[0]['group_id']

            # Get Request Json
            environment_json = request.get_json()

            if request.method == 'GET':
                return self.get(group_id)
            elif request.method == 'POST':
                return self.post(group_id, environment_json)
            elif request.method == 'PUT':
                return self.put(group_id, environment_json)
            elif request.method == 'DELETE':
                return self.delete(group_id, environment_json)

        return environments_blueprint

    def get(self, group_id):
        return jsonify({'data': self._environments.get(group_id)}), 200

    def post(self, group_id, data):
        if self._environments.exist(group_id, data):
            return jsonify({'message': 'This environment currently exists'}), 400
        else:
            self._environments.post(group_id, data)
            return jsonify({'message': 'Environment added successfully'}), 200

    def put(self, group_id, data):
        if data['current_name'] != data['name'] and self._environments.exist(group_id, data):
            return jsonify({'message': 'This new environment name currently exists'}), 400
        else:
            self._environments.put(group_id, data)
            return jsonify({'message': 'Environment edited successfully'}), 200

    def delete(self, group_id, data):
        for environment in data:
            self._environments.delete(group_id, environment)
        return jsonify({'message': 'Selected environments deleted successfully'}), 200
    
    def remove(self, group_id):
        self._environments.remove(group_id)