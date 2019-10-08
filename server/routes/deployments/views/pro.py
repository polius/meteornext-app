import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Pro:
    def __init__(self, credentials):
        self._credentials = credentials

        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._deployments = imp.load_source('basic', '{}/models/deployments/deployments.py'.format(credentials['path'])).Deployments(credentials)
        self._deployments_pro = imp.load_source('pro', '{}/models/deployments/deployments_pro.py'.format(credentials['path'])).Deployments_Pro(credentials)

        # Init meteor
        self._meteor = imp.load_source('meteor', '{}/routes/deployments/meteor.py'.format(credentials['path'])).Meteor(credentials)

    def blueprint(self):
        # Init blueprint
        deployments_pro_blueprint = Blueprint('deployments_pro', __name__, template_folder='deployments_pro')

        @deployments_pro_blueprint.route('/deployments/pro', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def deployments_pro_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user, deployment_json)
            elif request.method == 'PUT':
                return self.put(user, deployment_json)

        @deployments_pro_blueprint.route('/deployments/pro/code', methods=['GET'])
        @jwt_required
        def deployments_pro_code():
            # Retrieve code
            with open('{}/../apps/Meteor/app/query_execution.py'.format(self._credentials['path'])) as file_open:
                return jsonify({'data': file_open.read()}), 200

        @deployments_pro_blueprint.route('/deployments/pro/executions', methods=['GET'])
        @jwt_required
        def deployments_pro_executions():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get deployment executions
            executions = self._deployments_pro.getExecutions(user['id'], request.args['deploymentID'])
            return jsonify({'data': executions }), 200

        @deployments_pro_blueprint.route('/deployments/pro/execution', methods=['GET'])
        @jwt_required
        def deployments_pro_execution():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get deployment execution
            return jsonify({'data': self._deployments_pro.getExecution(user['id'], request.args['executionID'])}), 200

        return deployments_pro_blueprint

    def get(self, user):
        deployment_id = request.args['deploymentID'] if 'deploymentID' in request.args else None
        print(deployment_id)
        return jsonify({'data': self._deployments_pro.get(user['id'], deployment_id=deployment_id)}), 200

    def post(self, user, data):
        # Create deployment to the DB
        data['id'] = self._deployments.post(user['id'], data)
        data['execution_id'] = self._deployments_pro.post(data)

        # Start Meteor Execution
        data['group_id'] = user['group_id']
        self._meteor.execute(data)
        return jsonify({'message': 'Deployment created successfully', 'data': {'deploymentID': data['id'] }}), 200

    def put(self, user, data):
        # Get current deployment
        deployment = self._deployments_pro.get(user['id'], data['id'])[0]

        # Check if user has modified any value
        if deployment['environment'] == data['environment'] and \
           deployment['code'] == data['code'] and \
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
            self._deployments_pro.post(data)
        else:
            # Edit the current deployment if it's not already executed
            self._deployments_pro.put(data)
        return jsonify({'message': 'Deployment edited successfully'}), 200