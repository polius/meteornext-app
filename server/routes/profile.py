import pyotp
import bcrypt
import models.admin.users
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Profile:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)

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
            profile = {'username': user['username'], 'group': user['group'], 'email': user['email'], 'mfa': user['mfa'], 'mfa_created': user['mfa_created']}
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

        @profile_blueprint.route('/profile/mfa', methods=['GET','PUT'])
        @jwt_required()
        def profile_mfa_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                mfa_hash = pyotp.random_base32()
                mfa_uri = pyotp.TOTP(mfa_hash, interval=30).provisioning_uri(user['email'], issuer_name="Meteor Next")
                return jsonify({"mfa_hash": mfa_hash, "mfa_uri": mfa_uri}), 200

            elif request.method == 'PUT':
                data = request.get_json()
                if 'enabled' not in data:
                    return jsonify({'message': 'Insufficient parameters'}), 400
                # Disable MFA
                if data['enabled'] == 0:
                    self._users.disable_mfa({'username': get_jwt_identity()})
                    return jsonify({'message': 'MFA successfully disabled'}), 200
                if 'mode' not in data or data['mode'] not in ['mfa','u2f']:
                    return jsonify({'message': 'Mode is not valid'}), 400
                if data['mode'] == 'mfa' and data['enabled']:
                    mfa = pyotp.TOTP(data['hash'], interval=30)
                    if 'value' not in data or len(data['value']) == 0 or not mfa.verify(data['value'], valid_window=1):
                        return jsonify({'message': 'Invalid MFA Code'}), 400
                    self._users.enable_mfa({'username': get_jwt_identity(), 'mfa_hash': data['hash']})
                    return jsonify({'message': 'MFA successfully enabled'}), 200

        return profile_blueprint