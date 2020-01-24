import sys
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import utils
import models.admin.users
import models.deployments.environments
import models.deployments.regions
import models.deployments.servers

class Regions:
    def __init__(self, app, sql):
        self._app = app
        # Init models
        self._users = models.admin.users.Users(sql)
        self._environments = models.deployments.environments.Environments(sql)
        self._regions = models.deployments.regions.Regions(sql)
        self._servers = models.deployments.servers.Servers(sql)

    def license(self, value):
        self._license = value

    def blueprint(self):
        # Init blueprint
        regions_blueprint = Blueprint('regions', __name__, template_folder='regions')       

        @regions_blueprint.route('/deployments/regions', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def regions_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            region_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['group_id'])
            elif request.method == 'POST':
                return self.post(user['id'], user['group_id'], region_json)
            elif request.method == 'PUT':
                return self.put(user['id'], user['group_id'], region_json)
            elif request.method == 'DELETE':
                return self.delete(user['group_id'], region_json)

        @regions_blueprint.route('/deployments/regions/list', methods=['POST'])
        @jwt_required
        def regions_list_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            # Return Regions By User Environment
            return jsonify({'data': self._regions.get_by_environment(user['group_id'], data)}), 200

        @regions_blueprint.route('/deployments/regions/test', methods=['POST'])
        @jwt_required
        def regions_test_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            region_json = request.get_json()

            # Init Utils Class
            u = utils.Utils(self._app, region_json)

            if region_json['cross_region']:
                # Check SSH Connection & Deploy Path
                try:
                    if not u.check_ssh_path():
                        return jsonify({'message': "The user '{}' does not have rwx privileges to the Deploy Path".format(region_json['username'])}), 400
                except Exception as e:
                    return jsonify({'message': "Can't connect to the SSH Region"}), 400
            else:
                try:
                    u.check_ssh()
                except Exception as e:
                    return jsonify({'message': "Can't connect to the SSH Region"}), 400
            return jsonify({'message': 'Connection Successful'}), 200

        return regions_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id):
        return jsonify({'data': {'regions': self._regions.get(group_id), 'environments': self._environments.get(group_id)}}), 200

    def post(self, user_id, group_id, data):
        if self._regions.exist(group_id, data):
            return jsonify({'message': 'This region currently exists'}), 400
        elif data['ssh_tunnel']:
            # Deploy Meteor
            u = utils.Utils(self._app, data)
            status = u.prepare()
            if not status['success']:
                return jsonify({'message': status['error']}), 400

        # Create new Region
        self._regions.post(user_id, group_id, data)
        return jsonify({'message': 'Region added successfully'}), 200

    def put(self, user_id, group_id, data):
        if self._regions.exist(group_id, data):
            return jsonify({'message': 'This new region name currently exists'}), 400
        elif data['ssh_tunnel'] and data['cross_region']:
            u = utils.Utils(self._app, data)
            deploy_status = u.check_ssh_deploy()
            if 'error' in deploy_status:
                return jsonify({'message': deploy_status['error']}), 400

            if not deploy_status['exists']:
                # Clean Meteor
                r = self._regions.get(group_id, data['id'])
                if r[0]['hostname'] != data['hostname'] or r[0]['port'] != data['port'] or r[0]['deploy_path'] != data['deploy_path']:
                    u = utils.Utils(self._app, r[0])
                    status = u.unprepare()
                # Deploy Meteor
                u = utils.Utils(self._app, data)
                status = u.prepare(deploy=(not deploy_status['exists']))
                if not status['success']:
                    return jsonify({'message': status['error']}), 400

        # Edit Region
        self._regions.put(user_id, group_id, data)
        return jsonify({'message': 'Region edited successfully'}), 200

    def delete(self, group_id, data):
        # Check inconsistencies
        for region in data:
            if self._servers.exist_by_region(group_id, region):
                return jsonify({'message': "This region has attached servers"}), 400

        for region in data:
            if data['ssh_tunnel'] and data['cross_region']:
                r = self._regions.get(group_id, region)
                if len(r) > 0:
                    # Delete Meteor from region
                    u = utils.Utils(self._app, r[0])
                    u.unprepare()
                    self._regions.delete(group_id, region)
            else:
                self._regions.delete(group_id, region)
        return jsonify({'message': 'Selected regions deleted successfully'}), 200

    def remove(self, group_id):
        self._regions.remove(group_id)