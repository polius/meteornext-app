import json
import pyotp
import bcrypt
import models.admin.users
from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required)

import models.admin.settings
import routes.admin.settings

class Login:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._settings = models.admin.settings.Settings(sql)
        # Init routes
        self._settings_route = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        login_blueprint = Blueprint('login', __name__, template_folder='login')

        @login_blueprint.route('/login', methods=['POST'])
        def login_user():
            try:
                # Check license
                self._license.validate()
                if not self._license.validated:
                    return jsonify({"message": self._license.status['response']}), 401

                # Check parameters
                if not request.is_json:
                    return jsonify({"message": "Missing JSON in request"}), 400
                login_json = request.get_json()

                # Check Settings - Security (Administration URL + Force MFA)
                security = self._settings.get(setting_name='security')
                valid_url = self._settings_route.check_url(security)
                force_mfa = self._settings_route.check_mfa(security)

                # Get User from Database
                user = self._users.get(login_json['username'])

                # Check user & password
                if len(user) == 0 or not bcrypt.checkpw(login_json['password'].encode('utf-8'), user[0]['password'].encode('utf-8')):
                    return jsonify({"message": "Invalid username or password"}), 401

                # Check MFA
                if user[0]['mfa'] == 0 and force_mfa and 'mfa' in login_json and 'mfa_hash' in login_json:
                    mfa = pyotp.TOTP(login_json['mfa_hash'], interval=30)
                    if len(login_json['mfa']) == 0 or not mfa.verify(login_json['mfa']):
                        return jsonify({'message': 'Invalid MFA Code'}), 401
                    else:
                        self._users.put_mfa({'username': get_jwt_identity(), 'mfa': login_json['mfa'], 'mfa_hash': login_json['mfa_hash']})
                        user[0]['mfa'] = login_json['mfa']
                        user[0]['mfa_hash'] = login_json['mfa_hash']
                elif user[0]['mfa'] == 0 and force_mfa:
                    mfa_hash = pyotp.random_base32()
                    mfa_uri = pyotp.TOTP(mfa_hash, interval=30).provisioning_uri(user[0]['email'], issuer_name="Meteor Next")
                    return jsonify({"code": "mfa_setup", "message": "MFA setup is required", "mfa_hash": mfa_hash, "mfa_uri": mfa_uri}), 202
                if user[0]['mfa'] == 1 and len(login_json['mfa']) == 0:
                    return jsonify({"code": "mfa_request", "message": "Requesting MFA credentials"}), 202
                if user[0]['mfa'] == 1 and not pyotp.TOTP(user[0]['mfa_hash'], interval=30).verify(login_json['mfa']):
                    return jsonify({"message": "Invalid MFA Code"}), 401

                # Check disabled
                if user[0]['disabled']:
                    return jsonify({"message": "Account disabled"}), 401

                # Update user last_login
                self._users.put_last_login(login_json['username'])

                # Build return data
                ret = {
                    'access_token': create_access_token(identity=user[0]['username']),
                    'refresh_token': create_refresh_token(identity=user[0]['username']),
                    'username': user[0]['username'],
                    'coins': user[0]['coins'],
                    'admin': 1 if user[0]['admin'] and valid_url else 0,
                    'owner': user[0]['owner'],
                    'inventory_enabled': user[0]['inventory_enabled'],
                    'inventory_secured': user[0]['inventory_secured'],
                    'deployments_enabled': user[0]['deployments_enabled'],
                    'deployments_basic': user[0]['deployments_basic'],
                    'deployments_pro': user[0]['deployments_pro'],
                    'monitoring_enabled': user[0]['monitoring_enabled'],
                    'utils_enabled': user[0]['utils_enabled'],
                    'client_enabled': user[0]['client_enabled'],
                    'coins_execution': user[0]['coins_execution'],
                    'coins_day': user[0]['coins_day']
                }
                return jsonify({'data': ret}), 200
            except Exception as e:
                print(str(e))
                raise

        @login_blueprint.route('/login/check', methods=['GET'])
        @jwt_required()
        def login_check():
            return jsonify({'message': 'OK'}), 200

        return login_blueprint