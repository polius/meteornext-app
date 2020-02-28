import bcrypt
import models.admin.users
from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity)

import routes.admin.settings

class Login:
    def __init__(self, app, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql)

    def license(self, value):
        self._license = value

    def blueprint(self):
        # Init blueprint
        login_blueprint = Blueprint('login', __name__, template_folder='login')

        @login_blueprint.route('/login', methods=['POST'])
        def login_user():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Check parameters
            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400
            login_json = request.get_json()

            # Check Settings - Security (Administration URL)
            valid_url = self._settings.check_url()

            # Get User from Database
            user = self._users.get(login_json['username'])

            if len(user) == 0 or not bcrypt.checkpw(login_json['password'].encode('utf-8'), user[0]['password'].encode('utf-8')):
                return jsonify({"message": "Invalid username or password"}), 401
            else:
                # Update user last_login
                self._users.put_last_login(login_json['username'])

                # Build return data
                ret = {
                    'access_token': create_access_token(identity=user[0]['username']),
                    'refresh_token': create_refresh_token(identity=user[0]['username']),
                    'username': user[0]['username'],
                    'coins': user[0]['coins'],
                    'admin': user[0]['admin'] and valid_url,
                    'deployments_enable': user[0]['deployments_enable'],
                    'deployments_basic': user[0]['deployments_basic'],
                    'deployments_pro': user[0]['deployments_pro'],
                    'deployments_inbenta': user[0]['deployments_inbenta'],
                    'deployments_edit': user[0]['deployments_edit']
                }
                return jsonify({'data': ret}), 200

        @login_blueprint.route('/login/check', methods=['GET'])
        @jwt_required
        def login_check():
            return jsonify({'message': 'OK'}), 200

        return login_blueprint