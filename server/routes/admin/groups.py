import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    groups_blueprint = Blueprint('groups', __name__, template_folder='groups')

    # Init models
    groups = imp.load_source('groups', '{}/models/admin/groups.py'.format(credentials['path'])).Groups(credentials)
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)

    @groups_blueprint.route('/admin/groups', methods=['GET','POST','PUT','DELETE'])
    @jwt_required
    def groups_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        if request.method == 'GET':
            return jsonify({'data': groups.get()}), 200

        group_json = request.get_json()

        if request.method == 'POST':
            groups.post(group_json)
            return jsonify({'message': 'Group added'}), 200
        elif request.method == 'PUT':
            if groups.exist(group_json):
                return jsonify({'message': 'This group currently exists'}), 400
            groups.put(group_json)
            return jsonify({'message': 'Group edited'}), 200
        elif request.method == 'DELETE':
            groups.delete(group_json)
            return jsonify({'message': 'Selected groups deleted'}), 200

    return groups_blueprint