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

        @profile_blueprint.route('/profile', methods=['GET','PUT'])
        @jwt_required
        def profile_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            profile_json = request.get_json()

            if request.method == 'GET':
                return jsonify({'data': user}), 200

            elif request.method == 'PUT':
                # Check password
                if len(profile_json['password']) > 0 and len(profile_json['password']) < 8:
                    return jsonify({'message': 'Password must have at least 8 characters'}), 400

                # Check & Parse MFA
                if profile_json['mfa']:
                    if profile_json['mfaHash']:
                        mfa = pyotp.TOTP(profile_json['mfaHash'], interval=30)
                        if len(profile_json['mfaValue']) > 0 and not mfa.verify(profile_json['mfaValue']):
                            return jsonify({'message': 'Invalid MFA Code'}), 400
                    else:
                        profile_json['mfa'] = user['mfa']
                        profile_json['mfaHash'] = user['mfa_hash']
                else:
                    profile_json['mfaHash'] = None

                # Parse password
                if len(profile_json['password']) != 0:
                    profile_json['password'] = bcrypt.hashpw(profile_json['password'].encode('utf8'), bcrypt.gensalt())
                else:
                    profile_json['password'] = user['password']

                # Update profile
                self._users.put_profile({'username': get_jwt_identity(), 'email': profile_json['email'], 'password': profile_json['password'], 'mfa': profile_json['mfa'], 'mfa_hash': profile_json['mfaHash']})
                return jsonify({'message': 'Changes saved successfully'}), 200

        @profile_blueprint.route('/profile/mfa', methods=['GET'])
        @jwt_required
        def profile_mfa_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Generate MFA hash
            mfa_hash = pyotp.random_base32()
            mfa_uri = pyotp.TOTP(mfa_hash, interval=30).provisioning_uri(user['email'], issuer_name="Meteor Next")
            return jsonify({"mfa_hash": mfa_hash, "mfa_uri": mfa_uri}), 200

        return profile_blueprint