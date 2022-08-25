from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user
import json
import boto3

import models.admin.users
import models.admin.inventory.inventory
import models.admin.inventory.cloud
import routes.admin.settings

class Cloud:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._inventory = models.admin.inventory.inventory.Inventory(sql)
        self._cloud = models.admin.inventory.cloud.Cloud(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(self._license, sql)

    def blueprint(self):
        # Init blueprint
        admin_cloud_blueprint = Blueprint('admin_cloud', __name__, template_folder='admin_cloud')

        @admin_cloud_blueprint.route('/admin/inventory/cloud', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def admin_cloud_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
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
                return self.post(user)
            elif request.method == 'PUT':
                return self.put(user)
            elif request.method == 'DELETE':
                return self.delete()

        @admin_cloud_blueprint.route('/admin/inventory/cloud/test', methods=['POST'])
        @jwt_required()
        def admin_cloud_test_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            # Test Cloud Key
            return self.test(data)

        return admin_cloud_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        # Get args
        group_id = request.args['group_id'] if 'group_id' in request.args else None
        user_id = request.args['user_id'] if 'user_id' in request.args else None
        # Get cloud
        cloud = self._cloud.get(group_id=group_id, user_id=user_id)
        # Parse Buckets
        for c in cloud:
            c['buckets'] = c['buckets'].split(',') if c['buckets'] else []
        # Protect Secret Keys
        for c in cloud:
            c['secret_key'] = {} if c['secret_key'] else None
        # Return data
        return jsonify({'cloud': cloud}), 200

    def post(self, user):
        # Get data
        cloud = request.get_json()
        # Check group & user
        if not self._inventory.exist_group(cloud['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not cloud['shared'] and not self._inventory.exist_user(cloud['group_id'], cloud['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check cloud exists
        if self._cloud.exist(cloud):
            return jsonify({'message': 'This cloud key name currently exists'}), 400
        # Parse buckets
        cloud['buckets'] = ','.join([i.strip() for i in cloud['buckets']]) if len(cloud['buckets']) > 0 else None
        # Parse secret key
        if type(cloud['secret_key']) is dict:
            origin = self._cloud.get(cloud_id=cloud['id'])[0]
            cloud['secret_key'] = origin['secret_key']
        # Add cloud key
        self._cloud.post(user, cloud)
        return jsonify({'message': 'Cloud key added'}), 200

    def put(self, user):
        # Get data
        cloud = request.get_json()
        # Check group & user
        if not self._inventory.exist_group(cloud['group_id']):
            return jsonify({'message': 'This group does not exist'}), 400
        if not cloud['shared'] and not self._inventory.exist_user(cloud['group_id'], cloud['owner_id']):
            return jsonify({'message': 'This user does not exist in the provided group'}), 400
        # Check cloud key exists
        if self._cloud.exist(cloud):
            return jsonify({'message': 'This cloud key name currently exists'}), 400
        # Parse buckets
        cloud['buckets'] = ','.join([i.strip() for i in cloud['buckets']]) if len(cloud['buckets']) > 0 else None
        # Parse secret key
        cloud['secret_key'] = '<secret_key>' if type(cloud['secret_key']) is dict else cloud['secret_key']
        # Edit cloud key
        self._cloud.put(user, cloud)
        return jsonify({'message': 'Cloud key edited'}), 200

    def delete(self):
        data = json.loads(request.args['cloud'])
        # Delete cloud keys
        for cloud in data:
            self._cloud.delete(cloud)
        return jsonify({'message': 'Selected cloud keys deleted'}), 200

    def test(self, data):
        # Get Cloud Key
        if 'id' in data:
            cloud = self._cloud.get(cloud_id=data['id'])
            if len(cloud) == 0:
                return jsonify({'message': "Can't test the cloud key. This key does not exist in your inventory."}), 400
            cloud_key = { 'access_key': cloud[0]['access_key'], 'secret_key': cloud[0]['secret_key']}
        else:
            cloud_key = { 'access_key': data['access_key'], 'secret_key': data['secret_key']}

        # Test Cloud Key
        sts = boto3.client('sts', aws_access_key_id=cloud_key['access_key'], aws_secret_access_key=cloud_key['secret_key'])
        try:
            sts.get_caller_identity()
            return jsonify({'message': 'Credentials are valid'}), 200
        except Exception:
            return jsonify({'message': 'Credentials are not valid'}), 400
