from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from flask import Response, stream_with_context

import io
import csv
import json
import utils
import datetime
from itertools import repeat
import models.admin.users
import models.client.client
from connectors.connector import Connections

class Client:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._client = models.client.client.Client(sql)
        # Init connections
        self._connections = Connections()

    def blueprint(self):
        # Init blueprint
        client_blueprint = Blueprint('client', __name__, template_folder='client')

        @client_blueprint.route('/client/servers', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def client_servers_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            client_json = request.get_json()

            if request.method == 'GET':
                servers = self._client.get_servers(user['id'])
                folders = self._client.get_folders(user['id'])
                return jsonify({'servers': servers, 'folders': folders}), 200
            elif request.method == 'POST':
                if 'servers' in client_json:
                    self._client.add_servers(client_json['servers'], user['id'])
                    return jsonify({"message": "Servers successfully added"}), 200
                elif 'folder' in client_json:
                    if (self._client.exists_folder({'name': client_json['folder']}, user['id'])):
                        return jsonify({"message": "This folder name currently exists"}), 400
                    self._client.add_folder(client_json['folder'], user['id'])
                    return jsonify({"message": "Folder successfully created"}), 200
            elif request.method == 'PUT':
                if 'servers' in client_json:
                    self._client.move_servers(client_json['servers'], user['id'])
                    return jsonify({"message": "Servers successfully moved"}), 200
                elif 'folder' in client_json:
                    if (self._client.exists_folder(client_json['folder'], user['id'])):
                        return jsonify({"message": "This folder name currently exists"}), 400
                    self._client.rename_folder(client_json['folder'], user['id'])
                    return jsonify({"message": "Folder successfully renamed"}), 200
            elif request.method == 'DELETE':
                if 'servers' in client_json:
                    self._client.remove_servers(client_json['servers'], user['id'])
                    return jsonify({"message": "Servers successfully deleted"}), 200
                elif 'folders' in client_json:
                    self._client.remove_folders(client_json['folders'], user['id'])
                    return jsonify({"message": "Folder successfully deleted"}), 200

        @client_blueprint.route('/client/databases', methods=['GET'])
        @jwt_required
        def client_databases_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400

            # Open a server connection
            try:
                conn = self._connections.connect(user['id'], request.args['connection'], cred)
            except Exception as e:
                return jsonify({"message": "Can't connect to the Server"}), 500

            # Get Databases
            databases = conn.get_all_databases()
            version = conn.get_version()
            engines = conn.get_engines()
            encodings = conn.get_encodings()
            defaults = {
                "encoding": conn.get_default_encoding(),
                "collation": conn.get_default_collation()
            }
            return jsonify({'databases': databases, 'version': version, 'engines': engines, 'encodings': encodings, 'defaults': defaults}), 200

        @client_blueprint.route('/client/objects', methods=['GET'])
        @jwt_required
        def client_objects_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

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

        @client_blueprint.route('/client/variables', methods=['GET'])
        @jwt_required
        def client_variables_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Get Server Variables
            variables = conn.get_server_variables()
            return jsonify({'variables': variables}), 200

        @client_blueprint.route('/client/execute', methods=['POST'])
        @jwt_required
        def client_execute_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            client_json = request.get_json()

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], client_json['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], client_json['connection'], cred)

            # Execute all queries
            execution = []
            errors = False
            multiple = type(client_json['database']) == list and len(client_json['database']) == len(client_json['queries'])

            for index, query in enumerate(client_json['queries']):
                try:
                    database = client_json['database'][index] if multiple else client_json['database']
                    result = conn.execute(query=query, database=database)
                    result['query'] = query

                    # Get table metadata
                    if 'table' in client_json:
                        columns = conn.get_column_names(db=database, table=client_json['table'])
                        pks = conn.get_pk_names(db=database, table=client_json['table'])
                        # Get table column names & column type
                        result['columns'] = columns
                        result['pks'] = pks

                    conn.commit()
                    execution.append(result)

                except Exception as e:
                    errors = True
                    result = {'query': query, 'error': str(e)}
                    execution.append(result)
                    if ('executeAll' not in client_json or not client_json['executeAll']):
                        return jsonify({'data': self.__json(execution)}), 400

            return jsonify({'data': self.__json(execution)}), 200 if not errors else 400

        @client_blueprint.route('/client/structure', methods=['GET'])
        @jwt_required
        def client_structure_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

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
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

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
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

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
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

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
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.form['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.form['connection'], cred)
            
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
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Start export
            try:
                options = json.loads(request.args['options'])
                if options['mode'] == 'csv':
                    return Response(stream_with_context(self.__export_csv(options, conn)))
                elif options['mode'] == 'sql':
                    return Response(stream_with_context(self.__export_sql(options, cred, conn)))
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/saved', methods=['GET','POST','PUT','DELETE'])
        @jwt_required
        def client_saved_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            saved_json = request.get_json()

            if request.method == 'GET':
                saved_queries = self._client.get_saved_queries(user['id'])
                return jsonify({'saved': saved_queries}), 200
            elif request.method == 'POST':
                qid = self._client.add_saved_query(saved_json, user['id'])
                return jsonify({'data': qid, 'message': 'Saved query added successfully'}), 200
            elif request.method == 'PUT':
                qid = self._client.edit_saved_query(saved_json, user['id'])
                return jsonify({'message': 'Saved query edited successfully'}), 200
            elif request.method == 'DELETE':
                self._client.delete_saved_queries(saved_json, user['id'])
                return jsonify({'message': 'Selected saved queries deleted successfully'}), 200

        @client_blueprint.route('/client/processlist', methods=['GET','PUT'])
        @jwt_required
        def client_processlist_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            processlist_json = request.get_json()

            if request.method == 'GET':
                processlist_settings = self._client.get_processlist_settings(user['id'])
                return jsonify({'processlist': processlist_settings}), 200
            elif request.method == 'PUT':
                self._client.save_processlist_settings(processlist_json, user['id'])
                return jsonify({'message': 'Changes saved'}), 200

        @client_blueprint.route('/client/stop', methods=['GET'])
        @jwt_required
        def client_stop_query_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Close Connection
            self._connections.kill(user['id'], request.args['connection'])
            return jsonify({'message': 'Connection successfully stopped'}), 200

        @client_blueprint.route('/client/rights', methods=['GET'])
        @jwt_required
        def client_rights_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Get Rights
            if 'host' not in request.args and 'user' not in request.args:
                try:
                    rights = conn.get_all_rights()
                    return jsonify({'rights': rights}), 200
                except Exception as e:
                    return jsonify({"message": "Cannot retrieve the user permissions. Please check if the current user has SELECT privileges on the 'mysql.user' table.", "error": str(e)}), 400
            else:
                try:
                    server = conn.get_server_rights(request.args['user'], request.args['host'])
                except Exception as e:
                    return jsonify({"message": "Cannot retrieve the user permissions. Please check if the current user has SELECT privileges on the 'mysql.user' table.", "error": str(e)}), 400
                try:
                    database = conn.get_db_rights(request.args['user'], request.args['host'])
                except Exception as e:
                    return jsonify({"message": "Cannot retrieve the user permissions. Please check if the current user has SELECT privileges on the 'mysql.db' table.", "error": str(e)}), 400
                try:
                    table = conn.get_table_rights(request.args['user'], request.args['host'])
                except Exception as e:
                    return jsonify({"message": "Cannot retrieve the user permissions. Please check if the current user has SELECT privileges on the 'mysql.tables_priv' table.", "error": str(e)}), 400
                try:
                    column = conn.get_column_rights(request.args['user'], request.args['host'])
                except Exception as e:
                    return jsonify({"message": "Cannot retrieve the user permissions. Please check if the current user has SELECT privileges on the 'mysql.columns_priv' table.", "error": str(e)}), 400
                try:
                    proc = conn.get_proc_rights(request.args['user'], request.args['host'])
                except Exception as e:
                    return jsonify({"message": "Cannot retrieve the user permissions. Please check if the current user has SELECT privileges on the 'mysql.procs_priv' table.", "error": str(e)}), 400
                syntax = conn.get_rights_syntax(request.args['user'], request.args['host'])
                return jsonify({'server': server, 'database': database, 'table': table, 'column': column, 'proc': proc, 'syntax': syntax}), 200

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
        conn.stop()

    def __export_sql(self, options, cred, conn):
        errors = {'tables': [], 'views': [], 'triggers': [], 'functions': [], 'procedures': [], 'events': []}
        # Build header
        yield '# ************************************************************\n'
        yield '# Meteor Next - Export SQL\n'
        yield '# Version 1\n#\n'
        yield '# https://meteor2.io\n#\n'
        yield '# Host: {} ({} {})\n'.format(cred['sql']['hostname'], cred['sql']['engine'], conn.get_version())
        yield '# Database: {}\n'.format(request.args['database'])
        yield '# Generation Time: {} UTC\n'.format(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        yield '# ************************************************************\n\n'
        yield 'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;\n'
        yield 'SET FOREIGN_KEY_CHECKS = 0;\n\n'

        # Build Tables
        if 'tables' in options['objects']:
            for table in options['objects']['tables']:
                yield '# ------------------------------------------------------------\n'
                yield '# Table: {}\n'.format(table)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_table_syntax(request.args['database'], table)
                    conn.execute(query=f"SELECT SQL_NO_CACHE * FROM {table}", database=request.args['database'], fetch=False)
                    if options['include'] in ['Structure + Content','Structure']:
                        yield 'DROP TABLE IF EXISTS `{}`;\n\n'.format(table)
                        yield '{};\n\n'.format(syntax)
                    if options['include'] in ['Structure + Content','Content']:
                        first = True                            
                        while True:
                            row = conn.fetch_one()
                            if row == None:
                                if not first:
                                    yield ';\n\n'
                                break
                            args = [v for k, v in row.items()]
                            if first:
                                yield 'INSERT INTO `{}` ({})\nVALUES\n'.format(table, ','.join([f'`{k}`' for k, v in row.items()]))
                                first = False
                                yield '({})'.format(conn.mogrify(','.join(repeat('%s', len(args))), args))
                            else:
                                yield ',\n({})'.format(conn.mogrify(','.join(repeat('%s', len(args))), args))
                except Exception as e:
                    errors['tables'].append({'k': table, 'v': str(e)})
                    yield '# Error: {}\n\n'.format(e)

        # Build Views
        if 'views' in options['objects']:
            for view in options['objects']['views']:
                yield '# ------------------------------------------------------------\n'
                yield '# View: {}\n'.format(view)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_view_syntax(request.args['database'], view)
                    yield 'DROP VIEW IF EXISTS `{}`;\n\n'.format(view)
                    yield '{};\n\n'.format(syntax)
                except Exception as e:
                    errors['views'].append({'k': view, 'v': str(e)})
                    yield '# Error: {}\n\n'.format(e)

        # Build Triggers
        if 'triggers' in options['objects']:
            for trigger in options['objects']['triggers']:
                yield '# ------------------------------------------------------------\n'
                yield '# Trigger: {}\n'.format(trigger)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_trigger_syntax(request.args['database'], trigger)
                    yield 'DROP TRIGGER IF EXISTS `{}`;\n\n'.format(trigger)
                    yield '{};\n\n'.format(syntax)
                except Exception as e:
                    errors['triggers'].append({'k': trigger, 'v': str(e)})
                    yield '# Error: {}\n\n'.format(e)

        # Build Functions
        if 'functions' in options['objects']:
            for function in options['objects']['functions']:
                yield '# ------------------------------------------------------------\n'
                yield '# Function: {}\n'.format(function)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_function_syntax(request.args['database'], function)
                    if syntax:
                        yield 'DROP FUNCTION IF EXISTS `{}`;\n\n'.format(function)
                        yield '{};\n\n'.format(syntax)
                    else:
                        err = "Insufficient privileges to export the function '{}'. You must be the user named in the routine DEFINER clause or have SELECT access to the mysql.proc table".format(function)
                        raise Exception(err)
                except Exception as e:
                    errors['functions'].append({'k': function, 'v': str(e)})
                    yield '# Error: {}\n\n'.format(e)         

        # Build Procedures
        if 'procedures' in options['objects']:
            for procedure in options['objects']['procedures']:
                yield '# ------------------------------------------------------------\n'
                yield '# Procedure: {}\n'.format(procedure)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_procedure_syntax(request.args['database'], procedure)
                    if syntax:
                        yield 'DROP PROCEDURE IF EXISTS `{}`;\n\n'.format(procedure)
                        yield '{};\n\n'.format(syntax)
                    else:
                        err = "# Error: Insufficient privileges to export the procedure '{}'. You must be the user named in the routine DEFINER clause or have SELECT access to the mysql.proc table".format(procedure)
                        raise Exception(err)
                except Exception as e:
                    errors['procedures'].append({'k': procedure, 'v': str(e)})
                    yield '# Error: {}\n\n'.format(e)     

        # Build Events
        if 'events' in options['objects']:
            for event in options['objects']['events']:
                yield '# ------------------------------------------------------------\n'
                yield '# Event: {}\n'.format(event)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_event_syntax(request.args['database'], event)
                    yield 'DROP EVENT IF EXISTS `{}`;\n\n'.format(event)
                    yield '{};\n\n'.format(syntax)
                except Exception as e:
                    errors['events'].append({'k': event, 'v': str(e)})
                    yield '# Error: {}\n\n'.format(e)

        # Build footer
        yield 'SET FOREIGN_KEY_CHECKS = 1;\n\n'

        if len(errors['tables']) == 0 and len(errors['views']) == 0 and len(errors['triggers']) == 0 and len(errors['functions']) == 0 and len(errors['procedures']) == 0 and len(errors['events']) == 0:
            yield '# ************************************************************\n'
            yield '# Export Successful\n'
            yield '# ************************************************************'
        else:
            yield '# ------------------------------------------------------------\n'
            yield '# ERRORS\n'
            yield '# ------------------------------------------------------------\n'
            for table in errors['tables']:
                yield '# [ TABLE: {} ]: {}\n'.format(table['k'], table['v'])
            for view in errors['views']:
                yield '# [ VIEW: {} ]: {}\n'.format(view['k'], view['v'])
            for trigger in errors['triggers']:
                yield '# [ TRIGGER: {} ]: {}\n'.format(trigger['k'], trigger['v'])
            for function in errors['functions']:
                yield '# [ FUNCTION: {} ]: {}\n'.format(function['k'], function['v'])
            for procedure in errors['procedures']:
                yield '# [ PROCEDURE: {} ]: {}\n'.format(procedure['k'], procedure['v'])
            for event in errors['events']:
                yield '# [ EVENT: {} ]: {}\n'.format(event['k'], event['v'])

            yield '\n# ************************************************************\n'
            yield '# Export finished with errors\n'
            yield '# ************************************************************'

        # Close connection
        conn.stop()
