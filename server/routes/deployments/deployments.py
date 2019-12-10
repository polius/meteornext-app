import os
import json
import boto3
import tarfile
import shutil
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.deployments
import models.admin.settings

class Deployments:
    def __init__(self, app, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._deployments = models.deployments.deployments.Deployments(sql)
        self._settings = models.admin.settings.Settings(sql)

    def blueprint(self):
        # Init blueprint
        deployments_blueprint = Blueprint('deployments', __name__, template_folder='deployments')

        @deployments_blueprint.route('/deployments', methods=['GET','PUT','DELETE'])
        @jwt_required
        def deployments_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['id'])
            elif request.method == 'PUT':
                return self.put(user['id'], deployment_json)
            elif request.method == 'DELETE':
                return self.delete(user['id'], deployment_json)

        @deployments_blueprint.route('/deployments/results', methods=['GET'])
        @jwt_required
        def deployments_results_method():
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

            if not results['public'] and int(results['user_id']) != user['id']:
                return jsonify({'title': 'Authorized Access Only', 'description': 'The URL provided is private' }), 400

            # Get Logs Settings
            logs = json.loads(self._settings.get(setting_name='LOGS')[0]['value'])
            
            # Get Execution Results File
            if results['engine'] == 'local':
                execution_results = '{}/{}'.format(logs['local']['path'], uri)
                # Check if exists
                if not os.path.exists(execution_results + '.js') and not os.path.exists(execution_results + '.tar.gz'):
                    return jsonify({'title': 'Deployment Expired', 'description': 'This deployment has expired' }), 400
                elif not os.path.exists(execution_results + '.js'):
                    tf = tarfile.open("{}.tar.gz".format(execution_results), mode="r")
                    tf.extract("./meteor.js", path=execution_results)
                    os.rename('{}/meteor.js'.format(execution_results), '{}.js'.format(execution_results))
                    shutil.rmtree(execution_results, ignore_errors=True)

                return send_from_directory(logs['local']['path'], uri + '.js')

            elif results['engine'] == 'amazon_s3':
                session = boto3.Session(
                    aws_access_key_id=logs['amazon_s3']['aws_access_key'],
                    aws_secret_access_key=logs['amazon_s3']['aws_secret_access_key'],
                    region_name=logs['amazon_s3']['region_name']
                )
                s3 = session.resource('s3')
                try:
                    obj = s3.meta.client.get_object(Bucket=logs['amazon_s3']['bucket_name'], Key='results/{}.js'.format(uri))
                    return jsonify(obj['Body'].read().decode('utf-8')), 200
                except Exception:
                    return jsonify({'title': 'Deployment Expired', 'description': 'This deployment has expired' }), 400

        return deployments_blueprint

    def get(self, user_id):
        return jsonify({'data': self._deployments.get(user_id)}), 200

    def put(self, user_id, data):
        if not self._deployments.exist(user_id, data):
            return jsonify({'message': 'This deployment does not exist'}), 400
        else:
            self._deployments.put(user_id, data)
            return jsonify({'message': 'Deployment edited successfully'}), 200

    def delete(self, user_id, data):
        for deploy in data:
            self._deployments.delete(user_id, deploy)
        return jsonify({'message': 'Selected deployments deleted successfully'}), 200
