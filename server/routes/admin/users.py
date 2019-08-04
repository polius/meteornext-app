import imp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    users_blueprint = Blueprint('users', __name__, template_folder='users')

    # Init models
    groups = imp.load_source('groups', '{}/models/groups.py'.format(credentials['path'])).Groups(credentials)
    users = imp.load_source('users', '{}/models/users.py'.format(credentials['path'])).Users(credentials)

    @users_blueprint.route('/admin/users', methods=['GET','POST','PUT','DELETE'])
    @jwt_required
    def users_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        if request.method == 'GET':
            return jsonify({'data': users.get()}), 200

        data = request.get_json()

        # Encrypt password using bcrypt
        data['password'] = bcrypt.hashpw(data['password'].encode('utf8'))

        if request.method == 'POST':
            users.post(data)
            return jsonify({'message': 'User added'}), 200
        elif request.method == 'PUT':
            if users.exist(data):
                return jsonify({'message': 'This user currently exists'}), 400
            users.put(data)
            return jsonify({'message': 'User edited'}), 200
        elif request.method == 'DELETE':
            users.delete(data)
            return jsonify({'message': 'Selected users deleted'}), 200

    return users_blueprint