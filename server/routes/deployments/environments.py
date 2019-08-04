import imp
import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    environments_blueprint = Blueprint('environments', __name__, template_folder='environments')

    # Init models
    environments = imp.load_source('environments', '{}/models/deployments/environments.py'.format(credentials['path'])).Environments(credentials)

    @environments_blueprint.route('/deployments/environments', methods=['GET','POST','PUT','DELETE'])
    @jwt_required
    def environments_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Get Request Json
        data = request.get_json()

        if request.method == 'GET':
            return jsonify({'data': users.get()}), 200

        elif request.method == 'POST':
            user = users.get(data['username'])
            if len(user) > 0:
                return jsonify({'message': 'This user currently exists'}), 400
            else:
                data['password'] = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())
                users.post(data)
                return jsonify({'message': 'User added successfully'}), 200

        elif request.method == 'PUT':
            user = users.get(data['current_username'])
            if len(user) == 0:
                return jsonify({'message': 'This user does not exist'}), 400

            elif data['current_username'] != data['username'] and users.exist(data['username']):
                return jsonify({'message': 'This user currently exists'}), 400
            elif data['password'] != user[0]['password']:
                data['password'] = bcrypt.hashpw(data['password'].encode('utf8'), bcrypt.gensalt())
            users.put(data)
            return jsonify({'message': 'User edited successfully'}), 200

        elif request.method == 'DELETE':
            users.delete(data)
            return jsonify({'message': 'Selected users deleted successfully'}), 200

    return environments_blueprint