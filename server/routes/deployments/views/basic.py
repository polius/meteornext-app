import os
import json
import signal
import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import utils
import models.admin.users
import models.admin.groups
import models.admin.settings
import models.inventory.environments
import models.deployments.deployments
import models.deployments.deployments_basic
import models.deployments.deployments_finished
import models.notifications
import routes.deployments.meteor

class Basic:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._settings = models.admin.settings.Settings(sql)
        self._environments = models.inventory.environments.Environments(sql)
        self._deployments = models.deployments.deployments.Deployments(sql)
        self._deployments_basic = models.deployments.deployments_basic.Deployments_Basic(sql)
        self._deployments_finished = models.deployments.deployments_finished.Deployments_Finished(sql)
        self._notifications = models.notifications.Notifications(sql)

        # Init meteor
        self._meteor = routes.deployments.meteor.Meteor(app, sql)

    def blueprint(self):
        # Init blueprint
        deployments_basic_blueprint = Blueprint('deployments_basic', __name__, template_folder='deployments_basic')

        @deployments_basic_blueprint.route('/deployments/basic', methods=['GET','POST','PUT'])
        @jwt_required()
        def deployments_basic_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['deployments_basic']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            if request.method == 'GET':
                return self.__get(user)
            elif request.method == 'POST':
                return self.__post(user, deployment_json)
            elif request.method == 'PUT':
                return self.__put(user, deployment_json)

        @deployments_basic_blueprint.route('/deployments/basic/start', methods=['POST'])
        @jwt_required()
        def deployments_basic_start():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['deployments_basic']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Check deployment authority
            authority = self._deployments_basic.getUser(deployment_json['execution_id'])
            if len(authority) == 0:
                return jsonify({'message': 'This deployment does not exist'}), 400
            elif authority[0]['id'] != user['id'] and not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 400

            # Call Auxiliary Method
            return self.__start(user, authority, deployment_json)

        @deployments_basic_blueprint.route('/deployments/basic/stop', methods=['POST'])
        @jwt_required()
        def deployments_basic_stop():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['deployments_basic']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Check params
            if 'mode' not in deployment_json or deployment_json['mode'] not in ['graceful','forceful']:
                return jsonify({'message': 'Mode parameter required'}), 400

            # Check deployment authority
            authority = self._deployments_basic.getUser(deployment_json['execution_id'])
            if len(authority) == 0:
                return jsonify({'message': 'This deployment does not exist'}), 400
            elif authority[0]['id'] != user['id'] and not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 400

            # Call Auxiliary Method
            return self.__stop(deployment_json)

        @deployments_basic_blueprint.route('/deployments/basic/public', methods=['POST'])
        @jwt_required()
        def deployments_basic_public():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['deployments_basic']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Check deployment authority
            authority = self._deployments_basic.getUser(deployment_json['execution_id'])
            if len(authority) == 0:
                return jsonify({'message': 'This deployment does not exist'}), 400
            elif authority[0]['id'] != user['id'] and not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 400

            # Change deployment public value
            self._deployments_basic.setPublic(deployment_json['execution_id'], deployment_json['public'])

            return jsonify({'message': 'OK'}), 200

        return deployments_basic_blueprint

    ####################
    # Internal Methods #
    ####################
    def __get(self, user):
        # Check deployment authority
        authority = self._deployments_basic.getUser(request.args['execution_id'])
        if len(authority) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        elif authority[0]['id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Get deployment
        deployment = self._deployments_basic.get(request.args['execution_id'])

        # Get environments
        environments = [{"id": i['id'], "name": i['name'], "shared": i['shared']} for i in self._environments.get(authority[0]['id'], authority[0]['group_id'])]

        # Return data
        return jsonify({'deployment': deployment, 'environments': environments}), 200

    def __post(self, user, data):
        # Check Coins
        group = self._groups.get(group_id=user['group_id'])[0]
        if (user['coins'] - group['coins_execution']) < 0:
            return jsonify({'message': 'Insufficient Coins'}), 400

        # Check environment authority
        environment = self._environments.get(user_id=user['id'], group_id=user['group_id'], environment_id=data['environment'])
        if len(environment) == 0:
            return jsonify({'message': 'The environment does not exist'}), 400

        # Check logs path permissions
        if not self.__check_logs_path():
            return jsonify({'message': 'The local logs path has no write permissions'}), 400

        # Set Deployment Status
        if data['scheduled'] is not None:
            data['status'] = 'SCHEDULED'
            data['start_execution'] = False
            if datetime.datetime.strptime(data['scheduled'], '%Y-%m-%d %H:%M:%S') < datetime.datetime.now():
                return jsonify({'message': 'The scheduled date cannot be in the past'}), 400
        elif data['start_execution']:
            data['status'] = 'QUEUED' if group['deployments_execution_concurrent'] else 'STARTING'
        else:
            data['status'] = 'CREATED'

        # Create deployment to the DB
        data['group_id'] = group['id']
        data['id'] = self._deployments.post(user['id'], data)
        data['execution_id'] = self._deployments_basic.post(user['id'], data)

        # Consume Coins
        self._users.consume_coins(user, group['coins_execution'])

        # Build Response Data
        response = {'execution_id': data['execution_id'], 'coins': user['coins'] - group['coins_execution'] }

        if data['start_execution'] and not group['deployments_execution_concurrent']:
            # Get Meteor Additional Parameters
            data['group_id'] = user['group_id']
            data['environment_id'] = environment[0]['id']
            data['environment_name'] = environment[0]['name']
            data['execution_threads'] = group['deployments_execution_threads']
            data['execution_timeout'] = group['deployments_execution_timeout']
            data['mode'] = 'BASIC'
            data['user_id'] = user['id']
            data['username'] = user['username']

            # Start Meteor Execution
            self._meteor.execute(data)
            return jsonify({'message': 'Deployment Launched', 'data': response}), 200

        return jsonify({'message': 'Deployment created successfully', 'data': response}), 200

    def __put(self, user, data):
        # Get current deployment
        deployment = self._deployments_basic.get(data['execution_id'])[0]

        # Check deployment authority
        authority = self._deployments.getUser(data['id'])
        if len(authority) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        elif authority[0]['id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Check environment authority
        environment = self._environments.get(user_id=authority[0]['id'], group_id=authority[0]['group_id'], environment_id=data['environment'])
        if len(environment) == 0:
            return jsonify({'message': 'The environment does not exist'}), 400

        # Check scheduled date
        if data['scheduled'] is not None:
            data['start_execution'] = False
            if datetime.datetime.strptime(data['scheduled'], '%Y-%m-%d %H:%M:%S') < datetime.datetime.now():
                return jsonify({'message': 'The scheduled date cannot be in the past'}), 400

        # Proceed editing the deployment
        if deployment['status'] in ['CREATED','SCHEDULED'] and not data['start_execution']:
            # Check if user has modified any value
            if deployment['environment_id'] != data['environment'] or \
            deployment['databases'] != data['databases'] or \
            deployment['queries'] != data['queries'] or \
            deployment['method'] != data['method'] or \
            str(deployment['scheduled']) != str(data['scheduled']) and not (deployment['scheduled'] is None and data['scheduled'] == ''):
                data['group_id'] = authority[0]['group_id']
                self._deployments_basic.put(user['id'], data)
            return jsonify({'message': 'Deployment edited successfully', 'data': {'execution_id': data['execution_id']}}), 200
        else:
            # Check Coins
            group = self._groups.get(group_id=authority[0]['group_id'])[0]
            if not (authority[0]['id'] != user['id'] and user['admin']) and (user['coins'] - group['coins_execution']) < 0:
                return jsonify({'message': 'Insufficient Coins'}), 400

            # Check logs path permissions
            if not self.__check_logs_path():
                return jsonify({'message': 'The local logs path has no write permissions'}), 400

            # Set Deployment Status
            if data['scheduled'] is not None:
                data['status'] = 'SCHEDULED'
            elif data['start_execution']:
                data['status'] = 'QUEUED' if group['deployments_execution_concurrent'] else 'STARTING'
            else:
                data['status'] = 'CREATED'

            # Create a new Basic Deployment
            data['group_id'] = group['id']
            data['execution_id'] = self._deployments_basic.post(user['id'], data)

            # Consume Coins
            if authority[0]['id'] != user['id'] and user['admin']:
                coins = user['coins']
            else:
                self._users.consume_coins(user, group['coins_execution'])
                coins = user['coins'] - group['coins_execution']

            # Build Response Data
            response = {'execution_id': data['execution_id'], 'coins': coins }

            if data['start_execution'] and not group['deployments_execution_concurrent']:
                # Get Meteor Additional Parameters
                data['group_id'] = authority[0]['group_id']
                data['environment_id'] = environment[0]['id']
                data['environment_name'] = environment[0]['name']
                data['execution_threads'] = group['deployments_execution_threads']
                data['execution_timeout'] = group['deployments_execution_timeout']
                data['mode'] = 'BASIC'
                data['user_id'] = authority[0]['id']
                data['username'] = user['username']

                # Start Meteor Execution
                self._meteor.execute(data)
                return jsonify({'message': 'Deployment Launched', 'data': response}), 200

            return jsonify({'message': 'Deployment created successfully', 'data': response}), 200

    def __start(self, user, authority, data):
        # Check logs path permissions
        if not self.__check_logs_path():
            return jsonify({'message': 'The local logs path has no write permissions'}), 400

        # Get Deployment
        deployment = self._deployments_basic.get(data['execution_id'])

        # Check if deployment exists
        if len(deployment) == 0:
            return jsonify({'message': 'This deployment does not exist.'}), 400
        else:
            deployment = deployment[0]

        # Check if Deploy has already started
        if deployment['status'] == 'QUEUED':
            return jsonify({'message': 'Queued deployments cannot be started.'}), 400

        if deployment['status'] not in ['CREATED','SCHEDULED']:
            return jsonify({'message': ''}), 200

        # Get Meteor Additional Parameters
        group = self._groups.get(group_id=authority[0]['group_id'])[0]
        deployment['group_id'] = authority[0]['group_id']
        deployment['execution_threads'] = group['deployments_execution_threads']
        deployment['execution_timeout'] = group['deployments_execution_timeout']
        deployment['mode'] = 'BASIC'
        deployment['user_id'] = authority[0]['id']
        deployment['username'] = user['username']

        # Update Execution Status
        status = 'STARTING' if not group['deployments_execution_concurrent'] else 'QUEUED'
        self._deployments_basic.updateStatus(deployment['execution_id'], status)

        # Start Meteor Execution
        if not group['deployments_execution_concurrent']:
            self._meteor.execute(deployment)

        # Build Response Data
        response = {'execution_id': data['execution_id']}

        # Return Successful Message
        return jsonify({'data': response, 'message': 'Deployment Launched'}), 200

    def __stop(self, data):
        # Remove the deployment from the queue
        self._deployments_basic.updateStatus(data['execution_id'], 'STOPPED', True)

        # Get the deployment pid
        deployment = self._deployments_basic.getPid(data['execution_id'])[0]

        # Stop the execution if the deployment has already started
        mode = data['mode'] if 'mode' in data and data['mode'] in ['graceful','forceful'] else 'graceful'
        if deployment['pid'] is not None:
            self._deployments_basic.updateStatus(data['execution_id'], 'STOPPING', mode)
            try:
                if mode == 'graceful':
                    os.kill(deployment['pid'], signal.SIGINT)
                elif mode == 'forceful':
                    os.kill(deployment['pid'], signal.SIGTERM)
            except OSError:
                pass
            return jsonify({'message': 'Stopping the execution...'}), 200
        return jsonify({'message': 'Execution removed from the queue'}), 200

    def __check_logs_path(self):
        logs_path = json.loads(self._settings.get(setting_name='LOGS')[0]['value'])['local']['path']
        u = utils.Utils()
        return u.check_local_path(logs_path)