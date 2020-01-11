from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.releases
import models.deployments.deployments

class Releases:
    def __init__(self, app, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._releases = models.deployments.releases.Releases(sql)
        self._deployments = models.deployments.deployments.Deployments(sql)

    def license(self, value):
        self._license = value

    def blueprint(self):
        # Init blueprint
        releases_blueprint = Blueprint('releases', __name__, template_folder='releases')

        @releases_blueprint.route('/deployments/releases', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def releases_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            release_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['id'])
            elif request.method == 'POST':
                return self.post(user['id'], release_json)
            elif request.method == 'PUT':
                return self.put(user['id'], release_json)
            elif request.method == 'DELETE':
                return self.delete(user['id'], release_json)

        @releases_blueprint.route('/deployments/releases/active', methods=['GET'])
        @jwt_required
        def releases_active_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Return active releases
            return jsonify({'data': self._releases.getActive(user['id'])}), 200

        return releases_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user_id):
        return jsonify({'data': self._releases.get(user_id)}), 200

    def post(self, user_id, data):
        if self._releases.exist(user_id, data):
            return jsonify({'message': 'This release currently exists'}), 400
        else:
            self._releases.post(user_id, data)
            return jsonify({'message': 'Release added successfully'}), 200

    def put(self, user_id, data):
        # Change 'active' field
        if 'id' in data:
            self._releases.putActive(user_id, data)
        # Change all fields
        else:
            if self._releases.exist(user_id, data):
                return jsonify({'message': 'This new release currently exists'}), 400
            else:
                self._releases.put(user_id, data)

        return jsonify({'message': 'Release edited successfully'}), 200

    def delete(self, user_id, data):
        for release in data:
            self._deployments.removeRelease(release)
            self._releases.delete(user_id, release)
        return jsonify({'message': 'Selected releases deleted successfully'}), 200