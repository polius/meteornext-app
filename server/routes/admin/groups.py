import imp
from flask import Blueprint, jsonify
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    groups_blueprint = Blueprint('groups', __name__, template_folder='groups')

    # Init models
    groups = imp.load_source('groups', '{}/models/groups.py'.format(credentials['path'])).Groups(credentials)
    users = imp.load_source('users', '{}/models/users.py'.format(credentials['path'])).Users(credentials)

    @groups_blueprint.route('/admin/groups', methods=['GET'])
    @jwt_required
    def get_groups():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'status': 'failure', 'message': 'Insufficient Privileges'})
        return jsonify({'status': 'success', 'data': groups.get()})

    return groups_blueprint