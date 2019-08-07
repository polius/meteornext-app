import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    auxiliary_blueprint = Blueprint('auxiliary', __name__, template_folder='auxiliary')

    # Init models
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
    auxiliary = imp.load_source('auxiliary', '{}/models/deployments/auxiliary.py'.format(credentials['path'])).Auxiliary(credentials)

    @auxiliary_blueprint.route('/deployments/auxiliary', methods=['GET','POST','PUT','DELETE'])
    @jwt_required
    def auxiliary_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Get User
        user = users.get(get_jwt_identity())

        # Get Request Json
        auxiliary_json = request.get_json()

        if request.method == 'GET':
            return jsonify({'data': auxiliary.get(user[0]['group_id'])}), 200

        elif request.method == 'POST':
            if auxiliary.exist(user[0]['group_id'], {'name': auxiliary_json['name']}):
                return jsonify({'message': 'This auxiliary connection currently exists'}), 400
            else:
                auxiliary.post(user[0]['group_id'], auxiliary_json)
                return jsonify({'message': 'Auxiliary connection added successfully'}), 200

        elif request.method == 'PUT':
            if not auxiliary.exist(user[0]['group_id'], {'name': auxiliary_json['current_name']}):
                return jsonify({'message': 'This auxiliary connection does not exist'}), 400
            elif auxiliary_json['current_name'] != auxiliary_json['name'] and auxiliary.exist(user[0]['group_id'], {'name': auxiliary_json['name']}):
                return jsonify({'message': 'This new auxiliary connection name currently exists'}), 400
            else:
                auxiliary.put(user[0]['group_id'], auxiliary_json)
                return jsonify({'message': 'Auxiliary connection edited successfully'}), 200

        elif request.method == 'DELETE':
            auxiliary.delete(user[0]['group_id'], auxiliary_json)
            return jsonify({'message': 'Selected auxiliary connections deleted successfully'}), 200

    return auxiliary_blueprint