from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
import json
import boto3

import models.admin.users
import models.inventory.cloud

class Cloud:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._cloud = models.inventory.cloud.Cloud(sql)

    def blueprint(self):
        # Init blueprint
        cloud_blueprint = Blueprint('cloud', __name__, template_folder='cloud')

        @cloud_blueprint.route('/inventory/cloud', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def cloud_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            data = request.get_json()

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user, data)
            elif request.method == 'PUT':
                return self.put(user, data)
            elif request.method == 'DELETE':
                return self.delete(user)

        @cloud_blueprint.route('/inventory/cloud/test', methods=['POST'])
        @jwt_required()
        def cloud_test_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            # Test Cloud Key
            return self.test(user, data)

        return cloud_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        # Get Cloud
        cloud = self._cloud.get(user['id'], user['group_id'])
        # Parse Buckets
        for c in cloud:
            c['buckets'] = c['buckets'].split(',') if c['buckets'] else []
        # Protect Secret Keys
        for c in cloud:
            c['secret_key'] = {} if c['secret_key'] else None
        # Check Inventory Secured
        cloud_secured = []
        for c in cloud:
            if c['secured']:
                cloud_secured.append({"id": c['id'], "name": c['name'], "type": c['type'], "shared": c['shared'], "secured": c['secured'],})
            else:
                cloud_secured.append(c)
        return jsonify({'data': cloud_secured}), 200

    def post(self, user, cloud):
        # Check privileges
        if cloud['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check cloud keys exists
        if self._cloud.exist(user['id'], user['group_id'], cloud):
            return jsonify({'message': 'This cloud key name currently exists'}), 400
        # Parse buckets
        cloud['buckets'] = ','.join([i.strip() for i in cloud['buckets']]) if len(cloud['buckets']) > 0 else None
        # Parse secret key
        if type(cloud['secret_key']) is dict:
            origin = self._cloud.get(user['id'], user['group_id'], cloud['id'])[0]
            cloud['secret_key'] = origin['secret_key']
        # Add cloud key
        self._cloud.post(user['id'], user['group_id'], cloud)
        return jsonify({'message': 'Cloud key added'}), 200

    def put(self, user, cloud):
        # Check cloud
        check = self._cloud.get(user['id'], user['group_id'], cloud['id'])
        if len(check) == 0:
            return jsonify({'message': "The cloud key does not exist in your inventory"}), 400
        # Check privileges
        if check[0]['secured'] or (cloud['shared'] and not user['owner']):
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check cloud key exists
        if self._cloud.exist(user['id'], user['group_id'], cloud):
            return jsonify({'message': 'This cloud key name currently exists'}), 400
        # Parse buckets
        cloud['buckets'] = ','.join([i.strip() for i in cloud['buckets']]) if len(cloud['buckets']) > 0 else None
        # Parse secret key
        cloud['secret_key'] = '<secret_key>' if type(cloud['secret_key']) is dict else cloud['secret_key']
        # Edit cloud key
        self._cloud.put(user['id'], user['group_id'], cloud)
        return jsonify({'message': 'Cloud key edited'}), 200

    def delete(self, user):
        data = json.loads(request.args['cloud'])
        # Check privileges
        for cloud in data:
            cloud = self._cloud.get(user['id'], user['group_id'], cloud)
            if len(cloud) > 0 and cloud[0]['secured'] or (cloud[0]['shared'] and not user['owner']):
                return jsonify({'message': "Insufficient privileges"}), 401
        # Delete cloud keys
        for cloud in data:
            self._cloud.delete(user['id'], user['group_id'], cloud)
        return jsonify({'message': 'Selected cloud keys deleted'}), 200

    def test(self, user, data):
        # Get Cloud Key
        if 'id' in data:
            cloud = self._cloud.get(group_id=user['group_id'], user_id=user['id'], cloud_id=data['id'])
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
