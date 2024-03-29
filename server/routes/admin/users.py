import json
import string
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.groups
import models.admin.users
import models.admin.settings
import models.utils.imports
import routes.admin.settings
import apps.imports.imports

class Users:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._groups = models.admin.groups.Groups(sql)
        self._users = models.admin.users.Users(sql)
        self._settings = models.admin.settings.Settings(sql, self._license)
        self._imports = models.utils.imports.Imports(sql, self._license)
        # Init routes
        self._settings_route = routes.admin.settings.Settings(self._license, sql)
        # Init apps
        self._import_app = apps.imports.imports.Imports(sql)

    def blueprint(self):
        # Init blueprint
        users_blueprint = Blueprint('users', __name__, template_folder='users')

        @users_blueprint.route('/admin/users', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def users_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings_route.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(user['id'])
            elif request.method == 'PUT':
                return self.put(user['id'])
            elif request.method == 'DELETE':
                return self.delete()

        return users_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        if 'username' in request.args:
            return jsonify({'data': self._users.get(request.args['username'])})
        return jsonify({'data': {'users': self._users.get(), 'groups': self._groups.get()}}), 200

    def post(self, user_id):
        # Get data
        data = request.get_json()

        # Get user
        user = self._users.get(data['username'])

        # Check unique user
        if len(user) > 0:
            return jsonify({'message': 'This user currently exists'}), 400

        # Check Password Policy
        try:
            self.check_password_policy(data['password'])
        except Exception as e:
            return jsonify({'message': str(e)}), 400
        
        # Hash password
        data['password'] = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())

        # Add user
        self._users.post(user_id, data)
        return jsonify({'message': 'User added'}), 200

    def put(self, user_id):
        # Get data
        data = request.get_json()

        # Get user
        user = self._users.get(data['current_username'])

        # Check unique user
        if len(user) == 0:
            return jsonify({'message': 'This user does not exist'}), 400
        if data['current_username'] != data['username'] and self._users.exist(data['username']):
            return jsonify({'message': 'This user currently exists'}), 400

        # Check Password
        if 'password' not in data or data['password'] is None or len(data['password'].strip()) == 0:
            data['password'] = None
        elif data['password'] != user[0]['password']:
            try:
                self.check_password_policy(data['password'])
                data['password'] = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())
            except Exception as e:
                return jsonify({'message': str(e)}), 400

        # Clean Shared Inventory References if the group has changed
        if user[0]['group'] != data['group']:
            self._users.clean_shared(user[0]['id'], data['group'])

        # Edit user
        self._users.put(user_id, data)
        return jsonify({'message': 'User edited'}), 200

    def delete(self):
        # Get users list
        users = json.loads(request.args['users'])

        # Stop current imports
        # for username in users:
        #     user = self._users.get(username)
        #     imports = self._imports.get(user_id=user[0]['id'])
        #     for i in imports:
        #         if i['status'] == 'IN PROGRESS':
        #             self._import_app.stop(i['pid'])

        # Remove user
        self._users.delete(users)
        return jsonify({'message': 'Selected users deleted'}), 200

    def check_password_policy(self, password):
        security = json.loads(self._settings.get(setting_name='SECURITY'))
        special_characters = set(string.punctuation)
        if len(password) < int(security['password_min']):
            raise Exception(f"The password must be at least {security['password_min']} characters long.")
        if security['password_lowercase'] and not any(c.islower() for c in password):
            raise Exception('The password must contain a lowercase letter.')
        if security['password_uppercase'] and not any(c.isupper() for c in password):
            raise Exception('The password must contain a uppercase letter.')
        if security['password_number'] and not any(c.isnumeric() for c in password):
            raise Exception('The password must contain a number.')
        if security['password_special'] and not any(c in special_characters for c in password):
            raise Exception('The password must contain a special character.')
