import bcrypt
import models.admin.users
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Profile:
    def __init__(self, app, sql, license, mfa):
        self._license = license
        self._mfa = mfa
        # Init models
        self._users = models.admin.users.Users(sql)

    def blueprint(self):
        # Init blueprint
        profile_blueprint = Blueprint('profile', __name__, template_folder='profile')

        @profile_blueprint.route('/profile', methods=['GET','PUT'])
        @jwt_required
        def profile_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Get MFA Uri
            user['mfaUri'] = self._mfa.provisioning_uri(user['email'], issuer_name="Meteor Next")

            # Get Request Json
            profile_json = request.get_json()

            if request.method == 'GET':
                return jsonify({'data': user}), 200

            elif request.method == 'PUT':
                if len(profile_json['password']) > 0 and len(profile_json['password']) < 8:
                    return jsonify({'message': 'Password must have at least 8 characters'}), 400
                else:
                    if len(profile_json['password']) != 0:
                        profile_json['password'] = bcrypt.hashpw(profile_json['password'].encode('utf8'), bcrypt.gensalt())
                    self._users.put_profile({'username': get_jwt_identity(), 'email': profile_json['email'], 'password': profile_json['password'], 'mfa': profile_json['mfa']})
                    return jsonify({'message': 'Changes saved successfully'}), 200

        return profile_blueprint