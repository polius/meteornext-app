import imp
import bcrypt
from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    login_blueprint = Blueprint('login', __name__, template_folder='login')

    # Init models
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)

    @login_blueprint.route('/login', methods=['POST'])
    def login_user():
        if not request.is_json:
            return jsonify({"message": "Missing JSON in request"}), 400

        login_json = request.get_json()
        
        # Get User from Database
        user = users.get(login_json['username'])

        if len(user) == 0 or not bcrypt.checkpw(login_json['password'].encode('utf8'), user[0]['password'].encode('utf8')):
            return jsonify({"msg": "Invalid username and password."}), 401
        else:
            ret = {
                'access_token': create_access_token(identity=user[0]['username']),
                'refresh_token': create_refresh_token(identity=user[0]['username']),
                'username': user[0]['username'],
                'admin': user[0]['admin']
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