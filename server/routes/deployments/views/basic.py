import os
import imp
import signal
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

        # Coins per execution
        self._coins_execution = 10

    def blueprint(self):
        # Init blueprint
        deployments_basic_blueprint = Blueprint('deployments_basic', __name__, template_folder='deployments_basic')

        @deployments_basic_blueprint.route('/deployments/basic', methods=['GET','POST','PUT'])
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
                return self.__get(user)
            elif request.method == 'POST':
                return self.__post(user, deployment_json)
            elif request.method == 'PUT':
                return self.__put(user, deployment_json)

        @deployments_basic_blueprint.route('/deployments/basic/executions', methods=['GET'])
        @jwt_required
        def deployments_basic_executions():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get deployment executions
            executions = self._deployments_basic.getExecutions(user['id'], request.args['deployment_id'])
            return jsonify({'data': executions }), 200

        @deployments_basic_blueprint.route('/deployments/basic/start', methods=['POST'])
        @jwt_required
        def deployments_basic_start():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Call Auxiliary Method
            return self.__start(user, deployment_json)

        @deployments_basic_blueprint.route('/deployments/basic/stop', methods=['POST'])
        @jwt_required
        def deployments_basic_stop():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Call Auxiliary Method
            return self.__stop(user, deployment_json)

        @deployments_basic_blueprint.route('/deployments/basic/public', methods=['POST'])
        @jwt_required
        def deployments_basic_public():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Change deployment public value
            self._deployments_basic.setPublic(user['id'], deployment_json['execution_id'], deployment_json['public'])

            return jsonify({'message': 'OK'}), 200

        return deployments_basic_blueprint

    ####################
    # Internal Methods #
    ####################
    def __get(self, user):
        return jsonify({'data': self._deployments_basic.get(user['id'], request.args['execution_id'])}), 200

    def __post(self, user, data):
        # Check Coins
        group = self._groups.get(group_id=user['group_id'])[0]
        if (user['coins'] - group['coins_execution']) < 0:
            return jsonify({'message': 'Insufficient Coins'}), 400

        # Create deployment to the DB
        data['id'] = self._deployments.post(user['id'], data)
        data['status'] = 'STARTING' if data['start_execution'] else 'CREATED'
        data['execution_id'] = self._deployments_basic.post(data)

        # Consume Coins
        self._users.consume_coins(user, group['coins_execution'])

        # Build Response Data
        response = {'execution_id': data['execution_id'], 'coins': user['coins'] - group['coins_execution'] }

        if data['start_execution']:
            # Get Meteor Additional Parameters
            data['group_id'] = user['group_id']
            data['execution_threads'] = group['deployments_execution_threads']
            data['epf'] = group['deployments_execution_plan_factor']
            data['mode'] = 'BASIC'

            # Start Meteor Execution
            self._meteor.execute(data)
            return jsonify({'message': 'Deployment Launched', 'data': response}), 200

        return jsonify({'message': 'Deployment created successfully', 'data': response}), 200

    def __put(self, user, data):
        # Get current deployment
        deployment = self._deployments_basic.get(user['id'], data['execution_id'])[0]

        if deployment['status'] == 'CREATED' and not data['start_execution']:
            # Check if user has modified any value
            if deployment['environment'] != data['environment'] or \
            deployment['databases'] != data['databases'] or \
            deployment['queries'] != data['queries'] or \
            deployment['method'] != data['method']:
                self._deployments_basic.put(data)
            return jsonify({'message': 'Deployment edited successfully', 'data': {'execution_id': data['execution_id']}}), 200
        else:
            # Check Coins
            group = self._groups.get(group_id=user['group_id'])[0]
            if (user['coins'] - group['coins_execution']) < 0:
                return jsonify({'message': 'Insufficient Coins'}), 400

            # Create a new Basic Deployment
            data['status'] = 'STARTING' if data['start_execution'] else 'CREATED'
            data['execution_id'] = self._deployments_basic.post(data)

            # Consume Coins
            self._users.consume_coins(user, group['coins_execution'])

            # Build Response Data
            response = {'execution_id': data['execution_id'], 'coins': user['coins'] - group['coins_execution'] }

            if data['start_execution']:
                # Get Meteor Additional Parameters
                data['group_id'] = user['group_id']
                data['execution_threads'] = group['deployments_execution_threads']
                data['epf'] = group['deployments_execution_plan_factor']
                data['mode'] = 'BASIC'

                # Start Meteor Execution
                self._meteor.execute(data)
                return jsonify({'message': 'Deployment Launched', 'data': response}), 200

            return jsonify({'message': 'Deployment created successfully', 'data': response}), 200

    def __start(self, user, data):
        # Get Deployment
        deployment = self._deployments_basic.get(user['id'], data['execution_id'])

        # Check if deployment exists
        if len(deployment) == 0:
            return jsonify({'message': 'This deployment does not exist.'}), 400
        else:
            deployment = deployment[0]

        # Get Meteor Additional Parameters
        group = self._groups.get(group_id=user['group_id'])[0]
        deployment['group_id'] = user['group_id']
        deployment['execution_threads'] = group['deployments_execution_threads']
        deployment['epf'] = group['deployments_execution_plan_factor']
        deployment['mode'] = 'BASIC'

        # Update Execution Status
        self._deployments_basic.startExecution(user['id'], deployment['execution_id'])

        # Start Meteor Execution
        self._meteor.execute(deployment)

        # Build Response Data
        response = {'execution_id': data['execution_id']}

        # Return Successful Message
        return jsonify({'data': response, 'message': 'Deployment Launched'}), 200

    def __stop(self, user, data):
        result = self._deployments_basic.getPid(user['id'], data['execution_id'])

        # Check if deployment exists
        if len(result) == 0:
            return jsonify({'message': 'This deployment does not exist.'}), 400
        else:
            pid = result[0]['pid']

        # Update Execution Status
        self._deployments_basic.stopExecution(user['id'], data['execution_id'])

        # Stop the execution
        try:
            os.kill(pid, signal.SIGINT)
        except OSError:
            pass
        finally:
            return jsonify({'message': 'Stopping the execution...'}), 200
