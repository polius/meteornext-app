import secrets
from flask import Blueprint, jsonify
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users

class Inventory:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)

    def blueprint(self):
        # Init blueprint
        inventory_blueprint = Blueprint('inventory', __name__, template_folder='inventory')

        @inventory_blueprint.route('/inventory/genpass', methods=['GET'])
        @jwt_required()
        def inventory_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Generate password
            password = secrets.token_urlsafe(32)

            # Return password
            return jsonify({'password': password})

        return inventory_blueprint
