import bcrypt
import models.admin.users
from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity)

class Login:
    def __init__(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)

    def blueprint(self):
        # Init blueprint
        login_blueprint = Blueprint('login', __name__, template_folder='login')

        @login_blueprint.route('/login', methods=['POST'])
        def login_user():
            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400

            login_json = request.get_json()
            
            # Get User from Database
            user = self._users.get(login_json['username'])

            if len(user) == 0 or not bcrypt.checkpw(login_json['password'].encode('utf-8'), user[0]['password'].encode('utf-8')):
                return jsonify({"message": "Invalid username or password"}), 401
            else:
                ret = {
                    'access_token': create_access_token(identity=user[0]['username']),
                    'refresh_token': create_refresh_token(identity=user[0]['username']),
                    'username': user[0]['username'],
                    'coins': user[0]['coins'],
                    'admin': user[0]['admin'],
                    'deployments_enable': user[0]['deployments_enable'],
                    'deployments_basic': user[0]['deployments_basic'],
                    'deployments_pro': user[0]['deployments_pro'],
                    'deployments_inbenta': user[0]['deployments_inbenta'],
                    'deployments_edit': user[0]['deployments_edit']
                }
                return jsonify({'data': ret}), 200

        # @login_blueprint.route('/refresh', methods=['POST'])
        # @jwt_refresh_token_required
        # def refresh():
        #     ''' refresh token endpoint '''
        #     current_user = get_jwt_identity()
        #     ret = {
        #         'token': create_access_token(identity=current_user)
        #     }
        #     return jsonify({'status': True, 'data': ret}), 200

        return login_blueprint