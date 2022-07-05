import json
import time
import calendar
import requests
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.monitoring.monitoring
import models.monitoring.monitoring_settings

class Monitoring:
    def __init__(self, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._monitoring = models.monitoring.monitoring.Monitoring(sql, license)
        self._monitoring_settings = models.monitoring.monitoring_settings.Monitoring_Settings(sql)

    def blueprint(self):
        # Init blueprint
        monitoring_blueprint = Blueprint('monitoring', __name__, template_folder='monitoring')

        @monitoring_blueprint.route('/monitoring', methods=['GET','PUT'])
        @jwt_required()
        def monitoring_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['monitoring_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'PUT':
                return self.put(user)

        @monitoring_blueprint.route('/monitoring/settings', methods=['GET','PUT'])
        @jwt_required()
        def monitoring_settings_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['monitoring_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return jsonify({'settings': self._monitoring_settings.get(user)}), 200
            elif request.method == 'PUT':
                self._monitoring_settings.put(user, request.get_json())
                return jsonify({'message': 'Settings saved'}), 200

        @monitoring_blueprint.route('/monitoring/slack', methods=['GET'])
        @jwt_required()
        def monitoring_slack_test_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['monitoring_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Build Slack Message
            webhook_data = {
                "attachments": [
                    {
                        "text": "Yay, It works!",
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
                return jsonify({'message': "Slack message sent"}), 200

        return monitoring_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        server_id = request.args['server_id'] if 'server_id' in request.args else None
        if server_id:
            servers = self._monitoring.get(user, server_id)
            settings = self._monitoring_settings.get(user)
            return jsonify({'server': servers, 'settings': settings}), 200
        else:
            servers = self._monitoring.get_monitoring(user)
            events = self._monitoring.get_events(user)
            return jsonify({'servers': servers, 'events': events}), 200

    def put(self, user):
        self._monitoring.put_monitor(user, request.get_json())
        return jsonify({'message': 'Servers saved'}), 200
