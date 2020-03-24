import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.groups
import models.admin.users
import routes.inventory.environments
import routes.inventory.regions
import routes.inventory.servers
import routes.inventory.auxiliary
import routes.inventory.slack
import routes.admin.settings

class Groups:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._groups = models.admin.groups.Groups(sql)
        self._users = models.admin.users.Users(sql)

        # Init routes
        self._environments = routes.inventory.environments.Environments(app, sql, license)
        self._regions = routes.inventory.regions.Regions(app, sql, license)
        self._servers = routes.inventory.servers.Servers(app, sql, license)
        self._auxiliary = routes.inventory.auxiliary.Auxiliary(app, sql, license)
        self._slack = routes.inventory.slack.Slack(app, sql, license)
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        groups_blueprint = Blueprint('groups', __name__, template_folder='groups')

        @groups_blueprint.route('/admin/groups', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
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
            if not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            group_json = request.get_json()

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(user['id'], group_json)
            elif request.method == 'PUT':
                return self.put(user['id'], group_json)
            elif request.method == 'DELETE':
                return self.delete(group_json)

        return groups_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id=None):
        if group_id is None and 'groupID' not in request.args:
            return jsonify({'data': self._groups.get()}), 200
        else:
            # Get group ID
            groupID = request.args['groupID'] if group_id is None else group_id
            return jsonify({'data': self._groups.get(group_id=groupID)}), 200

    def post(self, user_id, data):
        # Get Group
        group = json.loads(data['group'])

        # Check if group currently exists
        if self._groups.exist(group):
            return jsonify({'message': 'This group currently exists'}), 400

        # Create group
        self._groups.post(user_id, group)
        return jsonify({'message': 'Group added'}), 200

    def put(self, user_id, data):
        # Get Modified Group
        group = json.loads(data['group'])

        # Get Current Group
        current = self.get(group['id'])[0].get_json()

        if group['name'] != current['group'][0]['name'] and self._groups.exist(group):
            return jsonify({'message': 'This group currently exists'}), 400

        # Calculate diff
        diff_group = self.__diff(current['group'], [group])

        # Apply diff
        if len(diff_group['change']) > 0:
            self._groups.put(user_id, diff_group['change'][0])

        return jsonify({'message': 'Group edited'}), 200

    def delete(self, data):
        for group in data:
            # Get group ID
            group_id = self._groups.get(group_id=group)[0]['id']

            # Delete all group elements
            self._slack.delete(group_id)
            self._auxiliary.remove(group_id)
            self._servers.remove(group_id)
            self._regions.remove(group_id)
            self._environments.remove(group_id)
            self._groups.delete(group)
        return jsonify({'message': 'Selected groups deleted'}), 200

    def __diff(self, dict_list1, dict_list2):
        diff = {'add': [], 'change': [], 'remove': []}

        for i in dict_list2:
            if 'id' not in i:
                diff['add'].append(i)
            else:
                match = [j for j in dict_list1 if i['id'] == j['id']]
                if len(match) > 0 and match[0] != i:
                    diff['change'].append(i)

        for i in dict_list1:
            match = any([1 for j in dict_list2 if 'id' in j and i['id'] == j['id']])
            if not match and not any([1 for j in diff['change'] if i['id'] == j['id']]):
                diff['remove'].append(i)
        return diff