import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.admin.utils.clones
import routes.admin.settings

class Clones:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._clone = models.admin.utils.clones.Clones(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(self._license, sql)

    def blueprint(self):
        # Init blueprint
        admin_utils_clones_blueprint = Blueprint('admin_utils_clones', __name__, template_folder='admin_utils_clones')

        @admin_utils_clones_blueprint.route('/admin/utils/clones', methods=['GET'])
        @jwt_required()
        def admin_utils_clones_method():
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

            # Get Clones
            return self.get()

        @admin_utils_clones_blueprint.route('/admin/utils/clones/action', methods=['POST'])
        @jwt_required()
        def admin_utils_clones_action_method():
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

        return admin_utils_clones_blueprint

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

        # Get clones
        efilter = args['filter'] if 'filter' in args else None
        esort = args['sort'] if 'sort' in args else None
        clone = self._clone.get(efilter, esort)
        users_list = self._clone.get_users_list()
        return jsonify({'clones': clone, 'users_list': users_list}), 200

    def action(self, data):
        if data['action'] == 'recover':
            for item in data['items']:
                self._clone.put(item, 0)
            return jsonify({'message': 'Selected clones recovered'}), 200

        elif data['action'] == 'delete':
            for item in data['items']:
                self._clone.put(item, 1)
            return jsonify({'message': 'Selected clones deleted'}), 200

        elif data['action'] == 'permanently':
            for item in data['items']:
                self._clone.delete(item)
            return jsonify({'message': 'Selected clones permanently deleted'}), 200
