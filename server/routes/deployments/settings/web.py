import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Web:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._web = imp.load_source('web', '{}/models/deployments/web.py'.format(credentials['path'])).Web(credentials)

    def blueprint(self):
        # Init blueprint
        web_blueprint = Blueprint('web', __name__, template_folder='web')

        @web_blueprint.route('/deployments/web', methods=['GET','PUT'])
        @jwt_required
        def web_method():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User Group ID
            group_id = self._users.get(get_jwt_identity())[0]['group_id']

            # Get Request Json
            web_json = request.get_json()

            if request.method == 'GET':
                return self.get(group_id)
            elif request.method == 'PUT':
                return self.put(group_id, web_json)

        return web_blueprint

    def get(self, group_id):
        return jsonify({'data': self._web.get(group_id)}), 200

    def put(self, group_id, data):
        if not self._web.exist(group_id):
            self._web.post(group_id, data)
        else:
            self._web.put(group_id, data)
        return jsonify({'message': 'Changes saved successfully'}), 200

    def delete(self, group_id):
        self._web.delete(group_id)
