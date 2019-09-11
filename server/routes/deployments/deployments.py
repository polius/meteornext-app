import imp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Deployments:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._deployments = imp.load_source('deployments', '{}/models/deployments/deployments.py'.format(credentials['path'])).Deployments(credentials)

    def blueprint(self):
        # Init blueprint
        deployments_blueprint = Blueprint('deployments', __name__, template_folder='deployments')

        @deployments_blueprint.route('/deployments', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def deployments_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['id'])
            elif request.method == 'POST':
                return self.post(user['id'], deployment_json)
            elif request.method == 'PUT':
                return self.put(user['id'], deployment_json)
            elif request.method == 'DELETE':
                return self.delete(user['id'], deployment_json)

        return deployments_blueprint

    def get(self, user_id):
        return jsonify({'data': self._deployments.get(user_id)}), 200

    def post(self, user_id, data):
        if self._deployments.exist(user_id, data):
            return jsonify({'message': 'This deployment currently exists'}), 400
        else:
            self._deployments.post(user_id, data)
            return jsonify({'message': 'Deployment added successfully'}), 200

    def put(self, user_id, data):
        if not self._deployments.exist(user_id, data):
            return jsonify({'message': 'This deployment does not exist'}), 400
        else:
            self._deployments.put(user_id, data)
            return jsonify({'message': 'Deployment edited successfully'}), 200

    def delete(self, user_id, data):
        for deploy in data:
            self._deployments.delete(user_id, deploy)
        return jsonify({'message': 'Selected deployments deleted successfully'}), 200
    
    def remove(self, user_id):
        self._deployments.remove(user_id)