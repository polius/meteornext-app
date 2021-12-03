import os
import sys
import uuid
import json
import gzip
import boto3
import signal
import subprocess
import botocore
import datetime
import unicodedata
import multiprocessing
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.admin.groups
import models.deployments.releases
import models.deployments.deployments
import models.deployments.executions
import models.deployments.deployments_queued
import models.deployments.deployments_finished
import models.admin.settings
import models.inventory.environments
import models.notifications
import routes.deployments.meteor

class Deployments:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._releases = models.deployments.releases.Releases(sql)
        self._deployments = models.deployments.deployments.Deployments(sql)
        self._executions = models.deployments.executions.Executions(sql)
        self._deployments_queued = models.deployments.deployments_queued.Deployments_Queued(sql)
        self._deployments_finished = models.deployments.deployments_finished.Deployments_Finished(sql)
        self._settings = models.admin.settings.Settings(sql, license)
        self._environments = models.inventory.environments.Environments(sql, license)
        self._notifications = models.notifications.Notifications(sql)

        # Init meteor
        self._meteor = routes.deployments.meteor.Meteor(app, sql, license)

    def blueprint(self):
        # Init blueprint
        deployments_blueprint = Blueprint('deployments', __name__, template_folder='deployments')

        @deployments_blueprint.route('/deployments', methods=['GET','POST','PUT'])
        @jwt_required()
        def deployments_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['deployments_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            if request.method == 'GET':
                return self.__get(user)
            elif request.method == 'POST':
                return self.__post(user, deployment_json)
            elif request.method == 'PUT':
                return self.__put(user, deployment_json)

        @deployments_blueprint.route('/deployments/blueprint', methods=['GET'])
        @jwt_required()
        def deployments_code():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Retrieve blueprint
            code_path = os.path.dirname(os.path.realpath(__file__))
            with open('{}/blueprint.py'.format(code_path)) as file_open:
                return jsonify({'data': file_open.read()}), 200

        @deployments_blueprint.route('/deployments/start', methods=['POST'])
        @jwt_required()
        def deployments_start():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            deployment_json = request.get_json()

            # Start Deployment
            return self.__start(user, deployment_json)

        @deployments_blueprint.route('/deployments/stop', methods=['POST'])
        @jwt_required()
        def deployments_stop():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            deployment_json = request.get_json()

            # Stop Deployment
            return self.__stop(user, deployment_json)

        @deployments_blueprint.route('/deployments/results', methods=['GET'])
        @jwt_required()
        def deployments_results_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get Request Json URI
            uri = request.args.get('uri')

            # Get Execution Results Metadata
            results = self._deployments.getResults(uri)

            if len(results) == 0:
                return jsonify({'title': 'Unknown deployment', 'description': 'This deployment does not currently exist' }), 400
            else:
                results = results[0]

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if not results['shared'] and int(results['user_id']) != user['id'] and not user['admin']:
                return jsonify({'title': 'Authorized Access Only', 'description': 'The URL provided is private' }), 400

            # Get Files Settings
            files = json.loads(self._settings.get(setting_name='FILES'))
            
            # Get Execution Results File
            if results['logs'] == 'local':
                deployments_path = os.path.join(files['local']['path'], 'deployments', uri)
                results_folder = os.path.join(files['local']['path'], 'results')
                results_path = os.path.join(files['local']['path'], 'results', uri)
                # Check if exists
                if not os.path.exists(deployments_path + '.tar.gz'):
                    return jsonify({'title': 'Deployment Expired', 'description': 'This deployment no longer exists' }), 400
                elif not os.path.exists(results_path + '.json'):
                    if not os.path.exists(results_folder):
                        os.makedirs(results_folder)
                    subprocess.run(f"tar Oxzf '{deployments_path}'.tar.gz './meteor.json' > {results_path}.json", shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return send_from_directory(results_folder, uri + '.json')

            elif results['logs'] == 'amazon_s3':
                # Check Amazon S3 credentials are setup
                if 'aws_access_key' not in files['amazon_s3']:
                    return jsonify({'title': 'Can\'t connect to Amazon S3', 'description': 'Check the provided Amazon S3 credentials' }), 400
                session = boto3.Session(
                    aws_access_key_id=files['amazon_s3']['aws_access_key'],
                    aws_secret_access_key=files['amazon_s3']['aws_secret_access_key'],
                    region_name=files['amazon_s3']['region']
                )
                try:
                    s3 = session.resource('s3')
                    obj = s3.meta.client.get_object(Bucket=files['amazon_s3']['bucket'], Key='results/{}.json.gz'.format(uri))
                    with gzip.open(obj['Body'], 'rb') as fopen:
                        return jsonify(json.load(fopen)), 200
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        return jsonify({'title': 'Deployment Expired', 'description': 'This deployment no longer exists in Amazon S3' }), 400
                    return jsonify({'title': 'Can\'t connect to Amazon S3', 'description': 'Check the provided Amazon S3 credentials' }), 400
                except Exception:
                    return jsonify({'title': 'Can\'t connect to Amazon S3', 'description': 'Check the provided Amazon S3 credentials' }), 400

        @deployments_blueprint.route('/deployments/executions', methods=['GET'])
        @jwt_required()
        def deployments_executions():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get args
            data = request.args

            # Get executions
            return self.__get_executions(user, data)

        @deployments_blueprint.route('/deployments/shared', methods=['POST'])
        @jwt_required()
        def deployments_shared():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            deployment_json = request.get_json()

            # Set Deployment Shared
            return self.__shared(user, deployment_json)

        return deployments_blueprint

    ###################
    # Recurring Tasks #
    ###################
    def check_queued(self):
        # Notify finished queue deployments and remove it from queue
        finished = self._deployments_queued.getFinished()
        for i in finished:
            if i['scheduled']:
                self._deployments_finished.post(i['execution_id'])
        if len(finished) > 0:
            ids = ','.join([str(i['id']) for i in finished])
            self._deployments_queued.delete(ids)

        # Populate new queued deployments
        self._deployments_queued.build()

        # Build dictionary of executions
        executions_raw = self._deployments_queued.getNext()
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
        finished = self._deployments_finished.get()

        for f in finished:
            # Create notifications
            notification = {'category': 'deployment'}
            notification['name'] = '{} has finished'.format(f['name'])
            notification['status'] = 'ERROR' if f['status'] == 'FAILED' else f['status']
            notification['data'] = '{{"id": "{}"}}'.format(f['uri'])
            self._notifications.post(f['user_id'], notification)

            # Clean finished deployments
            self._deployments_finished.delete(f['id'])

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
                    # Add Deployment to be Tracked
                    self._deployments_finished.post(s['id'])

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
        environments = [{"id": i['id'], "name": i['name'], "shared": i['shared']} for i in self._environments.get(user['id'], user['group_id'])]

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
        elif authority[0]['id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Get deployment executions
        executions = self._deployments.getExecutions(execution['deployment_id'])
        return jsonify({'data': executions }), 200

    def __post(self, user, data):
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
            'scheduled': data['scheduled'],
            'url': data['url'],
            'uri': str(uuid.uuid4()),
            'start_execution': data['start_execution'],
        }

        # Check Coins
        group = self._groups.get(group_id=user['group_id'])[0]
        if (user['coins'] - group['coins_execution']) < 0:
            return jsonify({'message': 'Insufficient Coins'}), 400

        # Check environment authority
        environment = self._environments.get(user_id=user['id'], group_id=user['group_id'], environment_id=execution['environment_id'])
        if len(environment) == 0:
            return jsonify({'message': 'The environment does not exist'}), 400
        environment = environment[0]

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

        # Check scheduled date
        if execution['scheduled'] is not None:
            execution['start_execution'] = False
            if datetime.datetime.strptime(execution['scheduled'], '%Y-%m-%d %H:%M:%S') < datetime.datetime.now():
                return jsonify({'message': 'The scheduled date cannot be in the past'}), 400

        # Check if selected environment contains any disabled servers
        if self._environments.is_disabled(user['id'], user['group_id'], execution['environment_id']):
            return jsonify({'message': 'The selected environment contains disabled servers.'}), 400

        # Set Deployment Status
        if execution['scheduled'] is not None:
            execution['status'] = 'SCHEDULED'
            execution['start_execution'] = False
            if datetime.datetime.strptime(execution['scheduled'], '%Y-%m-%d %H:%M:%S') < datetime.datetime.now():
                return jsonify({'message': 'The scheduled date cannot be in the past'}), 400
        elif execution['start_execution']:
            execution['status'] = 'QUEUED' if group['deployments_execution_concurrent'] else 'STARTING'
        else:
            execution['status'] = 'CREATED'

        # Create deployment to the DB
        execution['deployment_id'] = self._deployments.post(user['id'], deployment)
        execution_id = self._executions.post(user['id'], execution)

        # Consume Coins
        self._users.consume_coins(user, group['coins_execution'])

        # Build Response Data
        response = {'id': execution_id, 'coins': user['coins'] - group['coins_execution'] }

        if execution['start_execution'] and not group['deployments_execution_concurrent']:
            # Build Meteor Execution
            meteor = {
                'id': execution_id,
                'user_id': user['id'],
                'username': user['username'],
                'group_id': group['id'],
                'environment_id': environment['id'],
                'environment_name': environment['name'],
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

            # Start Meteor Execution
            self._meteor.execute(meteor)
            return jsonify({'message': 'Deployment Launched', 'data': response}), 200

        return jsonify({'message': 'Deployment created successfully', 'data': response}), 200

    def __put(self, user, data):
        # Edit Metadata
        if 'name' in data.keys():
            self._deployments.putName(user, data)
            return jsonify({'message': 'Deployment edited successfully'}), 200
        elif 'release' in data.keys():
            self._deployments.putRelease(user, data)
            return jsonify({'message': 'Deployment edited successfully'}), 200

        # Get Data
        execution = {
            'environment_id': data['environment'],
            'mode': data['mode'],
            'databases': data.get('databases'),
            'queries': data.get('queries'),
            'code': data.get('code'),
            'method': data['method'],
            'scheduled': data['scheduled'],
            'url': data['url'],
            'uri': data['uri'],
            'start_execution': data['start_execution'],
        }

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

        # Get deployment authority group
        group = self._groups.get(group_id=authority['group_id'])[0]

        # Check environment authority
        environment = self._environments.get(user_id=authority['id'], group_id=authority['group_id'], environment_id=data['environment'])
        if len(environment) == 0:
            return jsonify({'message': 'The environment does not exist'}), 400
        environment = environment[0]

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

        # Check scheduled date
        if execution['scheduled'] is not None:
            execution['start_execution'] = False
            if datetime.datetime.strptime(execution['scheduled'], '%Y-%m-%d %H:%M:%S') < datetime.datetime.now():
                return jsonify({'message': 'The scheduled date cannot be in the past'}), 400

        # Check if selected environment contains any disabled servers
        if self._environments.is_disabled(user['id'], user['group_id'], execution['environment_id']):
            return jsonify({'message': 'The selected environment contains disabled servers.'}), 400

        # Set Execution Status
        if execution['scheduled'] is not None:
            execution['status'] = 'SCHEDULED'
        elif execution['start_execution']:
            execution['status'] = 'QUEUED' if group['deployments_execution_concurrent'] else 'STARTING'
        else:
            execution['status'] = 'CREATED'

        # Edit the execution
        if current_execution['status'] in ['CREATED','SCHEDULED']:
            self._executions.put(user['id'], execution)
            execution_id = execution['id']
            coins = user['coins']
            if not execution['start_execution']:
                return jsonify({'message': 'Deployment edited successfully', 'data': {'id': execution_id}}), 200

        # Create a new execution
        else:
            # Check Coins
            if not (authority['id'] != user['id'] and user['admin']) and (user['coins'] - group['coins_execution']) < 0:
                return jsonify({'message': 'Insufficient Coins'}), 400

            # Create a new Deployment
            execution['deployment_id'] = current_execution['deployment_id']
            execution['uri'] = str(uuid.uuid4())
            execution_id = self._executions.post(user['id'], execution)

            # Consume Coins
            if authority['id'] != user['id'] and user['admin']:
                coins = user['coins']
            else:
                self._users.consume_coins(user, group['coins_execution'])
                coins = user['coins'] - group['coins_execution']

        # Build Response Data
        response = { 'uri': execution['uri'], 'coins': coins }

        if execution['start_execution'] and not group['deployments_execution_concurrent']:
            # Build Meteor Execution
            meteor = {
                'id': execution_id,
                'user_id': authority['id'],
                'username': user['username'],
                'group_id': authority['group_id'],
                'environment_id': environment['id'],
                'environment_name': environment['name'],
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

            # Start Meteor Execution
            self._meteor.execute(meteor)
            return jsonify({'message': 'Deployment Launched', 'data': response}), 200

        return jsonify({'message': 'Deployment created successfully', 'data': response}), 200

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

        # Check if selected environment contains any disabled servers
        if self._environments.is_disabled(user['id'], user['group_id'], execution['environment_id']):
            return jsonify({'message': 'The selected environment contains disabled servers.'}), 400

        # Get Group Authority
        group = self._groups.get(group_id=authority['group_id'])[0]

        # Build Meteor Execution
        meteor = {
            'id': execution['id'],
            'user_id': authority['id'],
            'username': user['username'],
            'group_id': authority['group_id'],
            'environment_id': execution['environment_id'],
            'environment_name': execution['environment_name'],
            'mode': execution['mode'],
            'method': execution['method'],
            'queries': execution['queries'],
            'databases': execution['databases'],
            'code': execution['code'],
            'url': execution['url'],
            'execution_threads': group['deployments_execution_threads'],
            'execution_timeout': group['deployments_execution_timeout']
        }

        # Update Execution Status
        status = 'STARTING' if not group['deployments_execution_concurrent'] else 'QUEUED'
        self._executions.updateStatus(execution['id'], status)

        # Start Meteor Execution
        if not group['deployments_execution_concurrent']:
            self._meteor.execute(meteor)

        # Build Response Data
        response = {'id': execution['id']}

        # Return Successful Message
        return jsonify({'data': response, 'message': 'Deployment Launched'}), 200

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
        self._executions.setShared(execution['id'], data['shared'])
        return jsonify({'message': 'Success'}), 200

    ####################
    # Internal Methods #
    ####################
    def __check_files_path(self):
        files_path = json.loads(self._settings.get(setting_name='FILES'))['local']['path']
        return self.__check_local_path(files_path)

    def __check_local_path(self, path):
        while not os.path.exists(path) and path != '/':
            path = os.path.normpath(os.path.join(path, os.pardir))
        if os.access(path, os.X_OK | os.W_OK):
            return True
        return False

    def __secure_code(self, code):
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.__secure_code2, args=(code,q))
        p.daemon = True
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
    whitelist = ['string','re','unicodedata','datetime','zoneinfo','calendar','collections','copy','numbers','math','cmath','decimal','fractions','random','statistics','fnmatch','secrets','csv','time','json','json.decoder','uuid','locale','boto3','hashlib']
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
