import os
import json
import botocore
import boto3
import tarfile
import shutil
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.releases
import models.deployments.deployments
import models.deployments.deployments_basic
import models.deployments.deployments_pro
import models.deployments.deployments_queued
import models.deployments.deployments_finished
import models.admin.settings
import routes.deployments.meteor

class Deployments:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._releases = models.deployments.releases.Releases(sql)
        self._deployments = models.deployments.deployments.Deployments(sql)
        self._deployments_basic = models.deployments.deployments_basic.Deployments_Basic(sql)
        self._deployments_pro = models.deployments.deployments_pro.Deployments_Pro(sql)
        self._deployments_queued = models.deployments.deployments_queued.Deployments_Queued(sql)
        self._deployments_finished = models.deployments.deployments_finished.Deployments_Finished(sql)
        self._settings = models.admin.settings.Settings(sql)

        # Init meteor
        self._meteor = routes.deployments.meteor.Meteor(app, sql)

    def blueprint(self):
        # Init blueprint
        deployments_blueprint = Blueprint('deployments', __name__, template_folder='deployments')

        @deployments_blueprint.route('/deployments', methods=['GET','PUT'])
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
                return self.__get(user['id'])
            elif request.method == 'PUT':
                return self.__put(user['id'], deployment_json)

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

            if not results['public'] and int(results['user_id']) != user['id'] and not user['admin']:
                return jsonify({'title': 'Authorized Access Only', 'description': 'The URL provided is private' }), 400

            # Get Logs Settings
            logs = json.loads(self._settings.get(setting_name='LOGS')[0]['value'])
            
            # Get Execution Results File
            if results['engine'] == 'local':
                execution_results = '{}/{}'.format(logs['local']['path'], uri)
                # Check if exists
                if not os.path.exists(execution_results + '.js') and not os.path.exists(execution_results + '.tar.gz'):
                    return jsonify({'title': 'Deployment Expired', 'description': 'This deployment no longer exists' }), 400
                elif not os.path.exists(execution_results + '.js'):
                    tf = tarfile.open("{}.tar.gz".format(execution_results), mode="r")
                    tf.extract("./meteor.js", path=execution_results)
                    os.rename('{}/meteor.js'.format(execution_results), '{}.js'.format(execution_results))
                    shutil.rmtree(execution_results, ignore_errors=True)

                return send_from_directory(logs['local']['path'], uri + '.js')

            elif results['engine'] == 'amazon_s3':
                # Check Amazon S3 credentials are setup
                if 'aws_access_key' not in logs['amazon_s3']:
                    return jsonify({'title': 'Can\'t connect to Amazon S3', 'description': 'Check the provided Amazon S3 credentials' }), 400
                session = boto3.Session(
                    aws_access_key_id=logs['amazon_s3']['aws_access_key'],
                    aws_secret_access_key=logs['amazon_s3']['aws_secret_access_key'],
                    region_name=logs['amazon_s3']['region_name']
                )
                try:
                    s3 = session.resource('s3')
                    obj = s3.meta.client.get_object(Bucket=logs['amazon_s3']['bucket_name'], Key='results/{}.js'.format(uri))
                    return jsonify(obj['Body'].read().decode('utf-8')), 200
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        return jsonify({'title': 'Deployment Expired', 'description': 'This deployment no longer exists in Amazon S3' }), 400
                    return jsonify({'title': 'Can\'t connect to Amazon S3', 'description': 'Check the provided Amazon S3 credentials' }), 400
                except Exception:
                    return jsonify({'title': 'Can\'t connect to Amazon S3', 'description': 'Check the provided Amazon S3 credentials' }), 400

        return deployments_blueprint

    ###################
    # Recurring Tasks #
    ###################
    def check_queued(self):
        # Notify finished queue deployments and remove it from queue
        finished = self._deployments_queued.getFinished()
        for i in finished:
            if i['scheduled']:
                self._deployments_finished.post({"mode": i['execution_mode'], "id": i['execution_id']})
        if len(finished) > 0:
            ids = ','.join([str(i['id']) for i in finished])
            self._deployments_queued.delete(ids)

        # Populate new queued deployments
        self._deployments_queued.build()

        # Build dictionary of executions
        executions_raw = self._deployments_queued.getNext()
        groups = {}
        executions_ids = {'basic':[],'pro':[]}
        executions = {'basic':[],'pro':[]}
        for i in executions_raw:
            concurrent = groups.get(i['group'], 0)
            if concurrent < i['concurrent']:
                groups[i['group']] = concurrent + 1
                if i['status'] == 'QUEUED':
                    executions_ids[i['mode']].append(i['id'])

        if len(executions_ids['basic']) > 0:
            basic = self._deployments_basic.getExecutionsN(','.join(str(i) for i in executions_ids['basic']))
            for b in basic:
                for e in executions_ids['basic']:
                    if b['execution_id'] == e:
                        executions['basic'].append(b)
                        break
        if len(executions_ids['pro']) > 0:
            pro = self._deployments_pro.getExecutionsN(','.join(str(i) for i in executions_ids['pro']))
            for p in pro:
                for e in executions_ids['pro']:
                    if p['execution_id'] == e:
                        executions['pro'].append(p)
                        break

        # Start Queued Executions
        for basic in executions['basic']:
            self._deployments_basic.updateStatus(basic['execution_id'], 'STARTING', True)
            self._meteor.execute(basic)
        for pro in executions['pro']:
            self._deployments_pro.updateStatus(pro['execution_id'], 'STARTING', True)
            self._meteor.execute(pro)

    ####################
    # Internal Methods #
    ####################
    def __get(self, user_id):
        return jsonify({'deployments': self._deployments.get(user_id), 'releases': self._releases.get(user_id)}), 200

    def __put(self, user_id, data):
        if data['put'] == 'name':
            self._deployments.putName(user_id, data)
        elif data['put'] == 'release':
            self._deployments.putRelease(user_id, data)
        return jsonify({'message': 'Deployment edited successfully'}), 200
