import os
import sys
import uuid
import json
import gzip
import boto3
import signal
import botocore
import calendar
import unicodedata
import multiprocessing
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.admin.groups
import models.deployments.releases
import models.deployments.deployments
import models.deployments.deployments_pinned
import models.deployments.executions
import models.deployments.executions_queued
import models.deployments.executions_finished
import models.deployments.executions_scheduled
import models.admin.settings
import models.inventory.environments
import models.inventory.servers
import models.notifications
import routes.deployments.meteor

class Deployments:
    def __init__(self, license, sql=None):
        self._license = license
        if sql:
            self.init(sql)

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._releases = models.deployments.releases.Releases(sql)
        self._deployments = models.deployments.deployments.Deployments(sql)
        self._deployments_pinned = models.deployments.deployments_pinned.Deployments_Pinned(sql)
        self._executions = models.deployments.executions.Executions(sql)
        self._executions_queued = models.deployments.executions_queued.Executions_Queued(sql)
        self._executions_finished = models.deployments.executions_finished.Executions_Finished(sql)
        self._executions_scheduled = models.deployments.executions_scheduled.Executions_Scheduled(sql)
        self._settings = models.admin.settings.Settings(sql, self._license)
        self._environments = models.inventory.environments.Environments(sql, self._license)
        self._servers = models.inventory.servers.Servers(sql, self._license)
        self._notifications = models.notifications.Notifications(sql)

        # Init meteor
        self._meteor = routes.deployments.meteor.Meteor(sql, self._license)

    def blueprint(self):
        # Init blueprint
        deployments_blueprint = Blueprint('deployments', __name__, template_folder='deployments')

        @deployments_blueprint.route('/deployments', methods=['GET','POST','PUT'])
        @jwt_required()
        def deployments_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['deployments_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.__get(user)
            elif request.method == 'POST':
                return self.__post(user)
            elif request.method == 'PUT':
                return self.__put(user)

        @deployments_blueprint.route('/deployments/blueprint', methods=['GET'])
        @jwt_required()
        def deployments_code():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['deployments_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Retrieve blueprint
            code_path = os.path.dirname(os.path.realpath(__file__))
            with open('{}/blueprint.py'.format(code_path)) as file_open:
                return jsonify({'data': file_open.read()}), 200

        @deployments_blueprint.route('/deployments/start', methods=['POST'])
        @jwt_required()
        def deployments_start():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Start Deployment
            return self.__start(user, deployment_json)

        @deployments_blueprint.route('/deployments/stop', methods=['POST'])
        @jwt_required()
        def deployments_stop():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Stop Deployment
            return self.__stop(user, deployment_json)

        @deployments_blueprint.route('/deployments/results', methods=['GET'])
        @jwt_required()
        def deployments_results_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get Request Json URI
            uri = request.args.get('uri')

            # Get Execution Results Metadata
            results = self._deployments.getResults(uri)

            if len(results) == 0:
                return jsonify({'title': 'Unknown deployment', 'description': 'This deployment does not currently exist' }), 400
            results = results[0]

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if not results['shared'] and int(results['user_id']) != user['id'] and not user['admin']:
                return jsonify({'title': 'Authorized Access Only', 'description': 'The URL provided is private' }), 400

            # Parse execution data
            progress = json.loads(results['progress'])
            queries = progress['queries'] if 'queries' in progress else None
            error = progress['error'] if 'error' in progress else None
            method = results['method'].lower()

            # Get Execution Results File
            if results['logs'] == 'local':
                # Check if exists
                bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
                base_path = os.path.realpath(os.path.dirname(sys.executable)) if bin else os.path.realpath(os.path.dirname(sys.argv[0]))
                if not os.path.exists(f"{base_path}/files/deployments/{uri}.csv"):
                    return jsonify({'title': 'Deployment Expired', 'description': 'This deployment no longer exists' }), 400
                with open(f"{base_path}/files/deployments/{uri}.csv") as fopen:
                    data = fopen.read()
                return jsonify({"data": data, "method": method, "queries": queries, "error": error}), 200

            elif results['logs'] == 'amazon_s3':
                amazon = json.loads(self._settings.get(setting_name='AMAZON'))
                # Check Amazon S3 credentials are setup
                if not amazon['enabled'] or len(amazon['aws_access_key']) == 0 or len(amazon['aws_secret_access_key']) == 0:
                    return jsonify({'title': 'Can\'t connect to Amazon S3', 'description': 'Check the Amazon S3 credentials in the Admin Panel.' }), 400
                session = boto3.Session(
                    aws_access_key_id=amazon['aws_access_key'],
                    aws_secret_access_key=amazon['aws_secret_access_key'],
                    region_name=amazon['region']
                )
                try:
                    s3 = session.resource('s3')
                    obj = s3.meta.client.get_object(Bucket=amazon['bucket'], Key='deployments/{}.csv.gz'.format(uri))
                    with gzip.open(obj['Body'], 'rb') as fopen:
                        return jsonify({"data": fopen.read().decode('utf-8'), "method": method, "queries": queries, "error": error}), 200
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        return jsonify({'title': 'Deployment Expired', 'description': 'This deployment no longer exists in Amazon S3' }), 400
                    return jsonify({'title': 'Can\'t connect to Amazon S3', 'description': 'Check the Amazon S3 credentials in the Admin Panel.', 'error': str(e)}), 400
                except Exception as e:
                    return jsonify({'title': 'Can\'t connect to Amazon S3', 'description': 'Check the Amazon S3 credentials in the Admin Panel.', 'error': str(e)}), 400
            return jsonify({'title': 'Unknown deployment', 'description': 'This deployment does not currently exist' }), 400

        @deployments_blueprint.route('/deployments/executions', methods=['GET'])
        @jwt_required()
        def deployments_executions():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get args
            data = request.args

            # Get executions
            return self.__get_executions(user, data)

        @deployments_blueprint.route('/deployments/shared', methods=['POST'])
        @jwt_required()
        def deployments_shared():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            # Set Deployment Shared
            return self.__shared(user, deployment_json)

        @deployments_blueprint.route('/deployments/pinned', methods=['POST','DELETE'])
        @jwt_required()
        def deployments_pinned():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            if request.method == 'POST':
                for item in data:
                    self._deployments_pinned.post(user['id'], item)
                return jsonify({'message': f"Deployment{'s' if len(data) > 1 else ''} pinned"}), 200

            elif request.method == 'DELETE':
                for item in data:
                    self._deployments_pinned.delete(user['id'], item)
                return jsonify({'message': f"Deployment{'s' if len(data) > 1 else ''} unpinned"}), 200

        return deployments_blueprint

    ###################
    # Recurring Tasks #
    ###################
    def check_queued(self):
        # Notify finished queue deployments and remove it from queue
        finished = self._executions_queued.getFinished()
        for i in finished:
            if i['scheduled']:
                self._executions_finished.post(i['execution_id'])
        if len(finished) > 0:
            ids = ','.join([str(i['id']) for i in finished])
            self._executions_queued.delete(ids)

        # Populate new queued deployments
        self._executions_queued.build()

        # Build dictionary of executions
        executions_raw = self._executions_queued.getNext()
        groups = {}
        executions_ids = []
        executions = []
        for i in executions_raw:
            concurrent = groups.get(i['group'], 0)
            if concurrent < i['concurrent']:
                groups[i['group']] = concurrent + 1
                if i['status'] == 'QUEUED':
                    executions_ids.append(i['id'])

        if len(executions_ids) > 0:
            execution = self._executions.getExecutionsN(','.join(str(i) for i in executions_ids))
            for e in execution:
                for item in executions_ids:
                    if e['id'] == item:
                        executions.append(e)
                        break

        # Start Queued Executions
        for execution in executions:
            self._executions.updateStatus(execution['id'], 'STARTING', True)
            self._meteor.execute(execution)

    def check_finished(self):
        # Get all basic finished executions
        finished = self._executions_finished.get()

        for f in finished:
            # Create notifications
            notification = {'category': 'deployment'}
            notification['name'] = f"{f['name']} has finished."
            notification['status'] = 'ERROR' if f['status'] == 'FAILED' else f['status']
            notification['data'] = '{{"id": "{}"}}'.format(f['uri'])
            self._notifications.post(f['user_id'], notification)

            # Clean finished executions
            self._executions_finished.delete(f['id'])

    def check_recurring(self):
        # Get all finished executions that have an entry to the 'executions_scheduled' table and create a new scheduled.
        executions = self._executions_scheduled.get()
        for execution in executions:
            # Check environment
            environment = self._environments.get(user_id=execution['user_id'], group_id=execution['group_id'], environment_id=execution['environment_id'])
            if len(environment) == 0:
                notification = {'category': 'deployment', 'data': '{{"id": "{}"}}'.format(execution['uri']), 'status': 'ERROR', 'name': 'Cannot schedule a new recurring execution. The environment does not exist in your inventory.'}
                self._notifications.post(execution['user_id'], notification)
                self._executions_scheduled.delete(execution['execution_id'])
                continue

            # Check files path permissions
            if not self.__check_files_path():
                notification = {'category': 'deployment', 'data': '{{"id": "{}"}}'.format(execution['uri']), 'status': 'ERROR', 'name': 'Cannot schedule a new recurring execution. No write permissions in the files folder.'}
                self._notifications.post(execution['user_id'], notification)
                self._executions_scheduled.delete(execution['execution_id'])
                continue

            # Check if selected environment contains any disabled servers
            if self._environments.is_disabled(execution['user_id'], execution['group_id'], execution['environment_id']):
                notification = {'category': 'deployment', 'data': '{{"id": "{}"}}'.format(execution['uri']), 'status': 'ERROR', 'name': 'Cannot schedule a new recurring execution. The selected environment contains disabled servers.'}
                self._notifications.post(execution['user_id'], notification)
                self._executions_scheduled.delete(execution['execution_id'])
                continue

            # Check coins
            if (execution['user_coins'] - execution['deployments_coins']) < 0:
                notification = {'category': 'deployment', 'data': '{{"id": "{}"}}'.format(execution['uri']), 'status': 'ERROR', 'name': 'Cannot schedule a new recurring execution. Insufficient Coins.'}
                self._notifications.post(execution['user_id'], notification)
                self._executions_scheduled.delete(execution['execution_id'])
                continue

            # Calculate schedule
            schedule_rules = json.loads(execution['schedule_rules']) if execution['schedule_rules'] else None
            execution['scheduled'] = self.__get_next_schedule(execution['schedule_type'], execution['schedule_value'], schedule_rules)['value']
            execution['status'] = 'SCHEDULED'

            # Consume coins
            self._users.consume_coins({"username": execution['username']}, execution['deployments_coins'])

            # Create a new scheduled execution
            execution['uri'] = str(uuid.uuid4())
            execution_id = self._executions.post(execution['user_id'], execution)

            # Update 'executions_scheduled' table
            self._executions_scheduled.delete(execution['execution_id'])
            self._executions_scheduled.post(execution_id, execution['schedule_type'], execution['schedule_value'], execution['schedule_rules'])

    def check_scheduled(self):
        # Get all basic scheduled executions
        scheduled = self._executions.getScheduled()

        # Check files path permissions
        if not self.__check_files_path():
            for s in scheduled:
                self._executions.setError(s['id'], 'No write permissions in the files folder')
        else:
            for s in scheduled:
                # Update Execution Status
                status = 'QUEUED' if s['concurrent_executions'] else 'STARTING'
                self._executions.updateStatus(s['id'], status)
                # Start Meteor Execution
                if s['concurrent_executions'] is None:
                    self._meteor.execute(s)
                    # Add Execution to be Tracked
                    self._executions_finished.post(s['id'])

    #################
    # Class Methods #
    #################
    def __get(self, user):
        # Get all user deployments
        if 'uri' not in request.args:
            dfilter = json.loads(request.args['filter']) if 'filter' in request.args else None
            dsort = json.loads(request.args['sort']) if 'sort' in request.args else None
            deployments = self._deployments.get(user_id=user['id'], dfilter=dfilter, dsort=dsort)
            releases = self._releases.get(user['id'])
            deployments_list = self._deployments.getDeploymentsName(user['id'])
            return jsonify({'deployments': deployments, 'releases': releases, 'deployments_list': deployments_list}), 200

        # Get current execution
        execution = self._executions.get(request.args['uri'])

        # Check if deployment exists
        if len(execution) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        execution = execution[0]

        # Check deployment authority
        authority = self._deployments.getUser(execution['deployment_id'])
        if len(authority) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        authority = authority[0]
        if authority['id'] != user['id'] and not execution['shared'] and not user['admin']:
            return jsonify({'message': 'This deployment is private'}), 400

        # Add execution owner
        execution['owner'] = (authority['id'] == user['id'] or user['admin'])

        # Get environments
        environments = [{"id": i['id'], "name": i['name'], "shared": i['shared'], "secured": i['secured']} for i in self._environments.get(user['id'], user['group_id'])]

        # Return data
        return jsonify({'deployment': execution, 'environments': environments}), 200

    def __get_executions(self, user, data):
        # Get current execution
        execution = self._executions.get(data['uri'])

        # Check if deployment exists
        if len(execution) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        execution = execution[0]

        # Check user privileges
        if user['disabled'] or (execution['mode'] == 'BASIC' and not user['deployments_basic']) or (execution['mode'] == 'PRO' and not user['deployments_pro']):
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Check deployment authority
        authority = self._deployments.getUser(execution['deployment_id'])
        if len(authority) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        if authority[0]['id'] != user['id'] and not execution['shared'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Get deployment executions
        executions = self._deployments.getExecutions(execution['deployment_id'])
        return jsonify({'data': executions }), 200

    def __post(self, user):
        # Get Request Json
        data = request.get_json()

        # Init Data
        deployment = {
            'name': data['name'],
            'release_id': data['release'],
        }
        execution = {
            'environment_id': data['environment'],
            'mode': data['mode'],
            'databases': data.get('databases'),
            'queries': data.get('queries'),
            'code': data.get('code'),
            'method': data['method'],
            'url': data['url'] if 'url' in data else None,
            'uri': str(uuid.uuid4()),
        }

        # Parse queries
        if execution['queries'] is not None:
            execution['queries'] = json.dumps([{"q": i} for i in execution['queries']])

        # Check Coins
        group = self._groups.get(group_id=user['group_id'])[0]
        if (user['coins'] - group['deployments_coins']) < 0:
            return jsonify({'message': 'Insufficient Coins'}), 400

        # Check environment exists
        environment = self._environments.get(user_id=user['id'], group_id=user['group_id'], environment_id=execution['environment_id'])
        if len(environment) == 0:
            return jsonify({'message': 'The selected environment does not exist in your inventory'}), 400
        environment = environment[0]

        # Check environment contains at least one server
        servers = self._servers.get_by_environment(user['id'], user['group_id'], execution['environment_id'])
        if len(servers) == 0:
            return jsonify({'message': 'The selected environment does not contain servers'}), 400

        # Check files path permissions
        if not self.__check_files_path():
            return jsonify({'message': 'No write permissions in the files folder'}), 400

        # Check Code Syntax Errors
        if execution['mode'] == 'PRO':
            try:
                execution['code'] = unicodedata.normalize("NFKD", execution['code'])
                self.__secure_code(execution['code'])
            except Exception as e:
                return jsonify({'message': 'Errors in code: {}'.format(str(e).capitalize())}), 400

        # Calculate schedule
        if 'schedule_type' in data:
            schedule = self.__get_next_schedule(data['schedule_type'], data['schedule_value'], data.get('schedule_rules'))
            execution['scheduled'] = schedule['value']
            if schedule['error']:
                return jsonify({'message': schedule['error']}), 400

        # Check if selected environment contains any disabled servers
        if self._environments.is_disabled(user['id'], user['group_id'], execution['environment_id']):
            return jsonify({'message': 'The selected environment contains disabled servers.'}), 400

        # Set Execution Status
        if 'scheduled' in execution:
            execution['status'] = 'SCHEDULED'
            execution['start_execution'] = False
        else:
            execution['scheduled'] = None
            execution['start_execution'] = data['start_execution']
            if execution['start_execution']:
                execution['status'] = 'QUEUED'
            else:
                execution['status'] = 'CREATED'

        # Create deployment to the DB
        execution['deployment_id'] = self._deployments.post(user['id'], deployment)
        execution_id = self._executions.post(user['id'], execution)

        # Add Schedule to the current execution
        if execution['scheduled'] and data['schedule_type'] in ['daily','weekly','monthly']:
            schedule_rules = None
            if data['schedule_type'] in ['weekly','monthly']:
                rules = sorted([int(i) for i in data['schedule_rules']['rules']])
                schedule_rules = json.dumps({"rules": rules, "day": data['schedule_rules']['day']}) if data['schedule_type'] == 'monthly' else json.dumps({"rules": rules})
            self._executions_scheduled.post(execution_id, data['schedule_type'], data['schedule_value'], schedule_rules)
        else:
            self._executions_scheduled.delete(execution_id)

        # Consume Coins
        self._users.consume_coins(user, group['deployments_coins'])

        # Build Response Data
        response = {'uri': execution['uri'], 'coins': user['coins'] - group['deployments_coins'] }

        # Return Response
        return jsonify({'message': 'Deployment created', 'data': response}), 200

    def __put(self, user):
        # Get Request Json
        data = request.get_json()

        # Edit Metadata
        if 'name' in data.keys():
            self._deployments.putName(user, data)
            return jsonify({'message': 'Deployment edited'}), 200
        elif 'release' in data.keys():
            self._deployments.putRelease(user, data)
            return jsonify({'message': 'Deployment edited'}), 200

        # Get Data
        execution = {
            'environment_id': data['environment'],
            'mode': data['mode'],
            'databases': data.get('databases'),
            'queries': data.get('queries'),
            'code': data.get('code'),
            'method': data['method'],
            'url': data['url'] if 'url' in data else None,
            'uri': data['uri'],
        }

        # Parse queries
        if execution['queries'] is not None:
            execution['queries'] = json.dumps([{"q": i} for i in execution['queries']])

        # Get Current Deployment
        current_execution = self._executions.get(execution['uri'])

        # Check if deployment exists
        if len(current_execution) == 0:
            return jsonify({'message': 'This deployment does not exist.'}), 400
        current_execution = current_execution[0]

        # Check deployment authority
        authority = self._deployments.getUser(current_execution['deployment_id'])
        if len(authority) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        authority = authority[0]
        if authority['id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Get deployment group
        group = self._groups.get(group_id=user['group_id'])[0]

        # Check environment exists
        environment = self._environments.get(user_id=user['id'], group_id=user['group_id'], environment_id=data['environment'])
        if len(environment) == 0:
            return jsonify({'message': 'The selected environment does not exist in your inventory'}), 400
        environment = environment[0]

        # Check environment contains at least one server
        servers = self._servers.get_by_environment(user['id'], user['group_id'], data['environment'])
        if len(servers) == 0:
            return jsonify({'message': 'The selected environment does not contain servers'}), 400

        # Check files path permissions
        if not self.__check_files_path():
            return jsonify({'message': 'No write permissions in the files folder'}), 400

        # Check Code Syntax Errors
        if execution['mode'] == 'PRO':
            try:
                execution['code'] = unicodedata.normalize("NFKD", execution['code'])
                self.__secure_code(execution['code'])
            except Exception as e:
                return jsonify({'message': 'Errors in code: {}'.format(str(e).capitalize())}), 400

        # Check if the current deployment contains another scheduled execution
        if self._executions_scheduled.exists(current_execution['id']):
            return jsonify({'message': 'The current deployment contains an already scheduled execution.'}), 400

        # Calculate schedule
        if 'schedule_type' in data:
            schedule = self.__get_next_schedule(data['schedule_type'], data['schedule_value'], data.get('schedule_rules'))
            execution['scheduled'] = schedule['value']
            if schedule['error']:
                return jsonify({'message': schedule['error']}), 400

        # Check if selected environment contains any disabled servers
        if self._environments.is_disabled(user['id'], user['group_id'], execution['environment_id']):
            return jsonify({'message': 'The selected environment contains disabled servers.'}), 400

        # Set Execution Status
        if 'scheduled' in execution:
            execution['status'] = 'SCHEDULED'
            execution['start_execution'] = False
        else:
            execution['scheduled'] = None
            execution['start_execution'] = data['start_execution']
            if execution['start_execution']:
                execution['status'] = 'QUEUED'
            else:
                execution['status'] = 'CREATED'

        # Edit the execution
        if current_execution['status'] in ['CREATED','SCHEDULED']:
            self._executions.put(user['id'], execution)
            execution_id = current_execution['id']
            coins = user['coins']
        # Create a new execution
        else:
            # Check Coins
            if (user['coins'] - group['deployments_coins']) < 0:
                return jsonify({'message': 'Insufficient Coins'}), 400

            # Create a new Deployment
            execution['deployment_id'] = current_execution['deployment_id']
            execution['uri'] = str(uuid.uuid4())
            execution_id = self._executions.post(user['id'], execution)

            # Consume Coins
            self._users.consume_coins(user, group['deployments_coins'])
            coins = user['coins'] - group['deployments_coins']

        # Add Schedule to the current execution
        if execution['scheduled'] and data['schedule_type'] in ['daily','weekly','monthly']:
            schedule_rules = None
            if data['schedule_type'] in ['weekly','monthly']:
                rules = sorted([int(i) for i in data['schedule_rules']['rules']])
                schedule_rules = json.dumps({"rules": rules, "day": data['schedule_rules']['day']}) if data['schedule_type'] == 'monthly' else json.dumps({"rules": rules})
            self._executions_scheduled.post(execution_id, data['schedule_type'], data['schedule_value'], schedule_rules)
        else:
            self._executions_scheduled.delete(execution_id)

        if current_execution['status'] in ['CREATED','SCHEDULED'] and not execution['start_execution']:
            return jsonify({'message': 'Deployment edited', 'data': {'uri': execution['uri']}}), 200

        # Build Response Data
        response = { 'uri': execution['uri'], 'coins': coins }

        # Return Response
        return jsonify({'message': 'Deployment created', 'data': response}), 200

    def __start(self, user, data):
        # Check files path permissions
        if not self.__check_files_path():
            return jsonify({'message': 'No write permissions in the files folder'}), 400

        # Get current deployment
        execution = self._executions.get(data['uri'])

        # Check if deployment exists
        if len(execution) == 0:
            return jsonify({'message': 'This deployment does not exist.'}), 400
        execution = execution[0]

        # Check user privileges
        if user['disabled'] or (execution['mode'] == 'BASIC' and not user['deployments_basic']) or (execution['mode'] == 'PRO' and not user['deployments_pro']):
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Check deployment authority
        authority = self._deployments.getUser(execution['deployment_id'])
        if len(authority) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        authority = authority[0]
        if authority['id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Check if Deploy can be started
        if execution['status'] not in ['CREATED','SCHEDULED']:
            return jsonify({'message': 'This deployment cannot be started.'}), 400

        # Check environment exists
        environment = self._environments.get(user_id=user['id'], group_id=user['group_id'], environment_id=execution['environment_id'])
        if len(environment) == 0:
            return jsonify({'message': 'The selected environment does not exist in your inventory'}), 400

        # Check environment contains at least one server
        servers = self._servers.get_by_environment(user['id'], user['group_id'], execution['environment_id'])
        if len(servers) == 0:
            return jsonify({'message': 'The selected environment does not contain servers'}), 400

        # Check if selected environment contains any disabled servers
        if self._environments.is_disabled(user['id'], user['group_id'], execution['environment_id']):
            return jsonify({'message': 'The selected environment contains disabled servers.'}), 400

        # Get Group
        group = self._groups.get(group_id=user['group_id'])[0]

        # Get Deployment
        deployment = self._deployments.get(user_id=authority['id'], deployment_id=execution['deployment_id'])[0]

        # Build Meteor Execution
        meteor = {
            'id': execution['id'],
            'name': deployment['name'],
            'release': deployment['release'],
            'user_id': user['id'],
            'username': user['username'],
            'group_id': user['group_id'],
            'environment_id': execution['environment_id'],
            'environment_name': execution['environment_name'],
            'mode': execution['mode'],
            'method': execution['method'],
            'queries': execution['queries'],
            'databases': execution['databases'],
            'code': execution['code'],
            'url': execution['url'],
            'uri': execution['uri'],
            'execution_threads': group['deployments_execution_threads'],
            'execution_timeout': group['deployments_execution_timeout']
        }

        # Update Execution Status
        self._executions.updateStatus(execution['id'], 'QUEUED')

        # Return Successful Message
        return jsonify({'message': 'Deployment started'}), 200

    def __stop(self, user, data):
        # Check params
        if 'uri' not in data:
            return jsonify({'message': 'Uri parameter is required'}), 400
        if 'mode' not in data or data['mode'] not in ['graceful','forceful']:
            return jsonify({'message': 'Mode parameter is required'}), 400

        # Get current deployment
        execution = self._executions.get(data['uri'])

        # Check if deployment exists
        if len(execution) == 0:
            return jsonify({'message': 'This deployment does not exist.'}), 400
        execution = execution[0]

        # Check user privileges
        if user['disabled'] or (execution['mode'] == 'BASIC' and not user['deployments_basic']) or (execution['mode'] == 'PRO' and not user['deployments_pro']):
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Check deployment authority
        authority = self._deployments.getUser(execution['deployment_id'])
        if len(authority) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        authority = authority[0]
        if authority['id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Remove the deployment from the queue & Get PID
        self._executions.updateStatus(execution['id'], 'STOPPED', True)

        # Stop the execution if the deployment has already started
        if execution['pid'] is not None:
            self._executions.updateStatus(execution['id'], 'STOPPING', data['mode'])
            try:
                if data['mode'] == 'graceful':
                    os.kill(execution['pid'], signal.SIGINT)
                elif data['mode'] == 'forceful':
                    os.kill(execution['pid'], signal.SIGTERM)
            except OSError:
                pass
            return jsonify({'message': 'Stopping the execution...'}), 200
        return jsonify({'message': 'Execution removed from the queue'}), 200

    def __shared(self, user, data):
        # Get current deployment
        execution = self._executions.get(data['uri'])

        # Check if deployment exists
        if len(execution) == 0:
            return jsonify({'message': 'This deployment does not exist.'}), 400
        execution = execution[0]

        # Check user privileges
        if user['disabled'] or (execution['mode'] == 'BASIC' and not user['deployments_basic']) or (execution['mode'] == 'PRO' and not user['deployments_pro']):
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Check deployment authority
        authority = self._deployments.getUser(execution['deployment_id'])
        if len(authority) == 0:
            return jsonify({'message': 'This deployment does not exist'}), 400
        authority = authority[0]
        if authority['id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Change deployment shared value
        self._deployments.setShared(execution['deployment_id'], data['shared'])

        # Return message
        if data['shared']:
            return jsonify({'message': 'This deployment is now shared'}), 200
        return jsonify({'message': 'This deployment is now private'}), 200

    ####################
    # Internal Methods #
    ####################
    def __get_next_schedule(self, schedule_type, schedule_value, schedule_rules=None):
        schedule = {"value": None, "error": None}
        now = datetime.strptime(datetime.utcnow().strftime("%Y-%m-%d %H:%M"), '%Y-%m-%d %H:%M')
        if schedule_type == 'one_time':
            schedule_formatted = datetime.strptime(schedule_value, '%Y-%m-%d %H:%M')
            if schedule_formatted < now:
                schedule['error'] = 'The scheduled date cannot be in the past'
            else:
                schedule['value'] = schedule_value
        elif schedule_type == 'daily':
            now_formatted = datetime.strptime(datetime.utcnow().strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M")
            schedule_formatted = datetime.strptime(datetime.utcnow().strftime("%Y-%m-%d") + ' ' + schedule_value, '%Y-%m-%d %H:%M')
            schedule['value'] = schedule_formatted.strftime("%Y-%m-%d %H:%M:%S") if schedule_formatted >= now_formatted else schedule_formatted + timedelta(days=1)
        elif schedule_type == 'weekly':
            if len(schedule_rules['rules']) == 0:
                schedule['error'] = 'Enter at least one day of the week'
            else:
                schedule_formatted = datetime.strptime(datetime.utcnow().strftime("%Y-%m-%d") + ' ' + schedule_value, '%Y-%m-%d %H:%M')
                schedule_rules = sorted([int(i) for i in schedule_rules['rules']])
                start_days = [schedule_formatted + timedelta(days=i - schedule_formatted.isoweekday()) for i in schedule_rules]
                start_days = [i if i >= now else i + timedelta(weeks=1) for i in start_days]
                schedule['value'] = sorted(start_days)[0].strftime("%Y-%m-%d %H:%M:%S")
        elif schedule_type == 'monthly':
            if len(schedule_rules['rules']) == 0:
                schedule['error'] = 'Enter at least one month'
            else:
                schedule_formatted = datetime.strptime(datetime.utcnow().strftime("%Y-%m-%d") + ' ' + schedule_value, '%Y-%m-%d %H:%M')
                schedule_rules = {"rules": sorted([int(i) for i in schedule_rules['rules']]), "day": schedule_rules['day']}
                start_days = [datetime.strptime(f"{schedule_formatted.year}-{('0'+str(i))[-2:]}-01", "%Y-%m-%d") for i in schedule_rules['rules']]
                start_days = [i if schedule_rules['day'] == 'first' else i.replace(day=calendar.monthrange(i.year, i.month)[1]) for i in start_days]
                start_days = [i if i >= now else i.replace(year=i.year + 1) for i in start_days]
                start_days = [i if schedule_rules['day'] == 'first' else i.replace(day=calendar.monthrange(i.year, i.month)[1]) for i in start_days]
                schedule['value'] = sorted(start_days)[0].strftime("%Y-%m-%d %H:%M:%S")
        return schedule

    def __check_files_path(self):
        # Get Path
        bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        base_path = os.path.realpath(os.path.dirname(sys.executable)) if bin else os.path.realpath(os.path.dirname(sys.argv[0]))
        path = f"{base_path}/files"

        # Check Write permissions in path
        while not os.path.exists(path) and path != '/':
            path = os.path.normpath(os.path.join(path, os.pardir))
        if os.access(path, os.X_OK | os.W_OK):
            return True
        return False

    def __secure_code(self, code):
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.__secure_code2, args=(code,q))
        p.start()
        p.join(3)
        if p.is_alive():
            p.terminate()
            raise Exception('Timeout exceeded.')
        result = q.get_nowait()
        if result != 'OK':
            raise Exception(result)

    def __secure_code2(self, code, queue):
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        secure_code = f"""import builtins
import importlib

def import2(name, globals=None, locals=None, fromlist=(), level=0):
    global importlib
    whitelist = ['string','re','unicodedata','datetime','zoneinfo','calendar','collections','copy','numbers','math','cmath','decimal','fractions','random','statistics','fnmatch','secrets','csv','time','json','json.decoder','uuid','locale','boto3','hashlib','itertools']
    frommodule = globals['__name__'] if globals else None
    if frommodule is None or frommodule == '__main__':
        if name not in whitelist:
            raise Exception(f"Module '{{name}}' is restricted.")
    else:
        split = frommodule.split('.')
        if len(split) > 1:
            if split[0] not in whitelist:
                raise Exception(f"Module '{{split[0]}}' is restricted.")
        elif frommodule not in whitelist:
            raise Exception(f"Module '{{frommodule}}' is restricted.")
    return importlib.__import__(name, globals, locals, fromlist, level)

def exec2(*args, **kwargs):
    raise Exception("Method exec() is restricted.")

def open2(*args, **kwargs):
    raise Exception("Method open() is restricted.")

builtins.__import__ = import2
builtins.exec = exec2
builtins.open = open2\n\n{code}\nblueprint()"""
        try:
            exec(secure_code, {'__name__':'__main__'}, {})
            queue.put('OK')
        except SyntaxError as e:
            queue.put(e.args[0] + ' (line ' + str(e.lineno-29) + ')')
        except Exception as e:
            queue.put(str(e))
