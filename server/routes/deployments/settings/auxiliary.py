from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import utils
import models.admin.users
import models.deployments.auxiliary

class Auxiliary:
    def __init__(self, app, sql):
        self._app = app
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
                return self.post(user['id'], user['group_id'], auxiliary_json)
            elif request.method == 'PUT':
                return self.put(user['id'], user['group_id'], auxiliary_json)
            elif request.method == 'DELETE':
                return self.delete(user['group_id'], auxiliary_json)

        @auxiliary_blueprint.route('/deployments/auxiliary/test', methods=['POST'])
        @jwt_required
        def auxiliary_test_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['deployments_edit']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            auxiliary_json = request.get_json()

            # Build Auxiliary Data
            ssh = None
            # if auxiliary_json['ssh_tunnel']:
            #    ssh = {"hostname": auxiliary_json['ssh_hostname'], "port": auxiliary_json['ssh_port'], "username": auxiliary_json['ssh_username'], "password": auxiliary_json['ssh_password'], "key": auxiliary_json['ssh_key']}
            sql = {"hostname": auxiliary_json['sql_hostname'], "port": auxiliary_json['sql_port'], "username": auxiliary_json['sql_username'], "password": auxiliary_json['sql_password']}
 
            # Init Utils Class
            u = utils.Utils(self._app, ssh)

            # Check SQL Connection
            try:
                u.check_sql(sql)
            except Exception as e:
                return jsonify({'message': "Can't connect to the Auxiliary Server"}), 400

            return jsonify({'message': 'Connection Successful'}), 200

        return auxiliary_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, group_id):
        return jsonify({'data': self._auxiliary.get(group_id)}), 200

    def post(self, user_id, group_id, data):
        if self._auxiliary.exist(group_id, data):
            return jsonify({'message': 'This auxiliary connection currently exists'}), 400
        else:
            self._auxiliary.post(user_id, group_id, data)
            return jsonify({'message': 'Auxiliary connection added successfully'}), 200

    def put(self, user_id, group_id, data):
        if self._auxiliary.exist(group_id, data):
            return jsonify({'message': 'This new auxiliary connection name currently exists'}), 400
        else:
            self._auxiliary.put(user_id, group_id, data)
            return jsonify({'message': 'Auxiliary connection edited successfully'}), 200

    def delete(self, group_id, data):
        for auxiliary in data:
            self._auxiliary.delete(group_id, auxiliary)
        return jsonify({'message': 'Selected auxiliary connections deleted successfully'}), 200

    def remove(self, group_id):
        self._auxiliary.remove(group_id)