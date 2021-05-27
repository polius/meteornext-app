from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from flask import Response, stream_with_context

import io
import re
import csv
import json
import datetime
from itertools import repeat
import models.admin.users
import models.admin.groups
import models.client.client
import connectors.client

class Client:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._client = models.client.client.Client(sql)
        # Init connections
        self._connections = connectors.client.Client(app)

    def blueprint(self):
        # Init blueprint
        client_blueprint = Blueprint('client', __name__, template_folder='client')

        @client_blueprint.route('/client/servers', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
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
                servers = self._client.get_servers(user['id'], user['group_id'])
                folders = self._client.get_folders(user['id'])
                if user['inventory_secured'] and not user['owner']:
                    servers_secured = []
                    for s in servers:
                        if s['shared']:
                            servers_secured.append({"id": s['id'], "name": s['name'], "region_id": s['region_id'], "region": s['region'], "engine": s['engine'], "version": s['version'], "shared": s['shared'], "region_shared": s['region_shared'], "folder_id": s['folder_id'], "folder_name": s['folder_name']})
                        elif s['region_shared']:
                            servers_secured.append({"id": s['id'], "name": s['name'], "region_id": s['region_id'], "region": s['region'], "engine": s['engine'], "version": s['version'], "hostname": s['hostname'], "port": s['port'], "username": s['username'], "password": s['password'], "shared": s['shared'], "region_shared": s['region_shared'], "folder_id": s['folder_id'], "folder_name": s['folder_name']})
                        else:
                            servers_secured.append(s)
                    return jsonify({'servers': servers_secured, 'folders': folders}), 200
                return jsonify({'servers': servers, 'folders': folders}), 200
            elif request.method == 'POST':
                if 'servers' in client_json:
                    self._client.add_servers(client_json['servers'], user)
                    return jsonify({"message": "Servers successfully added"}), 200
                elif 'folder' in client_json:
                    if (self._client.exists_folder({'name': client_json['folder']}, user['id'])):
                        return jsonify({"message": "This folder name currently exists"}), 400
                    self._client.add_folder(client_json['folder'], user['id'])
                    return jsonify({"message": "Folder successfully created"}), 200
            elif request.method == 'PUT':
                if 'servers' in client_json:
                    self._client.move_servers(client_json['servers'], user)
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

        @client_blueprint.route('/client/servers/unassigned', methods=['GET'])
        @jwt_required()
        def client_servers_unassigned_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                servers = self._client.get_servers_unassigned(user['id'], user['group_id'])
                if user['inventory_secured'] and not user['owner']:
                    servers_secured = []
                    for s in servers:
                        if s['shared']:
                            servers_secured.append({"id": s['id'], "name": s['name'], "region": s['region'], "engine": s['engine'], "version": s['version'], "shared": s['shared'], "region_shared": s['region_shared']})
                        elif s['region_shared']:
                            servers_secured.append({"id": s['id'], "name": s['name'], "region": s['region'], "engine": s['engine'], "version": s['version'], "hostname": s['hostname'], "port": s['port'], "username": s['username'], "password": s['password'], "shared": s['shared'], "region_shared": s['region_shared']})
                        else:
                            servers_secured.append(s)
                    return jsonify({'servers': servers_secured}), 200
                return jsonify({'servers': servers}), 200

        @client_blueprint.route('/client/databases', methods=['GET'])
        @jwt_required()
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
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400

            # Open a server connection
            try:
                conn = self._connections.connect(user['id'], request.args['connection'], cred)
            except Exception as e:
                return jsonify({"message": str(e)}), 500

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
        @jwt_required()
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
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            try:
                # Get Database Objects
                if 'detailed' in request.args:
                    tables = conn.get_table_info(db=request.args['database'])
                    views = conn.get_view_info(db=request.args['database'])
                    triggers = conn.get_trigger_info(db=request.args['database'])
                    functions = conn.get_function_info(db=request.args['database'])
                    procedures = conn.get_procedure_info(db=request.args['database'])
                    events = conn.get_event_info(db=request.args['database'])
                    return jsonify({'tables': self.__json(tables), 'views': self.__json(views), 'triggers': self.__json(triggers), 'functions': self.__json(functions), 'procedures': self.__json(procedures), 'events': self.__json(events)}), 200
                else:
                    tables = conn.get_all_tables(db=request.args['database'])
                    columns = conn.get_all_columns(db=request.args['database'])
                    triggers = conn.get_all_triggers(db=request.args['database'])
                    events = conn.get_all_events(db=request.args['database'])
                    routines = conn.get_all_routines(db=request.args['database'])
                    return jsonify({'tables': tables, 'columns': columns, 'triggers': triggers, 'events': events, 'routines': routines}), 200
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/variables', methods=['GET'])
        @jwt_required()
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
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Get Server Variables
            variables = conn.get_server_variables()
            return jsonify({'variables': variables}), 200

        @client_blueprint.route('/client/execute', methods=['POST'])
        @jwt_required()
        def client_execute_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Get Group
            group = self._groups.get(group_id=user['group_id'])[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            client_json = request.get_json()

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['id'], user['group_id'], client_json['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], client_json['connection'], cred)

            # Execute all queries
            execution = []
            errors = False
            multiple = type(client_json['database']) == list and len(client_json['database']) == len(client_json['queries'])
            use_database = None

            for index, query in enumerate(client_json['queries']):
                database = client_json['database'][index] if multiple else client_json['database']
                database = None if database and len(database) == 0 else database
                # Handle 'USE' keyword
                if query.strip()[:4].upper() == 'USE ':
                    database = use_database = query.strip()[4:-1] if query.endswith(';') else query.strip()[4:]
                elif use_database is not None:
                    database = use_database
                try:
                    # Execute query
                    result = conn.execute(query=query, database=database)
                    result['query'] = query
                    result['database'] = database
                    # Get table metadata
                    if 'table' in client_json:
                        columns = conn.get_column_names(db=database, table=client_json['table'])
                        pks = conn.get_pk_names(db=database, table=client_json['table'])
                        # Get table column names & column type
                        result['columns'] = columns
                        result['pks'] = pks
                    conn.commit()
                    execution.append(result)
                    # Track query
                    if group['client_tracking'] and (group['client_tracking_mode'] == 1 or query.strip()[:6].upper() != 'SELECT'):
                        self._client.track_query(user_id=user['id'], server_id=client_json['server'], database=database, query=query, status=1, records=result['rowCount'], elapsed=result['time'])

                except Exception as e:
                    # Track query
                    if group['client_tracking'] and (group['client_tracking_mode'] == 1 or query.strip()[:6].upper() != 'SELECT'):
                        self._client.track_query(user_id=user['id'], server_id=client_json['server'], database=database, query=query, status=0, error=str(e))
                    errors = True
                    result = {'query': query, 'database': database, 'error': str(e)}
                    execution.append(result)
                    if ('executeAll' not in client_json or not client_json['executeAll']):
                        return jsonify({'data': self.__json(execution)}), 400

            return jsonify({'data': self.__json(execution)}), 200 if not errors else 400

        @client_blueprint.route('/client/processlist', methods=['GET'])
        @jwt_required()
        def client_processlist_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Retrieve Processlist
            return jsonify({'processlist': conn.get_processlist()}), 200

        @client_blueprint.route('/client/explain', methods=['GET'])
        @jwt_required()
        def client_explain_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Explain Query
            return jsonify({'explain': conn.explain(request.args['query'])}), 200

        @client_blueprint.route('/client/structure', methods=['GET'])
        @jwt_required()
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
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
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
        @jwt_required()
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
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Get Columns
            columns = conn.get_columns_definition(db=request.args['database'], table=request.args['table'])
            return jsonify({'columns': self.__json(columns)}), 200

        @client_blueprint.route('/client/info', methods=['GET'])
        @jwt_required()
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
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
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
        @jwt_required()
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
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Get Collations
            collations = conn.get_collations(encoding=request.args['encoding'])
            return jsonify({'collations': self.__json(collations)}), 200

        @client_blueprint.route('/client/import', methods=['POST'])
        @jwt_required()
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
            cred = self._client.get_credentials(user['id'], user['group_id'], request.form['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.form['connection'], cred)
            
            # Get uploaded file
            if 'file' not in request.files or request.files['file'].filename == '':
                return jsonify({"message": 'No file was uploaded'}), 400

            if not self.__allowed_file(request.files['file'].filename):
                return jsonify({"message": 'The file extension is not valid'}), 400

            if request.content_length > 100 * 1024 * 1024:
                return jsonify({"message": 'The upload file exceeds the maximum allowed size (100MB)'}), 400

            # Execute uploaded file
            try:
                conn.execute(request.files['file'].read().decode("utf-8"), database=request.form['database'], import_file=True)
                conn.commit()
                return jsonify({'message': 'File successfully uploaded'}), 200
            except Exception as e:
                conn.rollback()
                return jsonify({'message': str(e)}), 400

            # command = ['mysql', '-u%s' % db_settings['USER'], '-p%s' % db_settings['PASSWORD'], db_settings['NAME']]
            # proc = subprocess.Popen(command, stdin = uploaded_file.stream)
            # stdout, stderr = proc.communicate()

        @client_blueprint.route('/client/export', methods=['GET'])
        @jwt_required()
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
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Start export
            try:
                options = json.loads(request.args['options'])
                if options['mode'] == 'csv':
                    return Response(stream_with_context(self.__export_csv(options, conn)))
                elif options['mode'] == 'sql':
                    options['engine'] = request.args['engine']
                    return Response(stream_with_context(self.__export_sql(options, conn)))
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/clone', methods=['POST'])
        @jwt_required()
        def client_clone_method():
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
            cred = self._client.get_credentials(user['id'], user['group_id'], client_json['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], client_json['connection'], cred)

            # Start clone
            try:
                self.__clone_object(client_json['options'], cred, conn)
                return jsonify({"message": 'Object cloned successfully'}), 200
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/saved', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
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

        @client_blueprint.route('/client/settings', methods=['GET','PUT'])
        @jwt_required()
        def client_settings_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            settings_json = request.get_json()

            if request.method == 'GET':
                settings = self._client.get_settings(user['id'])
                return jsonify({'settings': settings}), 200
            elif request.method == 'PUT':
                # Check JSON
                for key in settings_json.keys():
                    if key not in ['font_size','refresh_rate']:
                        return jsonify({"message": 'Invalid JSON provided'}), 400
                self._client.save_settings(user['id'], settings_json)
                return jsonify({'message': 'Changes saved'}), 200

        @client_blueprint.route('/client/stop', methods=['GET'])
        @jwt_required()
        def client_stop_query_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Kill Query
            self._connections.kill(user['id'], request.args['connection'])
            return jsonify({'message': 'Query successfully stopped'}), 200

        @client_blueprint.route('/client/rights', methods=['GET'])
        @jwt_required()
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
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Get Rights
            if 'host' not in request.args and 'user' not in request.args:
                try:
                    rights = conn.get_all_rights()
                    return jsonify({'rights': self.__json(rights)}), 200
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
                return jsonify({'server': self.__json(server), 'database': self.__json(database), 'table': self.__json(table), 'column': self.__json(column), 'proc': self.__json(proc), 'syntax': self.__json(syntax)}), 200

        @client_blueprint.route('/client/close', methods=['GET'])
        @jwt_required()
        def client_close_connection_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Close Connection
            self._connections.close(user['id'], request.args['connection'])
            return jsonify({'message': 'Connection successfully closed'}), 200

        @client_blueprint.route('/client/pks', methods=['GET'])
        @jwt_required()
        def client_columns_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials + Connection
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400
            conn = self._connections.connect(user['id'], request.args['connection'], cred)

            # Get Table PKs
            pks = conn.get_table_pks(database=request.args['database'], table=request.args['table'])
            return jsonify({'pks': pks}), 200

        return client_blueprint

    ####################
    # Internal Methods #
    ####################
    def __json(self, data):
        return json.dumps(data, default=self.__json_parser)

    def __json_parser(self, o):
        # if isinstance(o, datetime.datetime):
        return o.__str__()

    def __allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'sql'}

    def __export_csv(self, options, conn):
        for table in options['items']:
            first = options['fields']
            conn.execute(query=f"SELECT * FROM `{table}`", database=request.args['database'], fetch=False)
            while True:
                output = io.StringIO()
                rows = conn.fetch_many(1000)
                if rows == None or len(rows) == 0:
                    break
                writer = csv.DictWriter(output, fieldnames=list(rows[0]))
                if first:
                    writer.writeheader()
                    first = False
                writer.writerows(rows)
                yield output.getvalue()

    def __export_sql(self, options, conn):
        # Build Tables
        if options['object'] == 'table':
            for table in options['items']:
                yield '# ------------------------------------------------------------\n'
                yield '# Table: {}\n'.format(table)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_table_syntax(request.args['database'], table)
                    if options['includeDropTable']:
                        yield 'DROP TABLE IF EXISTS `{}`;\n\n'.format(table)
                    if options['include'] in ['Structure','Structure + Content']:
                        yield '{};\n\n'.format(syntax)
                    if options['include'] in ['Structure + Content','Content']:
                        conn.execute(query=f"SELECT SQL_NO_CACHE * FROM `{table}`", database=request.args['database'], fetch=False)
                        first = True
                        while True:
                            rows = conn.fetch_many(int(options['rows']))
                            if rows is None or len(rows) == 0:
                                break
                            data = ''
                            for row in rows:
                                keys = [f'`{k}`' for k in row.keys()]
                                vals = list(row.values())
                                if first:
                                    data += 'INSERT INTO `{}` ({})\nVALUES\n'.format(table, ','.join(keys))
                                    data += '({})'.format(conn.mogrify(','.join(repeat('%s', len(vals))), vals))
                                    first = False
                                else:
                                    data += ',\n({})'.format(conn.mogrify(','.join(repeat('%s', len(vals))), vals))
                            data += ';\n\n'
                            yield data
                            first = True
                except Exception as e:
                    yield '# Error: {}\n\n'.format(e)

        # Build Views
        elif options['object'] == 'view':
            for view in options['items']:
                yield '# ------------------------------------------------------------\n'
                yield '# View: {}\n'.format(view)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_view_syntax(request.args['database'], view)
                    if options['includeDropTable']:
                        yield 'DROP VIEW IF EXISTS `{}`;\n\n'.format(view)
                    yield '{};\n\n'.format(syntax)
                except Exception as e:
                    yield '# Error: {}\n\n'.format(e)

        # Build Triggers
        elif options['object'] == 'trigger':
            for trigger in options['items']:
                yield '# ------------------------------------------------------------\n'
                yield '# Trigger: {}\n'.format(trigger)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_trigger_syntax(request.args['database'], trigger)
                    syntax = re.sub('DEFINER\s*=\s*`(.*?)`\s*@\s*`(.*?)`\s', '', syntax)
                    if options['includeDropTable']:
                        yield 'DROP TRIGGER IF EXISTS `{}`;\n\n'.format(trigger)
                    if options['engine'] in ['MySQL','Aurora MySQL']:
                        if options['includeDelimiters']:
                            yield 'DELIMITER ;;\n{};;\nDELIMITER ;\n\n'.format(syntax)
                        else:
                            yield '{};\n\n'.format(syntax)
                    else:
                        yield '{};\n\n'.format(syntax)
                except Exception as e:
                    yield '# Error: {}\n\n'.format(e)

        # Build Functions
        elif options['object'] == 'function':
            for function in options['items']:
                yield '# ------------------------------------------------------------\n'
                yield '# Function: {}\n'.format(function)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_function_syntax(request.args['database'], function)
                    syntax = re.sub('DEFINER\s*=\s*`(.*?)`\s*@\s*`(.*?)`\s', '', syntax)
                    if syntax:
                        if options['includeDropTable']:
                            yield 'DROP FUNCTION IF EXISTS `{}`;\n\n'.format(function)
                        if options['engine'] in ['MySQL','Aurora MySQL'] and options['includeDelimiters']:
                            yield 'DELIMITER ;;\n{};;\nDELIMITER ;\n\n'.format(syntax)
                        else:
                            yield '{};\n\n'.format(syntax)
                    else:
                        err = "Insufficient privileges to export the function '{}'. You must be the user named in the routine DEFINER clause or have SELECT access to the mysql.proc table".format(function)
                        raise Exception(err)
                except Exception as e:
                    yield '# Error: {}\n\n'.format(e)         

        # Build Procedures
        elif options['object'] == 'procedure':
            for procedure in options['items']:
                yield '# ------------------------------------------------------------\n'
                yield '# Procedure: {}\n'.format(procedure)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_procedure_syntax(request.args['database'], procedure)
                    syntax = re.sub('DEFINER\s*=\s*`(.*?)`\s*@\s*`(.*?)`\s', '', syntax)
                    if syntax:
                        if options['includeDropTable']:
                            yield 'DROP PROCEDURE IF EXISTS `{}`;\n\n'.format(procedure)
                        if options['engine'] in ['MySQL','Aurora MySQL'] and options['includeDelimiters']:
                            yield 'DELIMITER ;;\n{};;\nDELIMITER ;\n\n'.format(syntax)
                        else:
                            yield '{};\n\n'.format(syntax)
                    else:
                        err = "# Error: Insufficient privileges to export the procedure '{}'. You must be the user named in the routine DEFINER clause or have SELECT access to the mysql.proc table".format(procedure)
                        raise Exception(err)
                except Exception as e:
                    yield '# Error: {}\n\n'.format(e)     

        # Build Events
        elif options['object'] == 'event':
            for event in options['items']:
                yield '# ------------------------------------------------------------\n'
                yield '# Event: {}\n'.format(event)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_event_syntax(request.args['database'], event)
                    syntax = re.sub('DEFINER\s*=\s*`(.*?)`\s*@\s*`(.*?)`\s', '', syntax)
                    if options['includeDropTable']:
                        yield 'DROP EVENT IF EXISTS `{}`;\n\n'.format(event)
                    if options['engine'] in ['MySQL','Aurora MySQL'] and options['includeDelimiters']:
                        yield 'DELIMITER ;;\n{};;\nDELIMITER ;\n\n'.format(syntax)
                    else:
                        yield '{};\n\n'.format(syntax)
                except Exception as e:
                    yield '# Error: {}\n\n'.format(e)

    def __clone_object(self, options, cred, conn):
        conn.disable_fks_checks()
        if options['object'] == 'table':
            for table in options['items']:
                conn.execute(query=f"DROP TABLE IF EXISTS `{table}`", database=options['target'])
                conn.execute(query=f"CREATE TABLE IF NOT EXISTS `{table}` LIKE `{options['origin']}`.`{table}`", database=options['target'])
                conn.execute(query=f"INSERT INTO `{table}` SELECT * FROM `{options['origin']}`.`{table}`", database=options['target'])
        elif options['object'] == 'view':
            for view in options['items']:
                syntax = conn.get_view_syntax(options['origin'], view)
                conn.execute(query=f"DROP VIEW IF EXISTS `{view}`", database=options['target'])
                conn.execute(query=syntax, database=options['target'])
        elif options['object'] == 'trigger':
            for trigger in options['items']:
                syntax = conn.get_trigger_syntax(options['origin'], trigger)
                syntax = re.sub('DEFINER\s*=\s*`(.*?)`\s*@\s*`(.*?)`\s', '', syntax)
                conn.execute(query=f"DROP TRIGGER IF EXISTS `{trigger}`", database=options['target'])
                conn.execute(query=syntax, database=options['target'])
        elif options['object'] == 'function':
            for function in options['items']:
                syntax = conn.get_function_syntax(options['origin'], function)
                syntax = re.sub('DEFINER\s*=\s*`(.*?)`\s*@\s*`(.*?)`\s', '', syntax)
                conn.execute(query=f"DROP FUNCTION IF EXISTS `{function}`", database=options['target'])
                conn.execute(query=syntax, database=options['target'])
        elif options['object'] == 'procedure':
            for procedure in options['items']:
                syntax = conn.get_procedure_syntax(options['origin'], procedure)
                syntax = re.sub('DEFINER\s*=\s*`(.*?)`\s*@\s*`(.*?)`\s', '', syntax)
                conn.execute(query=f"DROP PROCEDURE IF EXISTS `{procedure}`", database=options['target'])
                conn.execute(query=syntax, database=options['target'])
        elif options['object'] == 'event':
            for event in options['items']:
                syntax = conn.get_event_syntax(options['origin'], event)
                syntax = re.sub('DEFINER\s*=\s*`(.*?)`\s*@\s*`(.*?)`\s', '', syntax)
                conn.execute(query=f"DROP EVENT IF EXISTS `{event}`", database=options['target'])
                conn.execute(query=syntax, database=options['target'])
        conn.enable_fks_checks()
