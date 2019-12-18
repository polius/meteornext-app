from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.deployments.auxiliary

class Auxiliary:
    def __init__(self, app, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._auxiliary = models.deployments.auxiliary.Auxiliary(sql)

    def license(self, value):
        self._license = value

    def blueprint(self):
        # Init blueprint
        auxiliary_blueprint = Blueprint('auxiliary', __name__, template_folder='auxiliary')

        @auxiliary_blueprint.route('/deployments/auxiliary', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def auxiliary_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            auxiliary_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['group_id'])
            elif request.method == 'POST':
                return self.post(user['group_id'], auxiliary_json)
            elif request.method == 'PUT':
                return self.put(user['group_id'], auxiliary_json)
            elif request.method == 'DELETE':
                return self.delete(user['group_id'], auxiliary_json)

        return auxiliary_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id):
        return jsonify({'data': self._auxiliary.get(group_id)}), 200

    def post(self, group_id, data):
        if self._auxiliary.exist(group_id, data):
            return jsonify({'message': 'This auxiliary connection currently exists'}), 400
        else:
            self._auxiliary.post(group_id, data)
            return jsonify({'message': 'Auxiliary connection added successfully'}), 200

    def put(self, group_id, data):
        if self._auxiliary.exist(group_id, data):
            return jsonify({'message': 'This new auxiliary connection name currently exists'}), 400
        else:
            self._auxiliary.put(group_id, data)
            return jsonify({'message': 'Auxiliary connection edited successfully'}), 200

    def delete(self, group_id, data):
        for auxiliary in data:
            self._auxiliary.delete(group_id, auxiliary)
        return jsonify({'message': 'Selected auxiliary connections deleted successfully'}), 200

    def remove(self, group_id):
        self._auxiliary.remove(group_id)