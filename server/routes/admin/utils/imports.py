import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.admin.utils.imports
import routes.admin.settings

class Imports:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._imports = models.admin.utils.imports.Imports(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(self._license, sql)

    def blueprint(self):
        # Init blueprint
        admin_utils_imports_blueprint = Blueprint('admin_utils_imports', __name__, template_folder='admin_utils_imports')

        @admin_utils_imports_blueprint.route('/admin/utils/imports', methods=['GET'])
        @jwt_required()
        def admin_utils_imports_method():
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

            # Get Imports
            return self.get()

        @admin_utils_imports_blueprint.route('/admin/utils/imports/action', methods=['POST'])
        @jwt_required()
        def admin_utils_imports_action_method():
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

        return admin_utils_imports_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        # Parse arguments
        args = {}
        try:
            for k,v in request.args.to_dict().items():
                if k.count('[') == 0:
                    args[k] = v
                elif k.count('[') == 1:
                    if not k[:k.find('[')] in args:
                        args[k[:k.find('[')]] = {}
                    args[k[:k.find('[')]][k[k.find('[')+1:-1]] = v
                elif k.count('[') == 2:
                    if not k[:k.find('[')] in args:
                        args[k[:k.find('[')]] = {}
                    key = k[k.find('[')+1:-1]
                    key = key[:key.find(']')]
                    if key not in args[k[:k.find('[')]]:
                        args[k[:k.find('[')]][key] = []
                    args[k[:k.find('[')]][key].append(v)
        except Exception:
            return jsonify({'message': 'Invalid parameters'}), 400

        # Get imports
        rfilter = args['filter'] if 'filter' in args else None
        rsort = args['sort'] if 'sort' in args else None
        imports = self._imports.get(rfilter, rsort)
        users_list = self._imports.get_users_list()
        return jsonify({'imports': imports, 'users_list': users_list}), 200

    def action(self, data):
        if data['action'] == 'recover':
            for item in data['items']:
                self._imports.put(item, 0)
            return jsonify({'message': 'Selected imports recovered'}), 200

        elif data['action'] == 'delete':
            for item in data['items']:
                self._imports.put(item, 1)
            return jsonify({'message': 'Selected imports deleted'}), 200

        elif data['action'] == 'permanently':
            for item in data['items']:
                self._imports.delete(item)
            return jsonify({'message': 'Selected imports permanently deleted'}), 200
