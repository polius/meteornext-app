import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.admin.utils.exports
import routes.admin.settings

class Exports:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._export = models.admin.utils.exports.Exports(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(self._license, sql)

    def blueprint(self):
        # Init blueprint
        admin_utils_exports_blueprint = Blueprint('admin_utils_exports', __name__, template_folder='admin_utils_exports')

        @admin_utils_exports_blueprint.route('/admin/utils/exports', methods=['GET'])
        @jwt_required()
        def admin_utils_exports_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Exports
            return self.get()

        @admin_utils_exports_blueprint.route('/admin/utils/exports/action', methods=['POST'])
        @jwt_required()
        def admin_utils_exports_action_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Apply action
            return self.action(data)

        return admin_utils_exports_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        efilter = json.loads(request.args['filter']) if 'filter' in request.args else None
        esort = json.loads(request.args['sort']) if 'sort' in request.args else None
        export = self._export.get(efilter, esort)
        users_list = self._export.get_users_list()
        return jsonify({'exports': export, 'users_list': users_list}), 200

    def action(self, data):
        if data['action'] == 'recover':
            for item in data['items']:
                self._export.put(item, 0)
            return jsonify({'message': 'Selected exports recovered'}), 200

        elif data['action'] == 'delete':
            for item in data['items']:
                self._export.put(item, 1)
            return jsonify({'message': 'Selected exports deleted'}), 200

        elif data['action'] == 'permanently':
            for item in data['items']:
                self._export.delete(item)
            return jsonify({'message': 'Selected exports permanently deleted'}), 200
