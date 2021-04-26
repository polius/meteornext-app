import bcrypt
import models.admin.users
import models.admin.user_mfa
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)


class Profile:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._user_mfa = models.admin.user_mfa.User_MFA(sql)

    def blueprint(self):
        # Init blueprint
        profile_blueprint = Blueprint('profile', __name__, template_folder='profile')

        @profile_blueprint.route('/profile', methods=['GET'])
        @jwt_required()
        def profile_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User Profile
            profile = {'username': user['username'], 'group': user['group'], 'email': user['email'], 'mfa': None, 'mfa_created': None}
            mfa = self._user_mfa.get({'user_id': user['id']})
            if len(mfa) > 0:
                profile['mfa'] = '2fa' if mfa[0]['2fa_hash'] is not None else 'webauthn'
                profile['mfa_created'] = mfa[0]['created_at']
            return jsonify({'data': profile}), 200

        @profile_blueprint.route('/profile/password', methods=['PUT'])
        @jwt_required()
        def profile_password_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            # Check parameters
            if 'current' not in data or 'new' not in data or 'repeat' not in data:
                return jsonify({'message': 'Insufficient parameters'}), 400

            # Check password
            if not bcrypt.checkpw(data['current'].encode('utf-8'), user['password'].encode('utf-8')):
                return jsonify({"message": "The current password is invalid"}), 400

            if len(data['new']) < 8:
                return jsonify({'message': 'The new password must have at least 8 characters'}), 400

            if data['new'] != data['repeat']:
                return jsonify({"message": "The new password does not match"}), 400

            # Change password
            encrypted_passw = bcrypt.hashpw(data['new'].encode('utf8'), bcrypt.gensalt())
            self._users.change_password({'username': get_jwt_identity(), 'password': encrypted_passw})
            return jsonify({'message': 'Password successfully changed'}), 200

        return profile_blueprint
