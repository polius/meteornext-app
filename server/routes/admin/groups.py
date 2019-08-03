import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    groups_blueprint = Blueprint('groups', __name__, template_folder='groups')

    # Init models
    groups = imp.load_source('groups', '{}/models/groups.py'.format(credentials['path'])).Groups(credentials)
    users = imp.load_source('users', '{}/models/users.py'.format(credentials['path'])).Users(credentials)

    @groups_blueprint.route('/admin/groups', methods=['GET','POST','PUT','DELETE'])
    @jwt_required
    def groups_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'status': 'error', 'message': 'Insufficient Privileges'})

        if request.method == 'GET':
            return jsonify({'status': 'success', 'data': groups.get()})

        data = request.get_json()

        if request.method == 'POST':
            groups.post(data)
            return jsonify({'status': 'success', 'message': 'Group added'})
        elif request.method == 'PUT':
            if groups.exist(data):
                return jsonify({'status': 'warning', 'message': 'This group currently exists'})
            groups.put(data)
            return jsonify({'status': 'success', 'message': 'Group edited'})
        elif request.method == 'DELETE':
            groups.delete(data)
            return jsonify({'status': 'success', 'message': 'Selected groups deleted'})

    return groups_blueprint