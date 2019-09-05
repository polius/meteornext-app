import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Pro:
    def __init__(self, credentials):
        self._credentials = credentials

        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._deployments = imp.load_source('basic', '{}/models/deployments/deployments.py'.format(credentials['path'])).Deployments(credentials)
        self._deployments_pro = imp.load_source('pro', '{}/models/deployments/deployments_pro.py'.format(credentials['path'])).Deployments_Pro(credentials)

    def blueprint(self):
        # Init blueprint
        deployments_pro_blueprint = Blueprint('deployments_pro', __name__, template_folder='deployments_pro')

        @deployments_pro_blueprint.route('/deployments/pro', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def deployments_pro_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_enable']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            deployment_json = request.get_json()

            if request.method == 'POST':
                return self.post(user['id'], deployment_json)

        @deployments_pro_blueprint.route('/deployments/pro/code', methods=['GET'])
        @jwt_required
        def deployments_pro_code():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Retrieve code
            with open('{}/../apps/Meteor/app/query_execution.py'.format(self._credentials['path'])) as file_open:
                return jsonify({'data': file_open.read()}), 200

        return deployments_pro_blueprint

    def post(self, user_id, data):
        # Check if 'execution_threads' is a digit between 2-10
        if data['execution'] == 'PARALLEL':
            if not str(data['execution_threads']).isdigit() or int(data['execution_threads']) < 2 or int(data['execution_threads']) > 10:
                return jsonify({'message': "The 'Threads' field should be an integer between 2-10"}), 400

        data['id'] = self._deployments.post(user_id, data)
        self._deployments_pro.post(data)
        return jsonify({'message': 'Deployment created successfully'}), 200
