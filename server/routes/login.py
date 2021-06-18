import pyotp
import bcrypt
from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, jwt_required, set_access_cookies, unset_access_cookies)

import models.admin.users
import models.admin.user_mfa
import models.admin.settings
import routes.admin.settings
import routes.mfa

class Login:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._user_mfa = models.admin.user_mfa.User_MFA(sql)
        self._settings = models.admin.settings.Settings(sql)
        # Init routes
        self._settings_route = routes.admin.settings.Settings(app, sql, license)
        self._mfa = routes.mfa.MFA(app, sql, license)

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

            # Check Settings - Security (Administration URL + Force MFA)
            security = self._settings.get(setting_name='security')
            valid_url = self._settings_route.check_url(security)
            force_mfa = self._settings_route.check_mfa(security)

            # Get User from Database
            user = self._users.get(login_json['username'])

            # Check user & password
            if len(user) == 0 or not bcrypt.checkpw(login_json['password'].encode('utf-8'), user[0]['password'].encode('utf-8')):
                return jsonify({"message": "Invalid username or password"}), 401

            # Check disabled
            if user[0]['disabled']:
                return jsonify({"message": "Account disabled"}), 401

            # Check MFA
            if user[0]['mfa'] is None:
                if force_mfa:
                    return jsonify({"code": "mfa_setup", "message": "MFA is required"}), 202
            else:
                user_mfa = self._user_mfa.get({'user_id': user[0]['id']})
                if user[0]['mfa'] == '2fa':
                    if 'mfa' not in login_json:
                        return jsonify({"code": "2fa", "message": "Requesting 2FA credentials"}), 202
                    elif not pyotp.TOTP(user_mfa[0]['2fa_hash'], interval=30).verify(login_json['mfa'], valid_window=1):
                        return jsonify({"message": "Invalid MFA Code"}), 401
                elif user[0]['mfa'] == 'webauthn':
                    try:
                        if 'mfa' not in login_json:
                            return jsonify({"code": "webauthn", "data": self._mfa.get_webauthn_login(user, user_mfa), "message": "Requesting Webauthn credentials"}), 202
                        else:
                            self._mfa.post_webauthn_login(user, user_mfa)
                    except Exception as e:
                        return jsonify({'message': str(e)}), 400

            # Update user data
            ip = request.headers.getlist("X-Forwarded-For")[0] if request.headers.getlist("X-Forwarded-For") else request.remote_addr
            user_agent = request.user_agent.string
            self._users.put_last_login({"username": login_json['username'], "ip": ip, "user_agent": user_agent})

            # Generate access tokens
            access_token = create_access_token(identity=user[0]['username'])

            # Build return data
            data = {
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
            resp = jsonify({'data': data})
            set_access_cookies(resp, access_token, 12*60*60)
            return resp, 200

        @login_blueprint.route('/login/check', methods=['GET'])
        @jwt_required()
        def login_check():
            return jsonify({'message': 'OK'}), 200

        @login_blueprint.route('/logout', methods=['POST'])
        def logout_check():
            resp = jsonify({'message': 'Bye'})
            unset_access_cookies(resp)
            return resp

        return login_blueprint
