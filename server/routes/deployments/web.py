import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    web_blueprint = Blueprint('web', __name__, template_folder='web')

    # Init models
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
    web = imp.load_source('web', '{}/models/deployments/web.py'.format(credentials['path'])).Web(credentials)

    @web_blueprint.route('/deployments/web', methods=['GET','PUT'])
    @jwt_required
    def web_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Get User
        user = users.get(get_jwt_identity())

        # Get Request Json
        web_json = request.get_json()

        if request.method == 'GET':
            return jsonify({'data': web.get(user[0]['group_id'])}), 200

        elif request.method == 'PUT':
            if not web.exist(user[0]['group_id']):
                web.post(user[0]['group_id'], web_json)
            else:
                web.put(user[0]['group_id'], web_json)
            return jsonify({'message': 'Changes saved successfully'}), 200

    return web_blueprint