from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import json
import utils
import datetime
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
            databases = conn.get_all_databases()
            collations = conn.get_collations()
            return jsonify({'databases': databases, 'collations': collations}), 200

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
            conn.start()

            # Execute all queries
            execution = []
            for q in client_json['queries']:
                try:
                    result = conn.execute(query=q, database=client_json['database'])
                    result['query'] = q

                    # Get table metadata
                    if 'table' in client_json:
                        columns = conn.get_column_names(db=client_json['database'], table=client_json['table'])
                        pks = conn.get_pk_names(db=client_json['database'], table=client_json['table'])
                        # Get table column names & column type
                        result['columns'] = columns
                        result['pks'] = pks

                    conn.commit()
                    execution.append(result)

                except Exception as e:
                    result = {'query': q, 'error': str(e)}
                    execution.append(result)
                    return jsonify({'data': json.dumps(execution, default=self.__json_parser)}), 400
                finally:
                    conn.stop()

            return jsonify({'data': json.dumps(execution, default=self.__json_parser)}), 200

        @client_blueprint.route('/client/structure', methods=['GET'])
        @jwt_required
        def client_structure_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = connectors.connector.Connector(cred)

            # Get Structure
            columns = conn.get_columns(db=request.args['database'], table=request.args['table'])
            indexes = conn.get_indexes(db=request.args['database'], table=request.args['table'])
            fks = conn.get_fks(db=request.args['database'], table=request.args['table'])
            triggers = conn.get_triggers(db=request.args['database'], table=request.args['table'])
            return jsonify({'columns': json.dumps(columns, default=self.__json_parser), 'indexes': json.dumps(indexes, default=self.__json_parser), 'fks': json.dumps(fks, default=self.__json_parser), 'triggers': json.dumps(triggers, default=self.__json_parser)}), 200

        @client_blueprint.route('/client/structure/columns', methods=['GET'])
        @jwt_required
        def client_structure_columns_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = connectors.connector.Connector(cred)

            # Get Columns
            columns = conn.get_columns_definition(db=request.args['database'], table=request.args['table'])
            return jsonify({'columns': json.dumps(columns, default=self.__json_parser)}), 200

        @client_blueprint.route('/client/info', methods=['GET'])
        @jwt_required
        def client_info_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = connectors.connector.Connector(cred)

            # Get Info
            if request.args['object'] == 'table':
                info = conn.get_table_info(db=request.args['database'], table=request.args['name'])
                info['syntax'] = conn.get_table_syntax(db=request.args['database'], table=request.args['name'])
            elif request.args['object'] == 'view':
                info = conn.get_view_info(db=request.args['database'], view=request.args['name'])
            elif request.args['object'] == 'trigger':
                info = conn.get_trigger_info(db=request.args['database'], trigger=request.args['name'])
                info['syntax'] = conn.get_trigger_syntax(db=request.args['database'], trigger=request.args['name'])
            elif request.args['object'] == 'function':
                info = conn.get_function_info(db=request.args['database'], function=request.args['name'])
                info['syntax'] = conn.get_function_syntax(db=request.args['database'], function=request.args['name'])
            elif request.args['object'] == 'procedure':
                info = conn.get_procedure_info(db=request.args['database'], procedure=request.args['name'])
                info['syntax'] = conn.get_procedure_syntax(db=request.args['database'], procedure=request.args['name'])
            elif request.args['object'] == 'event':
                info = conn.get_event_info(db=request.args['database'], event=request.args['name'])
                info['syntax'] = conn.get_event_syntax(db=request.args['database'], event=request.args['name'])
            return jsonify({'info': json.dumps(info, default=self.__json_parser)}), 200

        return client_blueprint

    ####################
    # Internal Methods #
    ####################
    def __json_parser(self, o):
        if isinstance(o, datetime.datetime):
            return o.__str__()
