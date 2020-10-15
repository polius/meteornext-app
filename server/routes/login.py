import bcrypt
import models.admin.users
from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity)

import routes.admin.settings

class Login:
    def __init__(self, app, sql, license, mfa):
        self._app = app
        self._license = license
        self._mfa = mfa
        # Init models
        self._users = models.admin.users.Users(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        login_blueprint = Blueprint('login', __name__, template_folder='login')

        @login_blueprint.route('/login', methods=['POST'])
        def login_user():
            # Check license
            self._license.validate()
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check parameters
            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400
            login_json = request.get_json()

            # Check Settings - Security (Administration URL)
            valid_url = self._settings.check_url()

            # Get User from Database
            user = self._users.get(login_json['username'])

            # Check user & password
            if len(user) == 0 or not bcrypt.checkpw(login_json['password'].encode('utf-8'), user[0]['password'].encode('utf-8')):
                return jsonify({"message": "Invalid username or password"}), 401

            # Check MFA
            if len(login_json['mfa']) == 0 and user[0]['mfa'] == 1:
                return jsonify({"message": "Requesting MFA credentials"}), 202
            if user[0]['mfa'] == 1 and not self._mfa.verify(login_json['mfa']):
                return jsonify({"message": "Invalid MFA Code"}), 401

            # Update user last_login
            self._users.put_last_login(login_json['username'])

            # Build return data
            ret = {
                'access_token': create_access_token(identity=user[0]['username']),
                'refresh_token': create_refresh_token(identity=user[0]['username']),
                'username': user[0]['username'],
                'mfa': user[0]['mfa'],
                'coins': user[0]['coins'],
                'admin': user[0]['admin'] and valid_url,
                'inventory_enabled': user[0]['inventory_enabled'],
                'deployments_enabled': user[0]['deployments_enabled'],
                'deployments_basic': user[0]['deployments_basic'],
                'deployments_pro': user[0]['deployments_pro'],
                'monitoring_enabled': user[0]['monitoring_enabled'],
                'utils_enabled': user[0]['utils_enabled'],
                'client_enabled': user[0]['client_enabled']
            }
            return jsonify({'data': ret}), 200

        @login_blueprint.route('/login/check', methods=['GET'])
        @jwt_required
        def login_check():
            return jsonify({'message': 'OK'}), 200

        return login_blueprint