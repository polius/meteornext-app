import os
import json
import boto3
import tarfile
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.deployments

class Deployments:
    def __init__(self, credentials):
        # Init models
        self._users = models.admin.users.Users(credentials)
        self._deployments = models.deployments.deployments.Deployments(credentials)

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
            return jsonify({'data': self._deployments.get()}), 200

        @admin_deployments_blueprint.route('/admin/deployments/search', methods=['GET'])
        @jwt_required
        def admin_deployments_search_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Deployments
            return jsonify({'data': self._deployments.get(search=json.loads(request.args['data']))}), 200

        return admin_deployments_blueprint

