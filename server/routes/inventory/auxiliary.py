from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
import json

import connectors.base
import models.admin.users
import models.inventory.auxiliary

class Auxiliary:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._auxiliary = models.inventory.auxiliary.Auxiliary(sql)

    def blueprint(self):
        # Init blueprint
        auxiliary_blueprint = Blueprint('auxiliary', __name__, template_folder='auxiliary')

        @auxiliary_blueprint.route('/inventory/auxiliary', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def auxiliary_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            auxiliary = request.get_json()

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user, auxiliary)
            elif request.method == 'PUT':
                return self.put(user, auxiliary)
            elif request.method == 'DELETE':
                return self.delete(user)

        @auxiliary_blueprint.route('/inventory/auxiliary/test', methods=['POST'])
        @jwt_required
        def auxiliary_test_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            auxiliary_json = request.get_json()

            # Build Auxiliary Data
            if 'auxiliary' in auxiliary_json:
                aux = self._auxiliary.get(user['id'], user['group_id'], auxiliary_json['auxiliary'])
                if len(aux) == 0:
                    return jsonify({'message': "Can't test the connection. Invalid auxiliary provided."}), 400
                ssh = {'enabled': False}
                if aux[0]['ssh_tunnel']:
                    ssh = {"enabled": True, "hostname": aux[0]['ssh_hostname'], "port": aux[0]['ssh_port'], "username": aux[0]['ssh_username'], "password": aux[0]['ssh_password'], "key": aux[0]['ssh_key']}
                sql = {"engine": aux[0]['sql_engine'], "hostname": aux[0]['sql_hostname'], "port": aux[0]['sql_port'], "username": aux[0]['sql_username'], "password": aux[0]['sql_password']}
            else:
                ssh = {'enabled': False}
                if auxiliary_json['ssh_tunnel']:
                    ssh = {"enabled": True, "hostname": auxiliary_json['ssh_hostname'], "port": auxiliary_json['ssh_port'], "username": auxiliary_json['ssh_username'], "password": auxiliary_json['ssh_password'], "key": auxiliary_json['ssh_key']}
                sql = {"engine": auxiliary_json['sql_engine'], "hostname": auxiliary_json['sql_hostname'], "port": auxiliary_json['sql_port'], "username": auxiliary_json['sql_username'], "password": auxiliary_json['sql_password']}

            # Check SQL Connection
            try:
                sql = connectors.base.Base({'ssh': ssh, 'sql': sql})
                sql.test_sql()
            except Exception as e:
                return jsonify({'message': str(e)}), 400

            return jsonify({'message': 'Connection Successful'}), 200

        return auxiliary_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        auxiliary = self._auxiliary.get(user['id'], user['group_id'])
        if user['inventory_secured'] and not user['owner']:
            auxiliary_secured = []
            for a in auxiliary:
                if a['shared']:
                    auxiliary_secured.append({"id": a['id'], "name": a['name'], "sql_engine": a['sql_engine'], "sql_version": a['sql_version'], "shared": a['shared']})
                else:
                    auxiliary_secured.append(a)
            return jsonify({'data': auxiliary_secured}), 200
        return jsonify({'data': auxiliary}), 200

    def post(self, user, auxiliary):
        # Check privileges
        if auxiliary['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check auxiliary exists
        if self._auxiliary.exist(user['id'], user['group_id'], auxiliary):
            return jsonify({'message': 'This auxiliary name currently exists'}), 400
        # Add auxiliary
        self._auxiliary.post(user['id'], user['group_id'], auxiliary)
        return jsonify({'message': 'Auxiliary connection added successfully'}), 200

    def put(self, user, auxiliary):
        # Check privileges
        if auxiliary['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check auxiliary exists
        if self._auxiliary.exist(user['id'], user['group_id'], auxiliary):
            return jsonify({'message': 'This auxiliary name currently exists'}), 400
        # Edit auxiliary
        self._auxiliary.put(user['id'], user['group_id'], auxiliary)
        return jsonify({'message': 'Auxiliary connection edited successfully'}), 200

    def delete(self, user):
        data = json.loads(request.args['auxiliary'])
        # Check privileges
        for auxiliary in data:
            auxiliary = self._auxiliary.get(user['id'], user['group_id'], auxiliary)
            if len(auxiliary) > 0 and auxiliary[0]['shared'] and not user['owner']:
                return jsonify({'message': "Insufficient privileges"}), 401
        # Delete auxiliary
        for auxiliary in data:
            self._auxiliary.delete(user['group_id'], auxiliary)
        return jsonify({'message': 'Selected auxiliary connections deleted successfully'}), 200
