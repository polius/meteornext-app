import imp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Actions:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._groups = imp.load_source('groups', '{}/models/admin/groups.py'.format(credentials['path'])).Groups(credentials)
        self._deployments = imp.load_source('deployments', '{}/models/deployments/deployments.py'.format(credentials['path'])).Deployments(credentials)
        self._deployments_basic = imp.load_source('basic', '{}/models/deployments/deployments_basic.py'.format(credentials['path'])).Deployments_Basic(credentials)
        self._deployments_pro = imp.load_source('pro', '{}/models/deployments/deployments_pro.py'.format(credentials['path'])).Deployments_Pro(credentials)

        # Init meteor
        self._meteor = imp.load_source('meteor', '{}/routes/deployments/meteor.py'.format(credentials['path'])).Meteor(credentials)

    def blueprint(self):
        # Init blueprint
        deployments_actions_blueprint = Blueprint('deployments_actions', __name__, template_folder='deployments_actions')

        @deployments_actions_blueprint.route('/deployments/start', methods=['POST'])
        @jwt_required
        def deployments_start_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Call auxiliary method
            return self.__start(user, deployment_json)

        @deployments_actions_blueprint.route('/deployments/stop', methods=['POST'])
        @jwt_required
        def deployments_stop_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

        return deployments_actions_blueprint

    def __start(self, user, data):
        # Get Deployment
        deployment = self._deployments.getMode(user['id'], {'id': data['execution_id']})

        # Check if deployment exists
        if len(deployment) == 0:
            return jsonify({'message': 'This deployment does not exist.'}), 400
        else:
            deployment = deployment[0]
    
        # Build Meteor Data & Update Flags
        if deployment['mode'] == 'BASIC':
            meteor_data = self._deployments_basic.get(user['id'], execution_id=data['execution_id'])[0]
            self._deployments_basic.startExecution(user['id'], meteor_data['execution_id'])
        elif deployment['mode'] == 'PRO':
            meteor_data = self._deployments_pro.get(user['id'], execution_id=data['execution_id'])[0]
            self._deployments_pro.startExecution(user['id'], meteor_data['execution_id'])

        # Get Meteor Additional Parameters
        meteor_data['group_id'] = user['group_id']
        meteor_data['execution_threads'] = self._groups.get(group_id=user['group_id'])[0]['deployments_threads']

        # Start Meteor Execution
        self._meteor.execute(meteor_data)

        # Return Successful Message
        return jsonify({'message': 'Deployment started successfully'}), 200

    def __stop(self, user, data):
        pass