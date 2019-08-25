import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class S3:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._s3 = imp.load_source('s3', '{}/models/deployments/settings/s3.py'.format(credentials['path'])).S3(credentials)

    def blueprint(self):
        # Init blueprint
        s3_blueprint = Blueprint('s3', __name__, template_folder='s3')

        @s3_blueprint.route('/deployments/s3', methods=['GET','PUT'])
        @jwt_required
        def s3_method():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User
            group_id = self._users.get(get_jwt_identity())[0]['group_id']

            # Get Request Json
            s3_json = request.get_json()

            if request.method == 'GET':
                return self.get(group_id)
            elif request.method == 'PUT':
                return self.put(group_id, s3_json)

        return s3_blueprint

    def get(self, group_id):
        return jsonify({'data': self._s3.get(group_id)}), 200

    def put(self, group_id, data):
        if not self._s3.exist(group_id):
            self._s3.post(group_id, data)
        else:
            self._s3.put(group_id, data)
        return jsonify({'message': 'Changes saved successfully'}), 200

    def delete(self, group_id):
        self._s3.delete(group_id)