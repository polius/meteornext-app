import json
import pyotp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.groups
import models.admin.users
import routes.admin.settings

class Users:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._groups = models.admin.groups.Groups(sql)
        self._users = models.admin.users.Users(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        users_blueprint = Blueprint('users', __name__, template_folder='users')

        @users_blueprint.route('/admin/users', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def users_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            user_json = request.get_json()

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(user['id'], user_json)
            elif request.method == 'PUT':
                return self.put(user['id'], user_json)
            elif request.method == 'DELETE':
                return self.delete()

        @users_blueprint.route('/admin/users/mfa', methods=['GET'])
        @jwt_required
        def users_mfa_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User
            user = self._users.get(request.args['username'])[0]

            # Generate MFA hash
            mfa_hash = pyotp.random_base32()
            mfa_uri = pyotp.TOTP(mfa_hash, interval=30).provisioning_uri(user['email'], issuer_name="Meteor Next")
            return jsonify({"mfa_hash": mfa_hash, "mfa_uri": mfa_uri}), 200

        return users_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        return jsonify({'data': {'users': self._users.get(), 'groups': self._groups.get()}}), 200

    def post(self, user_id, data):
        user = self._users.get(data['username'])
        # Check unique user
        if len(user) > 0:
            return jsonify({'message': 'This user currently exists'}), 400
        
        # Hash password
        data['password'] = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())

        # Add user
        self._users.post(user_id, data)
        return jsonify({'message': 'User added successfully'}), 200

    def put(self, user_id, data):
        user = self._users.get(data['current_username'])
        # Check unique user
        if len(user) == 0:
            return jsonify({'message': 'This user does not exist'}), 400

        # Check password
        elif data['current_username'] != data['username'] and self._users.exist(data['username']):
            return jsonify({'message': 'This user currently exists'}), 400
        elif data['password'] != user[0]['password']:
            data['password'] = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())

        # Check & Parse MFA
        if data['mfa']['enabled']:
            if 'hash' in data['mfa']:
                mfa = pyotp.TOTP(data['mfa']['hash'], interval=30)
                if len(data['mfa']['value']) > 0 and not mfa.verify(data['mfa']['value']):
                    return jsonify({'message': 'Invalid MFA Code'}), 400
            else:
                data['mfa']['enabled'] = user[0]['mfa']
                data['mfa']['hash'] = user[0]['mfa_hash']
        else:
            data['mfa']['hash'] = None

        # Edit user
        self._users.put(user_id, data)
        return jsonify({'message': 'User edited successfully'}), 200

    def delete(self):
        users = json.loads(request.args['users'])
        self._users.delete(users)
        return jsonify({'message': 'Selected users deleted successfully'}), 200
