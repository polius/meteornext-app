import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.admin.inventory.inventory
import routes.admin.settings

class Inventory:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._inventory = models.admin.inventory.inventory.Inventory(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        admin_inventory_blueprint = Blueprint('admin_inventory', __name__, template_folder='admin_inventory')

        @admin_inventory_blueprint.route('/admin/inventory/groups', methods=['GET'])
        @jwt_required
        def admin_inventory_groups_method():
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

            # Return groups
            return jsonify({'groups': self._inventory.get_groups()}), 200

        @admin_inventory_blueprint.route('/admin/inventory/users', methods=['GET'])
        @jwt_required
        def admin_inventory_users_method():
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

            # Check params
            if 'group' not in request.args:
                return jsonify({'message': 'Missing "group" parameter'}), 400

            # Return users
            return jsonify({'users': self._inventory.get_users(request.args['group'])}), 200

        return admin_inventory_blueprint
