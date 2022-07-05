import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.admin.inventory.inventory
import routes.admin.settings

class Inventory:
    def __init__(self, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._inventory = models.admin.inventory.inventory.Inventory(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(sql, license)

    def blueprint(self):
        # Init blueprint
        admin_inventory_blueprint = Blueprint('admin_inventory', __name__, template_folder='admin_inventory')

        @admin_inventory_blueprint.route('/admin/inventory/groups', methods=['GET'])
        @jwt_required()
        def admin_inventory_groups_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

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

            # Return groups
            return jsonify({'groups': self._inventory.get_groups()}), 200

        @admin_inventory_blueprint.route('/admin/inventory/users', methods=['GET'])
        @jwt_required()
        def admin_inventory_users_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

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

            # Return users
            group_id = request.args['group_id'] if 'group_id' in request.args else None
            return jsonify({'users': self._inventory.get_users(group_id=group_id)}), 200

        return admin_inventory_blueprint
