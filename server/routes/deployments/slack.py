import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    slack_blueprint = Blueprint('slack', __name__, template_folder='slack')

    # Init models
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
    slack = imp.load_source('slack', '{}/models/deployments/slack.py'.format(credentials['path'])).Slack(credentials)

    @slack_blueprint.route('/deployments/slack', methods=['GET','PUT'])
    @jwt_required
    def slack_method():
        # Check user privileges
        is_admin = users.is_admin(get_jwt_identity())
        if not is_admin:
            return jsonify({'message': 'Insufficient Privileges'}), 401

        # Get User
        user = users.get(get_jwt_identity())

        # Get Request Json
        slack_json = request.get_json()

        if request.method == 'GET':
            return jsonify({'data': slack.get(user[0]['group_id'])}), 200

        elif request.method == 'PUT':
            if not slack.exist(user[0]['group_id']):
                slack.post(user[0]['group_id'], slack_json)
            else:
                slack.put(user[0]['group_id'], slack_json)
            return jsonify({'message': 'Changes saved successfully'}), 200

    return slack_blueprint