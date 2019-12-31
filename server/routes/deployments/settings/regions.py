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
                return self.__get(user['group_id'])
            elif request.method == 'POST':
                return self.__post(user['group_id'], region_json)
            elif request.method == 'PUT':
                return self.__put(user['group_id'], region_json)
            elif request.method == 'DELETE':
                return self.__delete(user['group_id'], region_json)

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

        return regions_blueprint

    ####################
    # Internal Methods #
    ####################
    def __get(self, group_id):
        return jsonify({'data': {'regions': self._regions.get(group_id), 'environments': self._environments.get(group_id)}}), 200

    def __post(self, group_id, data):
        if self._regions.exist(group_id, data):
            return jsonify({'message': 'This region currently exists'}), 400
        else:
            # Deploy Meteor
            connection = {'hostname': data['hostname'], 'port': data['port'], 'username': data['username'], 'password': data['password'], 'key': data['key']}
            u = utils.Utils(self._app, connection)
            status = u.prepare(data)
            if not status['success']:
                return jsonify({'message': status['error']}), 400
            
            # Create new Region
            self._regions.post(group_id, data)
            return jsonify({'message': 'Region added successfully'}), 200

    def __put(self, group_id, data):
        if self._regions.exist(group_id, data):
            return jsonify({'message': 'This new region name currently exists'}), 400
        else:
            # Deploy Meteor
            connection = {'hostname': data['hostname'], 'port': data['port'], 'username': data['username'], 'password': data['password'], 'key': data['key']}
            u = utils.Utils(self._app, connection)
            status = u.prepare(data)
            if not status['success']:
                return jsonify({'message': status['error']}), 400

            # Edit Region
            self._regions.put(group_id, data)
            return jsonify({'message': 'Region edited successfully'}), 200

    def __delete(self, group_id, data):
        # Check inconsistencies
        for region in data:
            if self._servers.exist_by_region(group_id, region):
                return jsonify({'message': "The region '" + region['name'] + "' has attached servers"}), 400

        for region in data:
            # Clean deployed Meteor
            # u.unprepare(data)

            self._regions.delete(group_id, region)
        return jsonify({'message': 'Selected regions deleted successfully'}), 200

    def remove(self, group_id):
        self._regions.remove(group_id)