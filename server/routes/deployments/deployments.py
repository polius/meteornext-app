import os
import imp
import json
import boto3
import tarfile
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Deployments:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._deployments = imp.load_source('deployments', '{}/models/deployments/deployments.py'.format(credentials['path'])).Deployments(credentials)
        self._settings = imp.load_source('settings', '{}/models/admin/settings.py'.format(credentials['path'])).Settings(credentials)

    def blueprint(self):
        # Init blueprint
        deployments_blueprint = Blueprint('deployments', __name__, template_folder='deployments')

        @deployments_blueprint.route('/deployments', methods=['GET','PUT','DELETE'])
        @jwt_required
        def deployments_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
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
                return jsonify({'message': 'This execution does not currently exist'}), 400
            else:
                results = results[0]

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check if Result is Public
            if not results['public'] and int(results['user_id']) != user['id']:
                return jsonify({'message': 'This results are private'}), 400

            # Get Logs Settings
            logs = json.loads(self._settings.get(setting_name='LOGS')[0]['value'])
            
            # Get Execution Results File
            if results['engine'] == 'local':
                results_directory = '{}{}.{}'.format(logs['local'], results['deployment_id'], results['execution_id'])
                results_name = '{}.js'.format(uri)
                if not os.path.exists('{}/{}'.format(results_directory, results_name)):
                    # Get compressed file name
                    for f in os.listdir(results_directory):
                        if f.endswith('.tar.gz'):
                            break

                    # Extract results file name
                    tf = tarfile.open("{}/{}".format(results_directory, f), mode="r")
                    tf.extract("./meteor.js", path=results_directory)

                    # Rename results
                    os.rename('{}/meteor.js'.format(results_directory), '{}/{}.js'.format(results_directory, uri))

                return send_from_directory(results_directory, results_name)

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
                    return jsonify({'message': 'This results no longer exists'}), 400

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
