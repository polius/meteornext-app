import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.deployments_shared

class Shared:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._shared = models.deployments.deployments_shared.Deployments_Shared(sql)

    def blueprint(self):
        # Init blueprint
        shared_blueprint = Blueprint('deployments_shared', __name__, template_folder='deployments_shared')

        @shared_blueprint.route('/deployments/shared/you', methods=['GET','POST','DELETE'])
        @jwt_required()
        def shared_you_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['deployments_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            if request.method == 'GET':
                return self.get_you(user['id'])
            elif request.method == 'POST':
                return self.post_you(user['id'], data)
            elif request.method == 'DELETE':
                return self.delete_you(user['id'], data)

        @shared_blueprint.route('/deployments/shared/you/pinned', methods=['POST','DELETE'])
        @jwt_required()
        def shared_you_pinned_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['deployments_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json() if request.get_json() else request.form

            if request.method == 'POST':
                for item in data:
                    self._shared.pin_you(user['id'], item, 1)
                return jsonify({'message': f"Deployment{'s' if len(data) > 1 else ''} pinned"}), 200

            elif request.method == 'DELETE':
                for item in data:
                    self._shared.pin_you(user['id'], item, 0)
                return jsonify({'message': f"Deployment{'s' if len(data) > 1 else ''} unpinned"}), 200

        @shared_blueprint.route('/deployments/shared/others', methods=['GET','DELETE'])
        @jwt_required()
        def shared_others_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['deployments_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            if request.method == 'GET':
                return self.get_others(user['id'])
            elif request.method == 'DELETE':
                return self.delete_others(user['id'], data)

        return shared_blueprint

    ####################
    # Internal Methods #
    ####################
    def get_you(self, user_id):
        dfilter = json.loads(request.args['filter']) if 'filter' in request.args else None
        dsort = json.loads(request.args['sort']) if 'sort' in request.args else None
        deployments = self._shared.get_you(user_id, dfilter=dfilter, dsort=dsort)
        return jsonify({'deployments': deployments}), 200

    def post_you(self, user_id, data):
        if 'url' not in data:
            return jsonify({'message': 'The deployment URL was not provided'}), 400
        if '/' not in data['url']:
            return jsonify({'message': 'This deployment does not exist'}), 400

        # Extract uri from url
        uri = data['url'][data['url'].rfind('/')+1:]
        # Check uri
        check = self._shared.check_uri(user_id, uri)
        if len(check) == 0:
            return jsonify({'message': 'This deployment does not exist or is not shared'}), 400

        # Check if deployment is already yours
        if check[0]['user_id'] == user_id:
            return jsonify({'message': 'You cannot import your shared deployments'}), 400

        # Check if deployment is already added
        if check[0]['already_added']:
            return jsonify({'message': 'This deployment is already added in your list'}), 400

        # Add new deployment
        self._shared.post_you(user_id, uri)
        return jsonify({'message': 'Deployment successfully added'}), 200

    def delete_you(self, user_id, data):
        for execution in data:
            self._shared.delete_you(user_id, execution)
        return jsonify({'message': 'Selected deployments successfully removed'}), 200

    def get_others(self, user_id):
        dfilter = json.loads(request.args['filter']) if 'filter' in request.args else None
        dsort = json.loads(request.args['sort']) if 'sort' in request.args else None
        deployments = self._shared.get_others(user_id, dfilter=dfilter, dsort=dsort)
        return jsonify({'deployments': deployments}), 200

    def delete_others(self, user_id, data):
        for execution in data:
            self._shared.delete_others(user_id, execution)
        return jsonify({'message': 'Selected deployments successfully unshared'}), 200
