from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from flask import Response, stream_with_context

import io
import csv
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
            servers = self._client.get_servers(user['group_id'])
            return jsonify({'servers': servers}), 200

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
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = connectors.connector.Connector(cred)

            # Get Databases
            databases = conn.get_all_databases()
            engines = conn.get_engines()
            encodings = conn.get_encodings()
            defaults = {
                "encoding": conn.get_default_encoding(),
                "collation": conn.get_default_collation()
            }
            return jsonify({'databases': databases, 'engines': engines, 'encodings': encodings, 'defaults': defaults}), 200

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
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = connectors.connector.Connector(cred)

            # Get Database Objects
            if 'detailed' in request.args:
                databases = conn.get_database_info()
                tables = conn.get_table_info(db=request.args['database'])
                views = conn.get_view_info(db=request.args['database'])
                triggers = conn.get_trigger_info(db=request.args['database'])
                functions = conn.get_function_info(db=request.args['database'])
                procedures = conn.get_procedure_info(db=request.args['database'])
                events = conn.get_event_info(db=request.args['database'])
                return jsonify({'databases': self.__json(databases), 'tables': self.__json(tables), 'views': self.__json(views), 'triggers': self.__json(triggers), 'functions': self.__json(functions), 'procedures': self.__json(procedures), 'events': self.__json(events)}), 200
            else:
                tables = conn.get_all_tables(db=request.args['database'])
                columns = conn.get_all_columns(db=request.args['database'])
                triggers = conn.get_all_triggers(db=request.args['database'])
                events = conn.get_all_events(db=request.args['database'])
                routines = conn.get_all_routines(db=request.args['database'])
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
                    return jsonify({'data': self.__json(execution)}), 400
                finally:
                    conn.stop()

            return jsonify({'data': self.__json(execution)}), 200

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
            return jsonify({'columns': self.__json(columns), 'indexes': self.__json(indexes), 'fks': self.__json(fks), 'triggers': self.__json(triggers)}), 200

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
            return jsonify({'columns': self.__json(columns)}), 200

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
                if len(info) > 0:
                    try:
                        info[0]['syntax'] = conn.get_table_syntax(db=request.args['database'], table=request.args['name'])
                    except Exception:
                        info[0]['syntax'] = ''
            elif request.args['object'] == 'view':
                info = conn.get_view_info(db=request.args['database'], view=request.args['name'])
                if len(info) > 0:
                    try:
                        info[0]['syntax'] = conn.get_view_syntax(db=request.args['database'], view=request.args['name'])
                    except Exception as e:
                        info[0]['syntax'] = ''
            elif request.args['object'] == 'trigger':
                info = conn.get_trigger_info(db=request.args['database'], trigger=request.args['name'])
                if len(info) > 0:
                    try:
                        info[0]['syntax'] = conn.get_trigger_syntax(db=request.args['database'], trigger=request.args['name'])
                    except Exception:
                        info[0]['syntax'] = ''
            elif request.args['object'] == 'function':
                info = conn.get_function_info(db=request.args['database'], function=request.args['name'])
                if len(info) > 0:
                    try:
                        info[0]['syntax'] = conn.get_function_syntax(db=request.args['database'], function=request.args['name'])
                    except Exception:
                        info[0]['syntax'] = ''
            elif request.args['object'] == 'procedure':
                info = conn.get_procedure_info(db=request.args['database'], procedure=request.args['name'])
                if len(info) > 0:
                    try:
                        info[0]['syntax'] = conn.get_procedure_syntax(db=request.args['database'], procedure=request.args['name'])
                    except Exception:
                        info[0]['syntax'] = ''
            elif request.args['object'] == 'event':
                info = conn.get_event_info(db=request.args['database'], event=request.args['name'])
                if len(info) > 0:
                    try:
                        info[0]['syntax'] = conn.get_event_syntax(db=request.args['database'], event=request.args['name'])
                    except Exception:
                        info[0]['syntax'] = ''
            return jsonify({'info': self.__json(info)}), 200

        @client_blueprint.route('/client/collations', methods=['GET'])
        @jwt_required
        def client_collations_method():
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

            # Get Collations
            collations = conn.get_collations(encoding=request.args['encoding'])
            return jsonify({'collations': self.__json(collations)}), 200

        @client_blueprint.route('/client/import', methods=['POST'])
        @jwt_required
        def client_import_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.form['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = connectors.connector.Connector(cred)
            
            # Get uploaded file
            if 'file' not in request.files or request.files['file'].filename == '':
                return jsonify({"message": 'No file was uploaded'}), 400

            if not self.__allowed_file(request.files['file'].filename):
                return jsonify({"message": 'The file extension is not valid'}), 400

            if request.content_length > 10 * 1024 * 1024:
                return jsonify({"message": 'The upload file exceeds the maximum allowed size (10MB)'}), 400

            # Execute uploaded file
            try:
                conn.execute(request.files['file'].read(), database=request.form['database'])
                conn.commit()
                return jsonify({'message': 'File successfully uploaded'}), 200
            except Exception as e:
                conn.rollback()
                return jsonify({'message': str(e)}), 400
            finally:
                conn.stop()

            # command = ['mysql', '-u%s' % db_settings['USER'], '-p%s' % db_settings['PASSWORD'], db_settings['NAME']]
            # proc = subprocess.Popen(command, stdin = uploaded_file.stream)
            # stdout, stderr = proc.communicate()

        @client_blueprint.route('/client/export', methods=['GET'])
        @jwt_required
        def client_export_method():
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
            conn.start()

            try:
                # Get options
                options = json.loads(request.args['options'])
                # Export SQL
                def export_sql():
                    for i in range(1000):
                        yield 'hello'

                if options['mode'] == 'csv':
                    return Response(stream_with_context(self.__export_csv(options, conn)))
                elif options['mode'] == 'sql':
                    return Response(stream_with_context(export_sql()))
            except Exception as e:
                conn.rollback()
                return jsonify({'message': str(e)}), 400
            finally:
                conn.stop()

        return client_blueprint

    ####################
    # Internal Methods #
    ####################
    def __json(self, data):
        return json.dumps(data, default=self.__json_parser)

    def __json_parser(self, o):
        if isinstance(o, datetime.datetime):
            return o.__str__()

    def __allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'sql'}

    def __export_csv(self, options, conn):
        for table in options['objects']['tables']:
            first = options['fields']
            conn.execute(query=f"SELECT * FROM {table}", database=request.args['database'], fetch=False)
            while True:
                output = io.StringIO()
                row = conn.fetch_one()
                if row == None:
                    break
                writer = csv.DictWriter(output, fieldnames=row.keys())
                if first:
                    writer.writeheader()
                    first = False
                writer.writerow(row)
                yield output.getvalue()
