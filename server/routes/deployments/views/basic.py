import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Basic:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._deployments = imp.load_source('basic', '{}/models/deployments/deployments.py'.format(credentials['path'])).Deployments(credentials)
        self._deployments_basic = imp.load_source('basic', '{}/models/deployments/deployments_basic.py'.format(credentials['path'])).Deployments_Basic(credentials)

    def blueprint(self):
        # Init blueprint
        deployments_basic_blueprint = Blueprint('deployments_basic', __name__, template_folder='deployments_basic')

        @deployments_basic_blueprint.route('/deployments/basic', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def deployments_basic_method():
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

        return deployments_basic_blueprint

    def get(self, user_id):
        deployment_id = request.args['deploymentID'] if 'deploymentID' in request.args else None
        return jsonify({'data': self._deployments_basic.get(user_id, deployment_id)}), 200

    def post(self, user_id, data):
        # Check if 'execution_threads' is a digit between 2-10
        if data['execution'] == 'PARALLEL':
            if not str(data['execution_threads']).isdigit() or int(data['execution_threads']) < 2 or int(data['execution_threads']) > 10:
                return jsonify({'message': "The 'Threads' field should be an integer between 2-10"}), 400

        data['id'] = self._deployments.post(user_id, data)
        self._deployments_basic.post(data)
        return jsonify({'message': 'Deployment created successfully'}), 200

    def put(self, user_id, data):
        # Check if 'execution_threads' is a digit between 2-10
        if data['execution'] == 'PARALLEL':
            if not str(data['execution_threads']).isdigit() or int(data['execution_threads']) < 2 or int(data['execution_threads']) > 10:
                return jsonify({'message': "The 'Threads' field should be an integer between 2-10"}), 400

        # Get current deployment
        deployment = self._deployments_basic.get(user_id, data['id'])[0]

        # Check if user has modified any value
        if deployment['environment'] == data['environment'] and \
           deployment['databases'] == data['databases'] and \
           deployment['queries'] == data['queries'] and \
           deployment['method'] == data['method'] and \
           deployment['execution'] == data['execution'] and \
           deployment['start_execution'] == data['start_execution']:
            if 'execution_threads' in data:
                if deployment['execution_threads'] == data['execution_threads']:
                    return jsonify({'message': 'Deployment edited successfully'}), 200
            else:
                return jsonify({'message': 'Deployment edited successfully'}), 200

        if deployment['start_execution'] == 1:
            # Create a new deployment if the current one is already executed
            self._deployments_basic.post(data)
        else:
            # Edit the current deployment if it's not already executed
            self._deployments_basic.put(data)
        return jsonify({'message': 'Deployment edited successfully'}), 200