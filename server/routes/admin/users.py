import imp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    users_blueprint = Blueprint('users', __name__, template_folder='users')

    # Init models
    groups = imp.load_source('groups', '{}/models/admin/groups.py'.format(credentials['path'])).Groups(credentials)
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)

    @users_blueprint.route('/admin/users', methods=['GET','POST','PUT','DELETE'])
    @jwt_required
    def users_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Get Request Json
        user_json = request.get_json()

        if request.method == 'GET':
            return jsonify({'data': {'users': users.get(), 'groups': groups.get()}}), 200

        elif request.method == 'POST':
            user = users.get(user_json['username'])
            if len(user) > 0:
                return jsonify({'message': 'This user currently exists'}), 400
            else:
                user_json['password'] = bcrypt.hashpw(user_json['password'].encode('utf8'), bcrypt.gensalt())
                users.post(user_json)
                return jsonify({'message': 'User added successfully'}), 200

        elif request.method == 'PUT':
            user = users.get(user_json['current_username'])
            if len(user) == 0:
                return jsonify({'message': 'This user does not exist'}), 400

            elif user_json['current_username'] != user_json['username'] and users.exist(user_json['username']):
                return jsonify({'message': 'This user currently exists'}), 400
            elif user_json['password'] != user_json[0]['password']:
                user_json['password'] = bcrypt.hashpw(user_json['password'].encode('utf8'), bcrypt.gensalt())
            users.put(user_json)
            return jsonify({'message': 'User edited successfully'}), 200

        elif request.method == 'DELETE':
            users.delete(user_json)
            return jsonify({'message': 'Selected users deleted successfully'}), 200

    return users_blueprint