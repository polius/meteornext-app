import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    s3_blueprint = Blueprint('s3', __name__, template_folder='s3')

    # Init models
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
    s3 = imp.load_source('s3', '{}/models/deployments/s3.py'.format(credentials['path'])).S3(credentials)

    @s3_blueprint.route('/deployments/s3', methods=['GET','PUT'])
    @jwt_required
    def s3_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Get User
        user = users.get(get_jwt_identity())

        # Get Request Json
        s3_json = request.get_json()

        if request.method == 'GET':
            return jsonify({'data': s3.get(user[0]['group_id'])}), 200

        elif request.method == 'PUT':
            if not s3.exist(user[0]['group_id']):
                s3.post(user[0]['group_id'], s3_json)
            else:
                s3.put(user[0]['group_id'], s3_json)
            return jsonify({'message': 'Changes saved successfully'}), 200

    return s3_blueprint