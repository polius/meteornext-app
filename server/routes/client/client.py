from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import utils
import models.admin.users
import models.client.client
import connectors.connector

class Client:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._client = models.client.client.Client(sql)

    def blueprint(self):
        # Init blueprint
        client_blueprint = Blueprint('client', __name__, template_folder='client')

        @client_blueprint.route('/client/servers', methods=['GET'])
        @jwt_required
        def client_servers_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Servers
            return jsonify({'data': self._client.get_servers(user['group_id'])}), 200

        @client_blueprint.route('/client/databases', methods=['GET'])
        @jwt_required
        def client_databases_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server_id'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = connectors.connector.Connector(cred)

            # Get Databases
            try:
                return jsonify({'data': conn.get_all_databases()}), 200
            except Exception as e:
                return jsonify({'message': str(e)}), 400

        @client_blueprint.route('/client/tables', methods=['GET'])
        @jwt_required
        def client_tables_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server_id'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = connectors.connector.Connector(cred)

            # Get Tables
            return jsonify({'data': conn.get_all_tables(db=request.args['database_name'])}), 200

        return client_blueprint

    ####################
    # Internal Methods #
    ####################
