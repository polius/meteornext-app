import imp
import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

class Groups:
    def __init__(self, credentials):
        # Init models
        self._groups = imp.load_source('groups', '{}/models/admin/groups.py'.format(credentials['path'])).Groups(credentials)
        self._users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)

        # Init routes
        self._environments = imp.load_source('environments', '{}/routes/deployments/environments.py'.format(credentials['path'])).Environments(credentials)
        self._regions = imp.load_source('regions', '{}/routes/deployments/regions.py'.format(credentials['path'])).Regions(credentials)
        self._servers = imp.load_source('servers', '{}/routes/deployments/servers.py'.format(credentials['path'])).Servers(credentials)
        self._auxiliary = imp.load_source('auxiliary', '{}/routes/deployments/auxiliary.py'.format(credentials['path'])).Auxiliary(credentials)
        self._slack = imp.load_source('slack', '{}/routes/deployments/slack.py'.format(credentials['path'])).Slack(credentials)
        self._s3 = imp.load_source('s3', '{}/routes/deployments/s3.py'.format(credentials['path'])).S3(credentials)
        self._web = imp.load_source('web', '{}/routes/deployments/web.py'.format(credentials['path'])).Web(credentials)

    def blueprint(self):
        # Init blueprint
        groups_blueprint = Blueprint('groups', __name__, template_folder='groups')

        @groups_blueprint.route('/admin/groups', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def groups_method():
            # Check user privileges
            is_admin = self._users.is_admin(get_jwt_identity())
            if not is_admin:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            group_json = request.get_json()

            if request.method == 'GET':
                return self.get(group_json)
            elif request.method == 'POST':
                return self.post(group_json)
            elif request.method == 'PUT':
                return self.put(group_json)
            elif request.method == 'DELETE':
                return self.delete(group_json)

        return groups_blueprint

    def get(self, data):
        if data is None:
            return jsonify({'data': self._groups.get()}), 200
        else:
            return jsonify({'data': self._groups.get(data)}), 200

    def post(self, data):
        # Get Group
        group = json.loads(data['group'])

        # Check if group currently exists
        if self._groups.exist(group):
            return jsonify({'message': 'This group currently exists'}), 400

        # Create group
        self._groups.post(group)

        # Get group ID
        group_id = self._groups.get(group)[0]['id']

        # Add elements
        try:
            print(data)
            for i in data['environments']:
                self._environments.post(group_id, json.loads(i))
            for i in data['regions']:
                self._regions.post(group_id, json.loads(i))
            for i in data['servers']:
                self._servers.post(group_id, json.loads(i))
            for i in data['auxiliary']:
                self._auxiliary.post(group_id, json.loads(i))

            self._slack.put(group_id, json.loads(data['slack']))
            self._s3.put(group_id, json.loads(data['s3']))
            self._web.put(group_id, json.loads(data['web']))
            return jsonify({'message': 'Group added'}), 200

        except Exception:
            # Rollback
            self.delete([group['name']])
            raise
            return jsonify({'message': 'An error ocurred adding a group'}), 400
            

    def put(self, data):
        if self._groups.exist(data):
            return jsonify({'message': 'This group currently exists'}), 400

        # Get group ID
        group_id = self._groups.get(data.group)[0]['id']

        # Edit objects
        self._groups.put(data.group)
        self._environments.put(group_id, data.environments)
        self._regions.put(group_id, data.regions)
        self._servers.put(group_id, data.regions)
        self._auxiliary.put(group_id, data.regions)
        self._slack.put(group_id, data.slack)
        self._s3.put(group_id, data.s3)
        self._web.put(group_id, data.web)

        return jsonify({'message': 'Group edited'}), 200

    def delete(self, data):
        for group in data:
            # Get group ID
            group_id = self._groups.get({'name': group})[0]['id']

            # Delete all group elements
            self._web.delete(group_id)
            self._s3.delete(group_id)
            self._slack.delete(group_id)
            self._auxiliary.remove(group_id)
            self._servers.remove(group_id)
            self._regions.remove(group_id)
            self._environments.remove(group_id)
            self._groups.delete(group)
        return jsonify({'message': 'Selected groups deleted'}), 200