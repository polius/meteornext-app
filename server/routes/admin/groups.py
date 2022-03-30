import json
import time
import calendar
import requests
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.groups
import models.admin.users
import routes.inventory.environments
import routes.inventory.regions
import routes.inventory.servers
import routes.inventory.auxiliary
import routes.admin.settings

class Groups:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._groups = models.admin.groups.Groups(sql)
        self._users = models.admin.users.Users(sql)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        groups_blueprint = Blueprint('groups', __name__, template_folder='groups')

        @groups_blueprint.route('/admin/groups', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def groups_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(user['id'])
            elif request.method == 'PUT':
                return self.put(user['id'])
            elif request.method == 'DELETE':
                return self.delete()

        @groups_blueprint.route('/admin/groups/slack', methods=['GET'])
        @jwt_required()
        def groups_slack_test_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
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

        @groups_blueprint.route('/admin/groups/usage', methods=['GET'])
        @jwt_required()
        def groups_usage_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Return group usage
            return jsonify({'group': self._groups.get_usage(request.args['group_id'])}), 200

        return groups_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        if 'groupID' not in request.args:
            return jsonify({'data': self._groups.get()}), 200
        else:
            # Get group ID
            groupID = request.args['groupID']
            # Get group
            group = self._groups.get(group_id=groupID)
            # Get group owners
            group_owners = self._groups.get_owners(group_id=groupID)
            return jsonify({'group': group, 'owners': group_owners}), 200

    def post(self, user_id):
        # Get data
        data = request.get_json()

        # Get Group
        group = json.loads(data['group'])
        source_id = None
        if data['mode'] == 'clone':
            source_id = group['id']
            del group['id']

        # Check if group currently exists
        if self._groups.exist(group):
            return jsonify({'message': 'This group currently exists'}), 400

        # Create group
        group_id = self._groups.post(user_id, group)

        # Create owners
        if data['mode'] == 'new':
            self._groups.post_owners(group_id, data['owners']['add'])
        # Clone inventory
        elif data['mode'] == 'clone':
            self._groups.clone_inventory(user_id, source_id, group_id)

        return jsonify({'message': 'Group added' if data['mode'] == 'new' else 'Group cloned'}), 200

    def put(self, user_id):
        # Get data
        data = request.get_json()

        # Get Modified Group
        group = json.loads(data['group'])

        # Check if group currently exists
        if self._groups.exist(group):
            return jsonify({'message': 'This group currently exists'}), 400

        # Update group & owners
        self._groups.put(user_id, group)
        self._groups.post_owners(group['id'], data['owners']['add'])
        self._groups.delete_owners(group['id'], data['owners']['del'])
        return jsonify({'message': 'Group edited'}), 200

    def delete(self):
        groups = json.loads(request.args['groups'])
        # Check if exists users in this group
        for group in groups:
            users = self._groups.get_users(group_id=group)
            if len(users) > 0:
                return jsonify({'message': 'This group contains users'}), 400

        # Delete all groups
        for group in groups:
            self._groups.delete(group)
        return jsonify({'message': 'Selected groups deleted'}), 200
