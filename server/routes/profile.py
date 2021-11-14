import json
import bcrypt
import string
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.admin.settings

class Profile:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._settings = models.admin.settings.Settings(sql, license)

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
            profile = {'username': user['username'], 'group': user['group'], 'email': user['email']}
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

            # Change password
            try:
                self.change_password(user, data['current'], data['new'], data['repeat'])
                return jsonify({'message': 'Password successfully changed'}), 200
            except Exception as e:
                return jsonify({'message': str(e)}), 400

        return profile_blueprint

    ####################
    # Internal Methods #
    ####################
    def change_password(self, user, current, new, repeat):
        # Check current password
        if not bcrypt.checkpw(current.encode('utf-8'), user['password'].encode('utf-8')):
            raise Exception("The current password is not valid.")

        # Check repeat password
        if new != repeat:
            raise Exception("The new password does not match")

        # Check Password Policy
        security = json.loads(self._settings.get(setting_name='SECURITY'))
        special_characters = set(string.punctuation)
        if len(new) < int(security['password_min']):
            raise Exception(f"The password must be at least {security['password_min']} characters long.")
        if security['password_lowercase'] and not any(c.islower() for c in new):
            raise Exception('The password must contain a lowercase letter.')
        if security['password_uppercase'] and not any(c.isupper() for c in new):
            raise Exception('The password must contain a uppercase letter.')
        if security['password_number'] and not any(c.isnumeric() for c in new):
            raise Exception('The password must contain a number.')
        if security['password_special'] and not any(c in special_characters for c in new):
            raise Exception('The password must contain a special character.')

        # Change password
        encrypted_passw = bcrypt.hashpw(new.encode('utf8'), bcrypt.gensalt())
        self._users.change_password({'username': user['username'], 'password': encrypted_passw})
        return encrypted_passw
