import os
import pyotp
import secrets
import webauthn
import models.admin.users
import models.admin.user_mfa
from flask import Blueprint, jsonify, request, session
from flask_jwt_extended import (jwt_required, get_jwt_identity)


class MFA:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._user_mfa = models.admin.user_mfa.User_MFA(sql)

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
                    self._user_mfa.clean_mfa({'user_id': user['id']})
                    return jsonify({'message': 'MFA successfully disabled'}), 200
                else:
                    mfa = pyotp.TOTP(data['hash'], interval=30)
                    if 'value' not in data or len(data['value']) == 0 or not mfa.verify(data['value'], valid_window=1):
                        return jsonify({'message': 'Invalid MFA Code'}), 400
                    self._users.store_2fa({'user_id': user['id'], '2fa_hash': data['hash']})
                    return jsonify({'message': 'MFA successfully enabled'}), 200

        @mfa_blueprint.route('/mfa/webauthn/register', methods=['POST'])
        @jwt_required()
        def mfa_webauthn_register_method():
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

            # Clear session variables prior to starting a new registration
            session.pop('register_ukey', None)
            session.pop('register_username', None)
            session.pop('register_display_name', None)
            session.pop('challenge', None)
            session['register_username'] = get_jwt_identity()
            session['register_display_name'] = user['username']

            # Generate challenge and store it to the user session
            challenge = self.generate_challenge(32)
            ukey = self.generate_ukey()
            session['challenge'] = challenge.rstrip('=')
            session['register_ukey'] = ukey

            # Make credentials
            make_credential_options = webauthn.WebAuthnMakeCredentialOptions(challenge, 'Meteor Next', data['host'], ukey, get_jwt_identity(), user['username'], 'https://meteor2.io')
            return jsonify(make_credential_options.registration_dict)

        @mfa_blueprint.route('/mfa/webauthn/verify', methods=['POST'])
        @jwt_required()
        def mfa_webauthn_verify_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get request data
            data = request.get_json()
            if 'credential' not in data:
                return jsonify({'message': 'Insufficient parameters'}), 400

            # Get session data
            challenge = session['challenge']
            username = session['register_username']
            display_name = session['register_display_name']
            ukey = session['register_ukey']
            
            # Build webauthn registration response
            rp_id = data['host']
            origin = 'https://' + data['host']
            registration_response = data['credential']
            trust_anchor_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trusted_attestation_roots')
            trusted_attestation_cert_required = True
            self_attestation_permitted = True
            none_attestation_permitted = True
            webauthn_registration_response = webauthn.WebAuthnRegistrationResponse(
                rp_id,
                origin,
                registration_response,
                challenge,
                trust_anchor_dir,
                trusted_attestation_cert_required,
                self_attestation_permitted,
                none_attestation_permitted,
                uv_required=False
            )
            # Verify webauthn registration response
            try:
                webauthn_credential = webauthn_registration_response.verify()

            except Exception as e:
                return jsonify({'message': str(e)}), 400

            # Store webauthn credentials
            storage = {
                'user_id': user['id'],
                'webauthn_ukey': ukey,
                'webauthn_pub_key': webauthn_credential.public_key,
                'webauthn_credential_id': webauthn_credential.credential_id,
                'webauthn_sign_count': webauthn_credential.sign_count,
                'webauthn_rp_id': rp_id
            }
            self._user_mfa.store_webauthn(storage)
            return jsonify({"message": 'OK'}), 200
            
        return mfa_blueprint
        
    ####################
    # Internal Methods #
    ####################
    def generate_challenge(self, challenge_len=32):
        return secrets.token_urlsafe(challenge_len)

    def generate_ukey(self):
        return self.generate_challenge(20)
