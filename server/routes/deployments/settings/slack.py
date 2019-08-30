import imp
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Slack:
    def __init__(self, credentials):
        # Init models
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)
        self._slack = imp.load_source('slack', '{}/models/deployments/slack.py'.format(credentials['path'])).Slack(credentials)

    def blueprint(self):
        # Init blueprint
        slack_blueprint = Blueprint('slack', __name__, template_folder='slack')

        @slack_blueprint.route('/deployments/slack', methods=['GET','PUT'])
        @jwt_required
        def slack_method():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get User Group ID
            group_id = self._users.get(get_jwt_identity())[0]['group_id']

            # Get Request Json
            slack_json = request.get_json()

            if request.method == 'GET':
                return self.get(group_id)
            elif request.method == 'PUT':
                return self.put(group_id, slack_json)

        return slack_blueprint

    def get(self, group_id):
        return jsonify({'data': self._slack.get(group_id)}), 200

    def put(self, group_id, data):
        if not self._slack.exist(group_id):
            self._slack.post(group_id, data)
        else:
            self._slack.put(group_id, data)
        return jsonify({'message': 'Changes saved successfully'}), 200

    def delete(self, group_id):
        self._slack.delete(group_id)