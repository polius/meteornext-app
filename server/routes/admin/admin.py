from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import routes.admin.settings

class Admin:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        admin_blueprint = Blueprint('admin', __name__, template_folder='admin')

        @admin_blueprint.route('/admin', methods=['GET'])
        @jwt_required()
        def admin_method():
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

            return jsonify({'message': 'Access granted'}), 200

        return admin_blueprint
