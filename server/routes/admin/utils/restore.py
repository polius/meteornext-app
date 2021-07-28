import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.admin.utils.restore
import routes.admin.settings

class Restore:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._restore = models.admin.utils.restore.Restore(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        admin_utils_restore_blueprint = Blueprint('admin_utils_restore', __name__, template_folder='admin_utils_restore')

        @admin_utils_restore_blueprint.route('/admin/utils/restore', methods=['GET'])
        @jwt_required()
        def admin_utils_restore_method():
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

            # Get Restores
            return self.get()

        @admin_utils_restore_blueprint.route('/admin/utils/restore/action', methods=['POST'])
        @jwt_required()
        def admin_utils_restore_action_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            data = request.get_json()

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Apply action
            return self.action(data)

        return admin_utils_restore_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        rfilter = json.loads(request.args['filter']) if 'filter' in request.args else None
        rsort = json.loads(request.args['sort']) if 'sort' in request.args else None
        restore = self._restore.get(rfilter, rsort)
        users_list = self._restore.get_users_list()
        return jsonify({'restore': restore, 'users_list': users_list}), 200

    def action(self, data):
        if data['action'] == 'recover':
            for item in data['items']:
                self._restore.put(item, 0)
            return jsonify({'message': 'Selected restores successfully recovered.'}), 200

        elif data['action'] == 'delete':
            for item in data['items']:
                self._restore.put(item, 1)
            return jsonify({'message': 'Selected restores successfully deleted.'}), 200

        elif data['action'] == 'permanently':
            for item in data['items']:
                self._restore.delete(item)
            return jsonify({'message': 'Selected restores successfully permanently deleted.'}), 200
