import os
import json
import boto3
import tarfile
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.admin.deployments
import models.deployments.releases
import routes.admin.settings

class Deployments:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._deployments = models.admin.deployments.Deployments(sql)
        self._releases = models.deployments.releases.Releases(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        admin_deployments_blueprint = Blueprint('admin_deployments', __name__, template_folder='admin_deployments')

        @admin_deployments_blueprint.route('/admin/deployments', methods=['GET','PUT'])
        @jwt_required()
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

            # Get Request Json
            deployment_json = request.get_json()

            if request.method == 'GET':
                # Get Deployments
                dfilter = json.loads(request.args['filter']) if 'filter' in request.args else None
                dsort = json.loads(request.args['sort']) if 'sort' in request.args else None
                deployments = self._deployments.get(dfilter, dsort)
                users_list = self._deployments.get_users_list()
                return jsonify({'deployments': deployments, 'users_list': users_list}), 200
            elif request.method == 'PUT':
                if deployment_json['put'] == 'name':
                    self._deployments.put_name(deployment_json['user_id'], deployment_json)
                elif deployment_json['put'] == 'release':
                    self._deployments.put_release(deployment_json['user_id'], deployment_json)
                return jsonify({'message': 'Deployment edited successfully'}), 200

        @admin_deployments_blueprint.route('/admin/deployments/releases', methods=['GET'])
        @jwt_required()
        def admin_deployments_releases_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Releases
            return jsonify({'releases': self._releases.getActive(user_id=request.args['user_id'])}), 200

        @admin_deployments_blueprint.route('/admin/deployments/filter', methods=['GET'])
        @jwt_required()
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
