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

        @client_blueprint.route('/client/objects', methods=['GET'])
        @jwt_required
        def client_objects_method():
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

            # Get Database Objects
            tables = conn.get_all_tables(db=request.args['database_name'])
            columns = conn.get_all_columns(db=request.args['database_name'])
            triggers = conn.get_all_triggers(db=request.args['database_name'])
            events = conn.get_all_events(db=request.args['database_name'])
            routines = conn.get_all_routines(db=request.args['database_name'])
            return jsonify({'tables': tables, 'columns': columns, 'triggers': triggers, 'events': events, 'routines': routines}), 200

        @client_blueprint.route('/client/execute', methods=['POST'])
        @jwt_required
        def client_execute_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            client_json = request.get_json()

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], client_json['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = connectors.connector.Connector(cred)

            # Execute all queries
            execution = []
            for q in client_json['queries']:
                try:
                    result = conn.execute(query=q, database=client_json['database'])
                    result['query'] = q
                    result['success'] = True
                except Exception as e:
                    result = {"query": q, "success": False, "error": str(e)}
                    break
                finally:
                    execution.append(result)

            return jsonify({'data': execution}), 200

        return client_blueprint

    ####################
    # Internal Methods #
    ####################
