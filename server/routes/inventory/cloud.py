from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
import json

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
            return jsonify({'message': 'Connection Successful'}), 200

        return cloud_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        cloud = self._cloud.get(user['id'], user['group_id'])
        # Check Inventory Secured
        if user['inventory_secured'] and not user['owner']:
            cloud_secured = []
            for c in cloud:
                if c['shared']:
                    cloud_secured.append({"id": c['id'], "name": c['name'], "shared": c['shared']})
                else:
                    cloud_secured.append(c)
            return jsonify({'data': cloud_secured}), 200
        return jsonify({'data': cloud}), 200

    def post(self, user, cloud):
        # Check privileges
        if cloud['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check cloud keys exists
        if self._cloud.exist(user['id'], user['group_id'], cloud):
            return jsonify({'message': 'This cloud key name currently exists'}), 400
        # Add cloud key
        self._cloud.post(user['id'], user['group_id'], cloud)
        return jsonify({'message': 'Cloud key added successfully'}), 200

    def put(self, user, cloud):
        # Check privileges
        if cloud['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check cloud key exists
        if self._cloud.exist(user['id'], user['group_id'], cloud):
            return jsonify({'message': 'This cloud key name currently exists'}), 400
        # Edit cloud key
        self._cloud.put(user['id'], user['group_id'], cloud)
        return jsonify({'message': 'Cloud key edited successfully'}), 200

    def delete(self, user):
        data = json.loads(request.args['cloud'])
        # Check privileges
        for cloud in data:
            cloud = self._cloud.get(user['id'], user['group_id'], cloud)
            if len(cloud) > 0 and cloud[0]['shared'] and not user['owner']:
                return jsonify({'message': "Insufficient privileges"}), 401
        # Delete cloud keys
        for cloud in data:
            self._cloud.delete(user['id'], user['group_id'], cloud)
        return jsonify({'message': 'Selected cloud keys deleted successfully'}), 200
