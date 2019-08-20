import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Profile:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)

    def blueprint(self):
        # Init blueprint
        profile_blueprint = Blueprint('profile', __name__, template_folder='profile')

        @profile_blueprint.route('/profile', methods=['GET','PUT'])
        @jwt_required
        def profile_method():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User
            user = self._users.get(get_jwt_identity())

            # Get Request Json
            profile_json = request.get_json()

            if request.method == 'GET':
                return jsonify({'data': user}), 200

            elif request.method == 'PUT':
                if user[0]['password'] != profile_json['password']:
                    profile_json['password'] = bcrypt.hashpw(profile_json['password'].encode('utf8'), bcrypt.gensalt())
                else:
                    profile_json['password'] = user[0]['password']
                self._users.put_profile({'username': get_jwt_identity(), 'email': profile_json['email'], 'password': profile_json['password']})
                return jsonify({'message': 'Changes saved successfully'}), 200

        return profile_blueprint