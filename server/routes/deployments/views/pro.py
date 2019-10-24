import os
import imp
import signal
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Pro:
    def __init__(self, credentials):
        self._credentials = credentials

        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._groups = imp.load_source('groups', '{}/models/admin/groups.py'.format(credentials['path'])).Groups(credentials)
        self._deployments = imp.load_source('basic', '{}/models/deployments/deployments.py'.format(credentials['path'])).Deployments(credentials)
        self._deployments_pro = imp.load_source('pro', '{}/models/deployments/deployments_pro.py'.format(credentials['path'])).Deployments_Pro(credentials)

        # Init meteor
        self._meteor = imp.load_source('meteor', '{}/routes/deployments/meteor.py'.format(credentials['path'])).Meteor(credentials)

    def blueprint(self):
        # Init blueprint
        deployments_pro_blueprint = Blueprint('deployments_pro', __name__, template_folder='deployments_pro')

        @deployments_pro_blueprint.route('/deployments/pro', methods=['GET','POST','PUT'])
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
                return self.__get(user)
            elif request.method == 'POST':
                return self.__post(user, deployment_json)
            elif request.method == 'PUT':
                return self.__put(user, deployment_json)

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
            executions = self._deployments_pro.getExecutions(user['id'], request.args['deployment_id'])
            return jsonify({'data': executions }), 200

        @deployments_pro_blueprint.route('/deployments/pro/start', methods=['POST'])
        @jwt_required
        def deployments_pro_start():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Call Auxiliary Method
            return self.__start(user, deployment_json)

        @deployments_pro_blueprint.route('/deployments/pro/stop', methods=['POST'])
        @jwt_required
        def deployments_pro_stop():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Call Auxiliary Method
            return self.__stop(user, deployment_json)

        @deployments_pro_blueprint.route('/deployments/pro/public', methods=['POST'])
        @jwt_required
        def deployments_pro_public():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Change deployment public value
            self._deployments_pro.setPublic(user['id'], deployment_json['execution_id'], deployment_json['public'])

            return jsonify({'message': 'OK'}), 200

        return deployments_pro_blueprint

    ####################
    # Internal Methods #
    ####################
    def __get(self, user):
        return jsonify({'data': self._deployments_pro.get(user['id'], request.args['execution_id'])}), 200

    def __post(self, user, data):
        # Create deployment to the DB
        data['id'] = self._deployments.post(user['id'], data)
        data['status'] = 'STARTING' if data['start_execution'] else 'CREATED'
        data['execution_id'] = self._deployments_pro.post(data)

        if data['start_execution']:
            # Get Meteor Additional Parameters
            data['group_id'] = user['group_id']
            data['execution_threads'] = self._groups.get(group_id=user['group_id'])[0]['deployments_threads']

            # Start Meteor Execution
            self._meteor.execute(data)

        return jsonify({'message': 'Deployment created successfully', 'data': data['execution_id']}), 200

    def __put(self, user, data):
        # Get current deployment
        deployment = self._deployments_pro.get(user['id'], data['execution_id'])[0]

        if deployment['status'] == 'CREATED' and not data['start_execution']:
            # Check if user has modified any value
            if deployment['environment'] != data['environment'] or \
            deployment['code'] != data['code'] or \
            deployment['method'] != data['method']:
                self._deployments_pro.put(data)
        else:
            # Create a new Pro Deployment
            data['status'] = 'STARTING' if data['start_execution'] else 'CREATED'
            data['execution_id'] = self._deployments_pro.post(data)

            if data['start_execution']:
                # Get Meteor Additional Parameters
                data['group_id'] = user['group_id']
                data['execution_threads'] = self._groups.get(group_id=user['group_id'])[0]['deployments_threads']

                # Start Meteor Execution
                self._meteor.execute(data)

        return jsonify({'message': 'Deployment edited successfully', 'data': data['execution_id']}), 200

    def __start(self, user, data):
        # Get Deployment
        deployment = self._deployments_pro.get(user['id'], data['execution_id'])

        # Check if deployment exists
        if len(deployment) == 0:
            return jsonify({'message': 'This deployment does not exist.'}), 400
        else:
            deployment = deployment[0]

        # Get Meteor Additional Parameters
        deployment['group_id'] = user['group_id']
        deployment['execution_threads'] = self._groups.get(group_id=user['group_id'])[0]['deployments_threads']

        # Update Execution Status
        self._deployments_pro.startExecution(user['id'], deployment['execution_id'])

        # Start Meteor Execution
        self._meteor.execute(deployment)

        # Return Successful Message
        return jsonify({'message': 'Deployment started successfully'}), 200

    def __stop(self, user, data):
        result = self._deployments_pro.getPid(user['id'], data['execution_id'])
  
        # Check if deployment exists
        if len(result) == 0:
            return jsonify({'message': 'This deployment does not exist.'}), 400
        else:
            pid = result[0]['pid']

        # Update Execution Status
        self._deployments_pro.stopExecution(user['id'], data['execution_id'])

        # Stop the execution
        try:
            os.kill(pid, signal.SIGINT)
        except OSError as e:
            print(str(e))
        finally:
            return jsonify({'message': 'Stopping the execution...'}), 200
