import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Settings:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._settings = imp.load_source('settings', '{}/models/admin/settings.py'.format(credentials['path'])).Settings(credentials)

    def blueprint(self):
        # Init blueprint
        settings_blueprint = Blueprint('settings', __name__, template_folder='settings')

        @settings_blueprint.route('/admin/settings', methods=['GET','PUT'])
        @jwt_required
        def settings_method():
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['admin'] or not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            settings_json = request.get_json()

            if request.method == 'GET':
                return self.get()
            elif request.method == 'PUT':
                return self.put(settings_json)

        return settings_blueprint

    def get(self):
        return jsonify({'data': self._settings.get()}), 200

    def put(self, data):
        self._settings.post(data)
        return jsonify({'message': 'Changes saved successfully'}), 200
