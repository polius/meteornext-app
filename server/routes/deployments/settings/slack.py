from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.slack

class Slack:
    def __init__(self, app, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._slack = models.deployments.slack.Slack(sql)

    def license(self, value):
        self._license = value

    def blueprint(self):
        # Init blueprint
        slack_blueprint = Blueprint('slack', __name__, template_folder='slack')

        @slack_blueprint.route('/deployments/slack', methods=['GET','PUT'])
        @jwt_required
        def slack_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            slack_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['group_id'])
            elif request.method == 'PUT':
                return self.put(user['group_id'], slack_json)

        return slack_blueprint

    ####################
    # Internal Methods #
    ####################
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