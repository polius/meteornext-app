import os
import json
import boto3
import tarfile
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.deployments
import routes.admin.settings

class Deployments:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._deployments = models.deployments.deployments.Deployments(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        admin_deployments_blueprint = Blueprint('admin_deployments', __name__, template_folder='admin_deployments')

        @admin_deployments_blueprint.route('/admin/deployments', methods=['GET'])
        @jwt_required
        def admin_deployments_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Deployments
            return jsonify({'data': self._deployments.get()}), 200

        @admin_deployments_blueprint.route('/admin/deployments/filter', methods=['GET'])
        @jwt_required
        def admin_deployments_search_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Deployments
            return jsonify({'data': self._deployments.get(search=json.loads(request.args['data']))}), 200

        return admin_deployments_blueprint
