import imp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Users:
    def __init__(self, credentials):
        # Init models
        self._groups = imp.load_source('groups', '{}/models/admin/groups.py'.format(credentials['path'])).Groups(credentials)
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)

    def blueprint(self):
        # Init blueprint
        users_blueprint = Blueprint('users', __name__, template_folder='users')

        @users_blueprint.route('/admin/users', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def users_method():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            user_json = request.get_json()

            if request.method == 'GET':
               return self.get()
            elif request.method == 'POST':
               return self.post(user_json)
            elif request.method == 'PUT':
                return self.put(user_json)
            elif request.method == 'DELETE':
                return self.delete(user_json)

        return users_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        return jsonify({'data': {'users': self._users.get(), 'groups': self._groups.get()}}), 200

    def post(self, data):
        user = self._users.get(data['username'])
        if len(user) > 0:
            return jsonify({'message': 'This user currently exists'}), 400
        else:
            data['password'] = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())
            self._users.post(data)
            return jsonify({'message': 'User added successfully'}), 200

    def put(self, data):
        user = self._users.get(data['current_username'])
        if len(user) == 0:
            return jsonify({'message': 'This user does not exist'}), 400

        elif data['current_username'] != data['username'] and self._users.exist(data['username']):
            return jsonify({'message': 'This user currently exists'}), 400
        elif data['password'] != user[0]['password']:
            data['password'] = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())
        self._users.put(data)
        return jsonify({'message': 'User edited successfully'}), 200

    def delete(self, data):
        self._users.delete(data)
        return jsonify({'message': 'Selected users deleted successfully'}), 200