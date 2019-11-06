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

    def blueprint(self):
        # Init blueprint
        admin_deployments_blueprint = Blueprint('admin_deployments', __name__, template_folder='admin_deployments')

        @admin_deployments_blueprint.route('/admin/deployments', methods=['GET'])
        @jwt_required
        def admin_deployments_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Deployments
            return self.get()

        return admin_deployments_blueprint

    def get(self):
        return jsonify({'data': self._deployments.get()}), 200
