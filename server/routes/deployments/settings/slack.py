import json
import time
import calendar
import requests
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
                return self.put(user['id'], user['group_id'], slack_json)

        @slack_blueprint.route('/deployments/slack/test', methods=['GET'])
        @jwt_required
        def slack_test_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Build Slack Message
            webhook_data = {
                "attachments": [
                    {
                        "text": "This is a test message.",
                        "color": 'good',
                        "ts": calendar.timegm(time.gmtime())
                    }
                ]
            }

            # Send Slack Message
            try:
                response = requests.post(request.args['webhook_url'], data=json.dumps(webhook_data), headers={'Content-Type': 'application/json'})
                if response.status_code != 200:
                    raise Exception()
            except Exception as e:
                return jsonify({'message': "Slack message could not be sent. Invalid Webhook URL"}), 400
            else:
                return jsonify({'message': "Slack message successfully sent"}), 200

        return slack_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id):
        return jsonify({'data': self._slack.get(group_id)}), 200

    def put(self, user_id, group_id, data):
        if not self._slack.exist(group_id):
            self._slack.post(user_id, group_id, data)
        else:
            self._slack.put(user_id, group_id, data)
        return jsonify({'message': 'Changes saved successfully'}), 200

    def delete(self, group_id):
        self._slack.delete(group_id)