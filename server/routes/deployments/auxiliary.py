import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Auxiliary:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._auxiliary = imp.load_source('auxiliary', '{}/models/deployments/auxiliary.py'.format(credentials['path'])).Auxiliary(credentials)

    def blueprint(self):
        # Init blueprint
        auxiliary_blueprint = Blueprint('auxiliary', __name__, template_folder='auxiliary')

        @auxiliary_blueprint.route('/deployments/auxiliary', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def auxiliary_method():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User Group ID
            group_id = self._users.get(get_jwt_identity())[0]['group_id']

            # Get Request Json
            auxiliary_json = request.get_json()

            if request.method == 'GET':
                return get(group_id)
            elif request.method == 'POST':
                return post(group_id, auxiliary_json)
            elif request.method == 'PUT':
                return put(group_id, auxiliary_json)
            elif request.method == 'DELETE':
                return delete(group_id, auxiliary_json)

        return auxiliary_blueprint

    def get(self, group_id):
        return jsonify({'data': self._auxiliary.get(group_id)}), 200

    def post(self, group_id, data):
        if self._auxiliary.exist(group_id, {'name': data['name']}):
            return jsonify({'message': 'This auxiliary connection currently exists'}), 400
        else:
            self._auxiliary.post(group_id, data)
            return jsonify({'message': 'Auxiliary connection added successfully'}), 200

    def put(self, group_id, data):
        if data['current_name'] != data['name'] and self._auxiliary.exist(group_id, {'name': data['name']}):
            return jsonify({'message': 'This new auxiliary connection name currently exists'}), 400
        else:
            self._auxiliary.put(group_id, data)
            return jsonify({'message': 'Auxiliary connection edited successfully'}), 200

    def delete(self, group_id, data):
        self._auxiliary.delete(group_id, data)
        return jsonify({'message': 'Selected auxiliary connections deleted successfully'}), 200

    def remove(self, group_id):
        self._auxiliary.remove(group_id)