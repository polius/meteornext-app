import imp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    regions_blueprint = Blueprint('regions', __name__, template_folder='regions')

    # Init models
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
    environments = imp.load_source('environments', '{}/models/deployments/environments.py'.format(credentials['path'])).Environments(credentials)
    regions = imp.load_source('regions', '{}/models/deployments/regions.py'.format(credentials['path'])).Regions(credentials)

    @regions_blueprint.route('/deployments/regions', methods=['GET','POST','PUT','DELETE'])
    @jwt_required
    def regions_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Get User
        user = users.get(get_jwt_identity())

        # Get Request Json
        region = request.get_json()

        if request.method == 'GET':
            return jsonify({'data': {'regions': regions.get(user[0]['group_id']), 'environments': environments.get(user[0]['group_id'])}}), 200

        elif request.method == 'POST':
            if regions.exist(user[0]['group_id'], {'environment': region['environment'], 'name': region['name']}):
                return jsonify({'message': 'This region currently exists'}), 400
            else:
                regions.post(user[0]['group_id'], region)
                return jsonify({'message': 'Region added successfully'}), 200

        elif request.method == 'PUT':
            if not regions.exist(user[0]['group_id'], {'environment': region['environment'], 'name': region['current_name']}):
                return jsonify({'message': 'This region does not exist'}), 400
            elif region['current_name'] != region['name'] and regions.exist(user[0]['group_id'], {'environment': region['environment'], 'name': region['name']}):
                return jsonify({'message': 'This new region name currently exists'}), 400
            else:
                regions.put(user[0]['group_id'], region)
                return jsonify({'message': 'Region edited successfully'}), 200

        elif request.method == 'DELETE':
            regions.delete(user[0]['group_id'], region)
            return jsonify({'message': 'Selected regions deleted successfully'}), 200

    return regions_blueprint