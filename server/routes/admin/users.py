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

        # Get Request Json
        data = request.get_json()

        # Get User from Database
        user = users.get(data['username'])

        # Encrypt password using bcrypt
        encrypted_password = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())

        if request.method == 'POST':
            if len(user) > 0:
                return jsonify({'message': 'This user currently exists'}), 400
            else:
                data['password'] = encrypted_password
                users.post(data)
                return jsonify({'message': 'User added successfully'}), 200

        elif request.method == 'PUT':
            if len(user) == 0:
                return jsonify({'message': 'This user does not exist'}), 400
            elif data['current_username'] != data['username'] and users.exist(data['username']):
                return jsonify({'message': 'This user currently exists'}), 400
            elif data['password'] != user['password']:
                data['password'] = encrypted_password
            users.put(data)
            return jsonify({'message': 'User edited successfully'}), 200

        elif request.method == 'DELETE':
            if len(user) == 0:
                return jsonify({'message': 'This user does not exist'}), 400
            else:
                users.delete(data)
                return jsonify({'message': 'Selected users deleted successfully'}), 200

    return users_blueprint