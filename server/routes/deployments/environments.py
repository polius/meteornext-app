import imp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    environments_blueprint = Blueprint('environments', __name__, template_folder='environments')

    # Init models
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
    environments = imp.load_source('environments', '{}/models/deployments/environments.py'.format(credentials['path'])).Environments(credentials)

    @environments_blueprint.route('/deployments/environments', methods=['GET','POST','PUT','DELETE'])
    @jwt_required
    def environments_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Get User
        user = users.get(get_jwt_identity())

        # Get Request Json
        environment_json = request.get_json()

        if request.method == 'GET':
            return jsonify({'data': environments.get(user[0]['group_id'])}), 200

        elif request.method == 'POST':
            if environments.exist(user[0]['group_id'], environment_json):
                return jsonify({'message': 'This environment currently exists'}), 400
            else:
                environments.post(user[0]['group_id'], environment_json)
                return jsonify({'message': 'Environment added successfully'}), 200

        elif request.method == 'PUT':
            if not environments.exist(user[0]['group_id'], environment_json):
                return jsonify({'message': 'This environment does not exist'}), 400
            elif data['current_name'] != data['name'] and environments.exist(user[0]['group_id'], environment_json):
                return jsonify({'message': 'This new environment name currently exists'}), 400
            else:
                environments.put(user[0]['group_id'], environment_json)
                return jsonify({'message': 'Environment edited successfully'}), 200

        elif request.method == 'DELETE':
            environments.delete(user[0]['group_id'], environment_json)
            return jsonify({'message': 'Selected environments deleted successfully'}), 200

    return environments_blueprint