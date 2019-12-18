import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.groups
import models.admin.users
import routes.deployments.settings.environments
import routes.deployments.settings.regions
import routes.deployments.settings.servers
import routes.deployments.settings.auxiliary
import routes.deployments.settings.slack

class Groups:
    def __init__(self, app, sql):
        # Init models
        self._groups = models.admin.groups.Groups(sql)
        self._users = models.admin.users.Users(sql)

        # Init routes
        self._environments = routes.deployments.settings.environments.Environments(app, sql)
        self._regions = routes.deployments.settings.regions.Regions(app, sql)
        self._servers = routes.deployments.settings.servers.Servers(app, sql)
        self._auxiliary = routes.deployments.settings.auxiliary.Auxiliary(app, sql)
        self._slack = routes.deployments.settings.slack.Slack(app, sql)

    def license(self, value):
        self._license = value

    def blueprint(self):
        # Init blueprint
        groups_blueprint = Blueprint('groups', __name__, template_folder='groups')

        @groups_blueprint.route('/admin/groups', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def groups_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            group_json = request.get_json()

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(group_json)
            elif request.method == 'PUT':
                return self.put(group_json)
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
            data = {
                'group': self._groups.get(group_id=groupID),
                'environments': self._environments.get(groupID)[0].get_json(),
                'regions': self._regions.get(groupID)[0].get_json(),
                'servers': self._servers.get(groupID)[0].get_json(),
                'auxiliary': self._auxiliary.get(groupID)[0].get_json(),
                'slack': self._slack.get(groupID)[0].get_json()
            }
            return jsonify(data), 200

    def post(self, data):
        # Get Group
        group = json.loads(data['group'])

        # Check if group currently exists
        if self._groups.exist(group):
            return jsonify({'message': 'This group currently exists'}), 400

        # Create group
        self._groups.post(group)

        # Get group ID
        group_id = self._groups.get(group_name=group['name'])[0]['id']

        # Add elements
        try:
            for i in data['environments']:
                self._environments.post(group_id, i)
            for i in data['regions']:
                self._regions.post(group_id, i)
            for i in data['servers']:
                self._servers.post(group_id, i)
            for i in data['auxiliary']:
                self._auxiliary.post(group_id, i)

            self._slack.put(group_id, json.loads(data['slack']))        
            return jsonify({'message': 'Group added'}), 200

        except Exception:
            # Rollback
            self.delete([group['name']])
            return jsonify({'message': 'An error ocurred adding a group'}), 400

    def put(self, data):
        # Get Modified Group
        group = json.loads(data['group'])

        # Get Current Group
        current = self.get(group['id'])[0].get_json()

        if group['name'] != current['group'][0]['name'] and self._groups.exist(group):
            return jsonify({'message': 'This group currently exists'}), 400

        # Calculate diff
        diff_group = self.__diff(current['group'], [group])
        diff_environments = self.__diff(current['environments']['data'], data['environments'])
        diff_regions = self.__diff(current['regions']['data']['regions'], data['regions'])
        diff_servers = self.__diff(current['servers']['data']['servers'], data['servers'])
        diff_auxiliary = self.__diff(current['auxiliary']['data'], data['auxiliary'])

        # Apply diff
        # - Groups -
        if len(diff_group['change']) > 0:
            self._groups.put(diff_group['change'][0])
        
        # - Environments -
        self._environments.delete(group['id'], diff_environments['remove'])
        for i in diff_environments['add']:
            self._environments.post(group['id'], i)
        for i in diff_environments['change']:
            self._environments.put(group['id'], i)

        # - Regions -
        self._regions.delete(group['id'], diff_regions['remove'])
        for i in diff_regions['add']:
            self._regions.post(group['id'], i)
        for i in diff_regions['change']:
            self._regions.put(group['id'], i)

        # - Servers -
        self._servers.delete(group['id'], diff_servers['remove'])
        for i in diff_servers['add']:
            self._servers.post(group['id'], i)
        for i in diff_servers['change']:
            self._servers.put(group['id'], i)

        # - Auxiliary Connections -
        self._auxiliary.delete(group['id'], diff_auxiliary['remove'])
        for i in diff_auxiliary['add']:
            self._auxiliary.post(group['id'], i)
        for i in diff_auxiliary['change']:
            self._auxiliary.put(group['id'], i)

        # - Slack -
        self._slack.put(group['id'], json.loads(data['slack']))

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