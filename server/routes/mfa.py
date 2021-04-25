import pyotp
import secrets
import webauthn
import models.admin.users
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)


class MFA:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)

    def blueprint(self):
        # Init blueprint
        mfa_blueprint = Blueprint('mfa', __name__, template_folder='mfa')

        @mfa_blueprint.route('/mfa/2fa', methods=['GET','POST'])
        @jwt_required()
        def mfa_2fa_method():
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

            elif request.method == 'POST':
                data = request.get_json()
                if 'enabled' not in data:
                    return jsonify({'message': 'Insufficient parameters'}), 400
                # Disable MFA
                if data['enabled'] == 0:
                    self._users.disable_mfa({'username': get_jwt_identity()})
                    return jsonify({'message': 'MFA successfully disabled'}), 200
                else:
                    mfa = pyotp.TOTP(data['hash'], interval=30)
                    if 'value' not in data or len(data['value']) == 0 or not mfa.verify(data['value'], valid_window=1):
                        return jsonify({'message': 'Invalid MFA Code'}), 400
                    self._users.enable_mfa({'username': get_jwt_identity(), 'mfa_hash': data['hash']})
                    return jsonify({'message': 'MFA successfully enabled'}), 200

        @mfa_blueprint.route('/mfa/webauthn/register', methods=['POST'])
        @jwt_required()
        def mfa_webauthn_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get data
            data = request.get_json()

            # Generate challenge
            challenge = self.generate_challenge(32)
            ukey = self.generate_ukey()
            make_credential_options = webauthn.WebAuthnMakeCredentialOptions(challenge, 'Meteor Next', data['host'], ukey, get_jwt_identity(), user['username'], 'https://meteor2.io')
            return jsonify(make_credential_options.registration_dict)
            
        return mfa_blueprint
        
    ####################
    # Internal Methods #
    ####################
    def generate_challenge(self, challenge_len=32):
        return secrets.token_urlsafe(challenge_len)

    def generate_ukey(self):
        return self.generate_challenge(20)
