import json
import pyotp
import bcrypt
import secrets
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes,
)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    RegistrationCredential,
    UserVerificationRequirement,
    AuthenticationCredential,
)
from flask import Blueprint, jsonify, request, session
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.admin.user_mfa
import routes.admin.settings

class MFA:
    def __init__(self, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._user_mfa = models.admin.user_mfa.User_MFA(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(sql, license)

    def blueprint(self):
        # Init blueprint
        mfa_blueprint = Blueprint('mfa', __name__, template_folder='mfa')

        @mfa_blueprint.route('/mfa', methods=['GET','DELETE'])
        @jwt_required()
        def mfa_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license['response']}), 401

            # Get request data
            data = request.args if request.method == 'GET' else request.get_json()

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if 'username' in data:
                user = self.impersonate_user(user, data)[0]

            if request.method == 'GET':
                # Get 2FA challenge
                user_mfa = self._user_mfa.get({'user_id': user['id']})
                return_data = { 'mfa': None, 'created': None}
                if len(user_mfa) > 0:
                    return_data['mode'] = '2fa' if user_mfa[0]['2fa_hash'] is not None else 'webauthn' if user_mfa[0]['webauthn_pub_key'] is not None else None
                    return_data['created'] = user_mfa[0]['created_at']
                return jsonify({'data': return_data}), 200
            elif request.method == 'DELETE':
                # Clean the user MFA
                self._user_mfa.disable_mfa({'user_id': user['id']})
                return jsonify({'message': 'MFA disabled'}), 200

        @mfa_blueprint.route('/mfa/2fa', methods=['GET','POST'])
        @jwt_required(optional=True)
        def mfa_2fa_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license['response']}), 401
            
            # Get request data
            data = request.args if request.method == 'GET' else request.get_json()

            # Get user
            try:
                user = self.get_user(data)
            except Exception as e:
                return jsonify({"message": str(e)}), 400

            if request.method == 'GET':
                # Get 2FA hash
                mfa_hash = pyotp.random_base32()
                mfa_uri = pyotp.TOTP(mfa_hash, interval=30).provisioning_uri(user['email'], issuer_name="Meteor Next")
                return jsonify({"mfa_hash": mfa_hash, "mfa_uri": mfa_uri}), 200

            elif request.method == 'POST':
                # Store 2FA
                mfa = pyotp.TOTP(data['hash'], interval=30)
                if 'value' not in data or len(data['value']) == 0 or not mfa.verify(data['value'], valid_window=1):
                    return jsonify({'message': 'Invalid MFA Code'}), 400
                self._user_mfa.enable_2fa({'user_id': user['id'], '2fa_hash': data['hash']})
                return jsonify({'message': 'MFA enabled'}), 200

        @mfa_blueprint.route('/mfa/webauthn/register', methods=['GET','POST'])
        @jwt_required(optional=True)
        def mfa_webauthn_register_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license['response']}), 401
            
            # Get request data
            data = request.args if request.method == 'GET' else request.get_json()

            # Get user
            try:
                user = self.get_user(data)
            except Exception as e:
                return jsonify({"message": str(e)}), 400

            if request.method == 'GET':              
                # Generate webauthn challenge
                return self.get_webauthn_register(user)

            elif request.method == 'POST':
                # Validate challenge & Register webauthn credential
                try:
                    self.post_webauthn_register(user, data)
                    if 'store' in data and data['store']:
                        return jsonify({'message': 'MFA enabled'}), 200
                    return jsonify({"message": 'Credentials validated'}), 200
                except Exception as e:
                    return jsonify({'message': str(e)}), 400

        return mfa_blueprint
        
    ####################
    # Internal Methods #
    ####################
    def get_webauthn_register(self, user):
        # Generate challenge and store it to the user session
        session['challenge'] = self.__generate_challenge()

        # Generate registration options
        registration_options = generate_registration_options(
            rp_id=request.host,
            rp_name="Meteor Next",
            user_id=user['username'],
            user_name=user['username'],
            user_display_name=user['username'],
            challenge=session['challenge'],
        )
        return options_to_json(registration_options)

    def post_webauthn_register(self, user, data):
        # Registration Response Verification
        registration_verification = verify_registration_response(
            credential=RegistrationCredential.parse_raw(json.dumps(data['credential'])),
            expected_challenge=session['challenge'],
            expected_origin='https://' + request.host,
            expected_rp_id=request.host,
            require_user_verification=False,
        )

        # Store webauthn credentials
        if 'store' in data and data['store'] is True:
            storage = {
                'user_id': user['id'],
                'webauthn_pub_key': bytes_to_base64url(registration_verification.credential_public_key),
                'webauthn_credential_id': data['credential']['id'],
                'webauthn_sign_count': 0,
                'webauthn_rp_id': request.host
            }
            self._user_mfa.enable_webauthn(storage)

    def get_webauthn_login(self, user_mfa):
        # Generate a new challenge
        session['challenge'] = self.__generate_challenge()

        # Generate authentification options
        authentication_options = generate_authentication_options(
            rp_id=request.host,
            challenge=session['challenge'],
            allow_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(user_mfa['webauthn_credential_id']))],
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        return options_to_json(authentication_options)

    def post_webauthn_login(self, user, user_mfa):
        # Get request data
        data = request.get_json()

        # Authentication Response Verification
        authentication_verification = verify_authentication_response(
            credential=AuthenticationCredential.parse_raw(json.dumps(data['mfa'])),
            expected_challenge=session['challenge'],
            expected_rp_id=request.host,
            expected_origin='https://' + request.host,
            credential_public_key=base64url_to_bytes(user_mfa['webauthn_pub_key']),
            credential_current_sign_count=user_mfa['webauthn_sign_count'],
            require_user_verification=False,
        )

        # Update sign_count
        self._user_mfa.put_webauthn_sign_count({'webauthn_sign_count': authentication_verification.new_sign_count, 'user_id': user['id']})

    def __generate_challenge(self, length=64):
        return secrets.token_bytes(length)

    def get_user(self, data):
        # From Login force MFA
        if get_jwt_identity() is None:
            user = self.check_login(data)
            if len(user) == 0:
                raise Exception('Invalid Credentials')
        else:
            # From Profile
            user = self._users.get(get_jwt_identity())
            if len(user) == 0:
                raise Exception('This user does not longer exist')
            
            # From Admin - Users
            if 'username' in data:
                user = self.impersonate_user(user[0], data)
                if len(user) == 0:
                    raise Exception('Insufficient Privileges')

        # Check if user is disabled
        if user[0]['disabled']:
            raise Exception('Account disabled')
        return user[0]

    def impersonate_user(self, current_user, new_user):
        # Check Settings - Security (Administration URL)
        if not self._settings.check_url() or not current_user['admin']:
            return []
        # Get new user
        return self._users.get(new_user['username'])

    def check_login(self, data):
        # Get User from Database
        user = self._users.get(data['username'])
        # Check user & password
        if len(user) == 0 or not bcrypt.checkpw(data['password'].encode('utf-8'), user[0]['password'].encode('utf-8')):
            return []
        # Login success
        return user
