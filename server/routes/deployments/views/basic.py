import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Basic:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._groups = imp.load_source('groups', '{}/models/admin/groups.py'.format(credentials['path'])).Groups(credentials)
        self._deployments = imp.load_source('basic', '{}/models/deployments/deployments.py'.format(credentials['path'])).Deployments(credentials)
        self._deployments_basic = imp.load_source('basic', '{}/models/deployments/deployments_basic.py'.format(credentials['path'])).Deployments_Basic(credentials)

        # Init meteor
        self._meteor = imp.load_source('meteor', '{}/routes/deployments/meteor.py'.format(credentials['path'])).Meteor(credentials)

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
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user, deployment_json)
            elif request.method == 'PUT':
                return self.put(user, deployment_json)

        @deployments_basic_blueprint.route('/deployments/basic/executions', methods=['GET'])
        @jwt_required
        def deployments_basic_executions():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get deployment executions
            executions = self._deployments_basic.getExecutions(user['id'], request.args['deploymentID'])
            return jsonify({'data': executions }), 200

        @deployments_basic_blueprint.route('/deployments/basic/execution', methods=['GET'])
        @jwt_required
        def deployments_basic_execution():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get deployment execution
            return jsonify({'data': self._deployments_basic.getExecution(user['id'], request.args['executionID'])}), 200

        return deployments_basic_blueprint

    def get(self, user):
        deployment_id = request.args['deploymentID'] if 'deploymentID' in request.args else None
        return jsonify({'data': self._deployments_basic.get(user['id'], deployment_id)}), 200

    def post(self, user, data):
        # Create deployment to the DB
        data['id'] = self._deployments.post(user['id'], data)
        data['execution_id'] = self._deployments_basic.post(data)

        # Get Meteor Additional Parameters
        data['group_id'] = user['group_id']
        data['execution_threads'] = self._groups.get(group_id=user['group_id'])[0]['deployments_threads']

        # Start Meteor Execution
        if data['start_execution']:
            self._meteor.execute(data)

        return jsonify({'message': 'Deployment created successfully', 'data': {'deploymentID': data['id'] }}), 200

    def put(self, user, data):
        # Get current deployment
        deployment = self._deployments_basic.get(user['id'], data['id'])[0]

        # Check if user has modified any value
        if deployment['environment'] != data['environment'] or \
           deployment['databases'] != data['databases'] or \
           deployment['queries'] != data['queries'] or \
           deployment['method'] != data['method'] or \
           deployment['start_execution'] != data['start_execution']:
            self._deployments_basic.put(data)

        if data['start_execution']:
            # Get Meteor Additional Parameters
            deployment['group_id'] = user['group_id']
            deployment['execution_threads'] = self._groups.get(group_id=user['group_id'])[0]['deployments_threads']

            # Start Meteor Execution
            self._meteor.execute(data)

        return jsonify({'message': 'Deployment edited successfully'}), 200