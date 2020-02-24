import os
import json
import signal
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import utils
import models.admin.users
import models.admin.groups
import models.admin.settings
import models.deployments.environments
import models.deployments.deployments
import models.deployments.deployments_inbenta
import models.deployments.deployments_finished
import models.notifications
import routes.deployments.meteor

class Inbenta:
    def __init__(self, app, sql):
        self._app = app
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._settings = models.admin.settings.Settings(sql)
        self._environments = models.deployments.environments.Environments(sql)
        self._deployments = models.deployments.deployments.Deployments(sql)
        self._deployments_inbenta = models.deployments.deployments_inbenta.Deployments_Inbenta(sql)
        self._deployments_finished = models.deployments.deployments_finished.Deployments_Finished(sql)
        self._notifications = models.notifications.Notifications(sql)

        # Init meteor
        self._meteor = routes.deployments.meteor.Meteor(app, sql)

    def license(self, value):
        self._license = value

    def blueprint(self):
        # Init blueprint
        deployments_inbenta_blueprint = Blueprint('deployments_inbenta', __name__, template_folder='deployments_inbenta')

        @deployments_inbenta_blueprint.route('/deployments/inbenta', methods=['GET','POST','PUT'])
        @jwt_required
        def deployments_inbenta_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_inbenta']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            if request.method == 'GET':
                return self.__get(user)
            elif request.method == 'POST':
                return self.__post(user, deployment_json)
            elif request.method == 'PUT':
                return self.__put(user, deployment_json)

        @deployments_inbenta_blueprint.route('/deployments/inbenta/executions', methods=['GET'])
        @jwt_required
        def deployments_inbenta_executions():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_inbenta']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user authority
            authority = self._deployments.getUser(request.args['deployment_id'])
            if len(authority) == 0:
                return jsonify({'message': 'This deployment does not exist'}), 400
            elif authority[0]['user_id'] != user['id'] and not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 400

            # Get deployment executions
            executions = self._deployments_inbenta.getExecutions(request.args['deployment_id'])
            return jsonify({'data': executions }), 200

        @deployments_inbenta_blueprint.route('/deployments/inbenta/start', methods=['POST'])
        @jwt_required
        def deployments_inbenta_start():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_inbenta']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Check deployment authority
            authority = self._deployments_inbenta.getUser(deployment_json['execution_id'])
            if len(authority) == 0:
                return jsonify({'message': 'This deployment does not exist'}), 400
            elif authority[0]['user_id'] != user['id'] and not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 400

            # Call Auxiliary Method
            return self.__start(user, deployment_json)

        @deployments_inbenta_blueprint.route('/deployments/inbenta/stop', methods=['POST'])
        @jwt_required
        def deployments_inbenta_stop():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_inbenta']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Check deployment authority
            authority = self._deployments_inbenta.getUser(deployment_json['execution_id'])
            if len(authority) == 0:
                return jsonify({'message': 'This deployment does not exist'}), 400
            elif authority[0]['user_id'] != user['id'] and not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 400

            # Call Auxiliary Method
            return self.__stop(user, deployment_json)

        @deployments_inbenta_blueprint.route('/deployments/inbenta/public', methods=['POST'])
        @jwt_required
        def deployments_inbenta_public():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_inbenta']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Check deployment authority
            authority = self._deployments_inbenta.getUser(deployment_json['execution_id'])
            if len(authority) == 0:
                return jsonify({'message': 'This deployment does not exist'}), 400
            elif authority[0]['user_id'] != user['id'] and not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 400

            # Change deployment public value
            self._deployments_inbenta.setPublic(deployment_json['execution_id'], deployment_json['public'])

            return jsonify({'message': 'OK'}), 200

        return deployments_inbenta_blueprint

    ###################
    # Recurring Tasks #
    ###################
    def check_finished(self):
        # Get all inbenta finished executions
        finished = self._deployments_finished.getInbenta()

        for f in finished:
            # Create notifications
            notification = {'icon': 'fas fa-circle', 'category': 'deployment'}
            notification['name'] = '{} has finished'.format(f['name'])
            notification['status'] = 'ERROR' if f['status'] == 'FAILED' else f['status']
            notification['data'] = '{{"id": "{}", "name": "{}", "mode": "INBENTA", "environment": "{}", "method": "{}", "overall": "{}"}}'.format(f['id'], f['name'], f['environment'], f['method'], f['overall'])
            self._notifications.post(f['user_id'], notification)

            # Clean finished deployments
            finished_deployment = {'mode': 'INBENTA', 'id': f['id']}
            self._deployments_finished.delete(finished_deployment)

    def check_scheduled(self):
        # Get all inbenta scheduled executions
        scheduled = self._deployments_inbenta.getScheduled()

        # Check logs path permissions
        if not self.__check_logs_path():
            for s in scheduled:
                self._deployments_inbenta.setError(s['execution_id'], 'The local logs path has no write permissions')
        else:
            for s in scheduled:
                # Update Execution Status
                status = 'STARTING' if s['concurrent_executions'] == 0 else 'QUEUED'
                self._deployments_inbenta.updateStatus(s['execution_id'], status)

                # Start Meteor Execution
                if s['concurrent_executions'] == 0:
                    self._meteor.execute(s)
                    # Add Deployment to be Tracked
                    deployment = {"mode": s['mode'], "id": s['execution_id']}
                    self._deployments_finished.post(deployment)

    ####################
    # Internal Methods #
    ####################
    def __get(self, user):
        # Check deployment authority
        authority = self._deployments_inbenta.getUser(request.args['execution_id'])
        if len(authority) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        elif authority[0]['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400
        
        # Get deployment
        deployment = self._deployments_inbenta.get(request.args['execution_id'])
        deployment[0]['products_list'] = {"Chatbot": "chatbot", "KM": "km", "Search": "search", "Ticketing": "ticketing", "Legacy": "no-product"} 
        deployment[0]['schema_list'] = ['logs_cmpl', 'tmpl_edit', 'tickets']

        # Get environments
        environments = [i['name'] for i in self._environments.get(user['group_id'])]

        # Return data
        return jsonify({'deployment': deployment, 'environments': environments}), 200

    def __post(self, user, data):
        # Check Coins
        group = self._groups.get(group_id=user['group_id'])[0]
        if (user['coins'] - group['coins_execution']) < 0:
            return jsonify({'message': 'Insufficient Coins'}), 400

        # Check logs path permissions
        if not self.__check_logs_path():
            return jsonify({'message': 'The local logs path has no write permissions'}), 400

        # Create deployment to the DB
        if data['scheduled'] != '':
            data['status'] = 'SCHEDULED'
            data['start_execution'] = False
            if datetime.strptime(data['scheduled'], '%Y-%m-%d %H:%M') < datetime.now():
                return jsonify({'message': 'The scheduled date cannot be in the past'}), 400
        elif data['start_execution']:
            data['status'] = 'QUEUED' if group['deployments_execution_concurrent'] != 0 else 'STARTING'
        else:
            data['status'] = 'CREATED'
        data['id'] = self._deployments.post(user['id'], data)
        data['execution_id'] = self._deployments_inbenta.post(data)

        # Consume Coins
        self._users.consume_coins(user, group['coins_execution'])

        # Build Response Data
        response = {'execution_id': data['execution_id'], 'coins': user['coins'] - group['coins_execution'] }

        if data['start_execution'] and group['deployments_execution_concurrent'] == 0:
            # Get Meteor Additional Parameters
            data['group_id'] = user['group_id']
            data['execution_threads'] = group['deployments_execution_threads']
            data['execution_limit'] = group['deployments_execution_limit']
            data['mode'] = 'INBENTA'
            data['user'] = user['username']

            # Start Meteor Execution
            self._meteor.execute(data)
            return jsonify({'message': 'Deployment Launched', 'data': response}), 200

        return jsonify({'message': 'Deployment created successfully', 'data': response}), 200

    def __put(self, user, data):
        # Check deployment authority
        authority = self._deployments_inbenta.getUser(data['execution_id'])
        if len(authority) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        elif authority[0]['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Check scheduled date
        if data['scheduled'] != '':
            data['start_execution'] = False
            if datetime.strptime(data['scheduled'], '%Y-%m-%d %H:%M') < datetime.now():
                return jsonify({'message': 'The scheduled date cannot be in the past'}), 400

        # Set Deployment Status
        if data['scheduled'] != '':
            data['status'] = 'SCHEDULED'
        elif data['start_execution']:
            data['status'] = 'QUEUED' if group['deployments_execution_concurrent'] != 0 else 'STARTING'
        else:
            data['status'] = 'CREATED'

        # Get current deployment
        deployment = self._deployments_inbenta.get(data['execution_id'])[0]

        # Proceed editing the deployment 
        if deployment['status'] in ['CREATED','SCHEDULED','QUEUED'] and not data['start_execution']:
            # Check if user has modified any value
            if deployment['environment'] != data['environment'] or \
            deployment['products'] != data['products'] or \
            deployment['schema'] != data['schema'] or \
            deployment['databases'] != data['databases'] or \
            deployment['queries'] != data['queries'] or \
            deployment['method'] != data['method'] or \
            (deployment['scheduled'] != data['scheduled'] and data['scheduled'] != ''):
                self._deployments_inbenta.put(data)
            return jsonify({'message': 'Deployment edited successfully', 'data': {'execution_id': data['execution_id']}}), 200
        else:
            # Check Coins
            group = self._groups.get(group_id=user['group_id'])[0]
            if not (authority[0]['user_id'] != user['id'] and user['admin']) and (user['coins'] - group['coins_execution']) < 0:
                return jsonify({'message': 'Insufficient Coins'}), 400

            # Check logs path permissions
            if not self.__check_logs_path():
                return jsonify({'message': 'The local logs path has no write permissions'}), 400

            # Create a new Inbenta Deployment
            data['execution_id'] = self._deployments_inbenta.post(data)

            # Consume Coins
            if authority[0]['user_id'] != user['id'] and user['admin']:
                coins = user['coins']
            else:
                self._users.consume_coins(user, group['coins_execution'])
                coins = user['coins'] - group['coins_execution']

            # Build Response Data
            response = {'execution_id': data['execution_id'], 'coins': coins }

            if data['start_execution'] and group['deployments_execution_concurrent'] == 0:
                # Get Meteor Additional Parameters
                data['group_id'] = user['group_id']
                data['execution_threads'] = group['deployments_execution_threads']
                data['execution_limit'] = group['deployments_execution_limit']
                data['mode'] = 'INBENTA'
                data['user'] = user['username']

                # Start Meteor Execution
                self._meteor.execute(data)
                return jsonify({'message': 'Deployment Launched', 'data': response}), 200

            return jsonify({'message': 'Deployment created successfully', 'data': response}), 200

    def __start(self, user, data):
        # Check logs path permissions
        if not self.__check_logs_path():
            return jsonify({'message': 'The local logs path has no write permissions'}), 400

        # Get Deployment
        deployment = self._deployments_inbenta.get(data['execution_id'])

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
        group = self._groups.get(group_id=user['group_id'])[0]
        deployment['group_id'] = user['group_id']
        deployment['execution_threads'] = group['deployments_execution_threads']
        deployment['execution_limit'] = group['deployments_execution_limit']
        deployment['mode'] = 'INBENTA'
        deployment['user'] = user['username']

        # Update Execution Status
        status = 'STARTING' if group['deployments_execution_concurrent'] == 0 else 'QUEUED'
        self._deployments_inbenta.updateStatus(deployment['execution_id'], status)

        # Start Meteor Execution
        if group['deployments_execution_concurrent'] == 0:
            self._meteor.execute(deployment)

        # Build Response Data
        response = {'execution_id': data['execution_id']}

        # Return Successful Message
        return jsonify({'data': response, 'message': 'Deployment Launched'}), 200

    def __stop(self, user, data):
        # Get the deployment pid
        deployment = self._deployments_inbenta.getPid(data['execution_id'])[0]

        # Update Execution Status
        self._deployments_basic.updateStatus(data['execution_id'], 'STOPPING')

        # Stop the execution
        try:
            os.kill(deployment['pid'], signal.SIGINT)
        except OSError:
            pass
        finally:
            return jsonify({'message': 'Stopping the execution...'}), 200

    def __check_logs_path(self):
        logs_path = json.loads(self._settings.get(setting_name='LOGS')[0]['value'])['local']['path']
        u = utils.Utils(self._app)
        return u.check_local_path(logs_path)