from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from flask import Response, stream_with_context
from sentry_sdk import set_user

import io
import re
import csv
import json
import time
import sqlparse
from itertools import repeat
import models.admin.users
import models.admin.groups
import models.client.client
import connectors.client

class Client:
    def __init__(self, app, sql, license):
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._client = models.client.client.Client(sql, license)
        # Init connections
        self._connections = connectors.client.Client(app)

    def blueprint(self):
        # Init blueprint
        client_blueprint = Blueprint('client', __name__, template_folder='client')

        @client_blueprint.route('/client/servers', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def client_servers_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            client_json = request.get_json() if request.method != 'GET' else None

            if request.method == 'GET':
                servers = self._client.get_servers(user['id'], user['group_id'])
                folders = self._client.get_folders(user['id'])
                servers_secured = []
                for s in servers:
                    if s['secured']:
                        servers_secured.append({"id": s['id'], "name": s['name'], "engine": s['engine'], "version": s['version'], "region_id": s['region_id'], "region": s['region'], "shared": s['shared'], "secured": s['secured'], "active": s['active'], "region_shared": s['region_shared'], "region_secured": s['region_secured'], "ssl": s['ssl'], "ssh": s['ssh'], "folder_id": s['folder_id'], "folder_name": s['folder_name']})
                    else:
                        servers_secured.append(s)
                return jsonify({'servers': servers_secured, 'folders': folders}), 200
            elif request.method == 'POST':
                if 'servers' in client_json:
                    self._client.add_servers(client_json['servers'], user)
                    return jsonify({"message": "Servers added"}), 200
                elif 'folder' in client_json:
                    if (self._client.exists_folder({'name': client_json['folder']}, user['id'])):
                        return jsonify({"message": "This folder name currently exists"}), 400
                    self._client.add_folder(client_json['folder'], user['id'])
                    return jsonify({"message": "Folder created"}), 200
            elif request.method == 'PUT':
                if 'servers' in client_json:
                    self._client.move_servers(client_json['servers'], user)
                    return jsonify({"message": "Servers moved"}), 200
                elif 'folder' in client_json:
                    if (self._client.exists_folder(client_json['folder'], user['id'])):
                        return jsonify({"message": "This folder name currently exists"}), 400
                    self._client.rename_folder(client_json['folder'], user['id'])
                    return jsonify({"message": "Folder renamed"}), 200
            elif request.method == 'DELETE':
                if 'servers' in client_json:
                    self._client.remove_servers(client_json['servers'], user['id'])
                    return jsonify({"message": "Servers deleted"}), 200
                elif 'folders' in client_json:
                    self._client.remove_folders(client_json['folders'], user['id'])
                    return jsonify({"message": "Folder deleted"}), 200

        @client_blueprint.route('/client/servers/unassigned', methods=['GET'])
        @jwt_required()
        def client_servers_unassigned_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                servers = self._client.get_servers_unassigned(user['id'], user['group_id'])
                servers_secured = []
                for s in servers:
                    if s['secured']:
                        servers_secured.append({"id": s['id'], "name": s['name'], "engine": s['engine'], "version": s['version'], "region": s['region'], "shared": s['shared'], "secured": s['secured'], "active": s['active'], "region_shared": s['region_shared'], "region_secured": s['region_secured'], "ssl": s['ssl'], "ssh": s['ssh']})
                    else:
                        servers_secured.append(s)
                return jsonify({'servers': servers_secured}), 200

        @client_blueprint.route('/client/databases', methods=['GET'])
        @jwt_required()
        def client_databases_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            # Check Server Disabled
            if not cred['active']:
                return jsonify({"message": 'This server is disabled'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)

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
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/objects', methods=['GET'])
        @jwt_required()
        def client_objects_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            # Get Server Connection
            try:
                conn = self._connections.connect(user['id'], request.args['connection'], cred)

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
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)

                # Get Server Variables
                variables = conn.get_server_variables()
                return jsonify({'variables': variables}), 200
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/execute', methods=['POST'])
        @jwt_required()
        def client_execute_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Group
            group = self._groups.get(group_id=user['group_id'])[0]

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            client_json = request.get_json()

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], client_json['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            # Get Connection Timeout
            if group['client_limits']:
                cred['sql']['timeout_type'] = 'select' if group['client_limits_timeout_mode'] == 2 else 'all'
                cred['sql']['timeout_value'] = group['client_limits_timeout_value']
                if client_json['origin'] == 'editor':
                    cred['sql']['execution_rows'] = group['client_limits_rows']

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], client_json['connection'], cred)
            except Exception as e:
                database = None if client_json['database'] is None or len(client_json['database']) == 0 else client_json['database']
                result = {'query': client_json['queries'][0], 'database': database, 'error': str(e)}
                return jsonify({"data": self.__json([result])}), 400

            # Execute all queries
            execution = []
            errors = False

            for query in client_json['queries']:
                try:
                    # Parse query
                    query = sqlparse.format(query, strip_comments=True).strip()
                    # Select database
                    if query.upper().startswith('USE '):
                        client_json['database'] = query[4:].strip()[1:-1] if query[4:].strip().startswith('`') and query[4:].strip().endswith('`') else query[4:].strip()
                    database = None if client_json['database'] is None or len(client_json['database']) == 0 else client_json['database']
                    # Track query (start)
                    if group['client_tracking'] and (group['client_tracking_mode'] == 1 or (query.strip()[:6].upper() != 'SELECT' and query.strip()[:4].upper() != 'SHOW' and query.strip()[:7].upper() != 'EXPLAIN' and query.strip()[:3].upper() != 'USE')):
                        conn.query_id = self._client.track_query_start(user_id=user['id'], server_id=client_json['server'], database=database, query=query)
                    # Execute query
                    start_time = time.time()
                    result = conn.execute(query=query, database=database)
                    # Append extra data
                    result['time'] = "{0:.3f}".format(time.time() - start_time)
                    result['query'] = query if len(query) < 1000 else f"{query[:1000]}..."
                    result['database'] = database
                    if client_json['origin'] == 'editor' and group['client_limits']:
                        result['limit'] = group['client_limits_rows']
                    # Get table metadata
                    if 'table' in client_json:
                        columns = conn.get_column_names(db=database, table=client_json['table'])
                        pks = conn.get_pk_names(db=database, table=client_json['table'])
                        # Get table column names & column type
                        result['columns'] = columns
                        result['pks'] = pks
                    execution.append(result)
                    # Track query (end)
                    if conn.query_id:
                        self._client.track_query_end(query_id = conn.query_id, status='SUCCESS', records=result['rowCount'], elapsed=result['time'])
                except Exception as e:
                    errors = True
                    result = {'query': query if len(query) < 1000 else f"{query[:1000]}...", 'database': database, 'error': str(e), 'time': "{0:.3f}".format(time.time() - start_time)}
                    execution.append(result)
                    # Track query (end)
                    if conn.query_id:
                        self._client.track_query_end(query_id=conn.query_id, status='FAILED', elapsed=result['time'], error=str(e))
                    if ('executeAll' not in client_json or not client_json['executeAll']):
                        return jsonify({'data': self.__json(execution)}), 400
                finally:
                    conn.query_id = None

            # Return queries data
            return jsonify({'data': self.__json(execution)}), 200 if not errors else 400

        @client_blueprint.route('/client/processlist', methods=['GET'])
        @jwt_required()
        def client_processlist_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)

                # Retrieve Processlist
                return jsonify({'processlist': conn.get_processlist()}), 200
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/explain', methods=['GET'])
        @jwt_required()
        def client_explain_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)
            except Exception as e:
                return jsonify({"message": str(e)}), 400

            # Explain Query
            database = request.args['database'] if 'database' in request.args else None
            try:
                return jsonify({'explain': conn.explain(request.args['query'], database=database)}), 200
            except Exception as e:
                return jsonify({'message': "The selected queries can't be analyzed (not a DML query)"}), 400

        @client_blueprint.route('/client/structure', methods=['GET'])
        @jwt_required()
        def client_structure_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)

                # Get Structure
                columns = conn.get_columns(db=request.args['database'], table=request.args['table'])
                indexes = conn.get_indexes(db=request.args['database'], table=request.args['table'])
                fks = conn.get_fks(db=request.args['database'], table=request.args['table'])
                triggers = conn.get_triggers(db=request.args['database'], table=request.args['table'])
                return jsonify({'columns': self.__json(columns), 'indexes': self.__json(indexes), 'fks': self.__json(fks), 'triggers': self.__json(triggers)}), 200
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/structure/columns', methods=['GET'])
        @jwt_required()
        def client_structure_columns_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)

                # Get Columns
                columns = conn.get_columns_definition(db=request.args['database'], table=request.args['table'])
                return jsonify({'columns': self.__json(columns)}), 200
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/info', methods=['GET'])
        @jwt_required()
        def client_info_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)
            except Exception as e:
                return jsonify({"message": str(e)}), 400

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
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)

                # Get Collations
                collations = conn.get_collations(encoding=request.args['encoding'])
                return jsonify({'collations': self.__json(collations)}), 200
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/import', methods=['POST'])
        @jwt_required()
        def client_import_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.form['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.form['connection'], cred)
            except Exception as e:
                return jsonify({"message": str(e)}), 400
            
            # Get uploaded file
            if 'file' not in request.files or request.files['file'].filename == '':
                return jsonify({"message": 'No file was uploaded'}), 400

            if not self.__allowed_file(request.files['file'].filename):
                return jsonify({"message": 'The file extension is not valid'}), 400

            if request.content_length > 10 * 1024 * 1024:
                return jsonify({"message": 'The upload file exceeds the maximum allowed size (10 MB). Please use the CLIENT section to import this file.'}), 400

            # Execute uploaded file
            try:
                conn.execute(request.files['file'].read().decode("utf-8"), database=request.form['database'], import_file=True)
                return jsonify({'message': 'File uploaded'}), 200
            except Exception as e:
                return jsonify({'message': str(e)}), 400

        @client_blueprint.route('/client/export', methods=['GET'])
        @jwt_required()
        def client_export_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)
            except Exception as e:
                return jsonify({"message": str(e)}), 400

            try:
                options = json.loads(request.args['options'])
                # Start export
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
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            client_json = request.get_json()

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], client_json['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], client_json['connection'], cred)
            except Exception as e:
                return jsonify({"message": str(e)}), 400

            # Start clone
            try:
                self.__clone_object(client_json['options'], conn)
                return jsonify({"message": 'Object cloned'}), 200
            except Exception as e:
                return jsonify({"message": str(e)}), 400

        @client_blueprint.route('/client/saved', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def client_saved_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            saved_json = request.get_json() if request.method != 'GET' else None

            if request.method == 'GET':
                saved_queries = self._client.get_saved_queries(user['id'])
                return jsonify({'saved': saved_queries}), 200
            elif request.method == 'POST':
                qid = self._client.add_saved_query(saved_json, user['id'])
                return jsonify({'data': qid, 'message': 'Saved query added'}), 200
            elif request.method == 'PUT':
                qid = self._client.edit_saved_query(saved_json, user['id'])
                return jsonify({'message': 'Saved query edited'}), 200
            elif request.method == 'DELETE':
                self._client.delete_saved_queries(saved_json, user['id'])
                return jsonify({'message': 'Selected saved queries deleted'}), 200

        @client_blueprint.route('/client/settings', methods=['GET','PUT'])
        @jwt_required()
        def client_settings_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                settings = self._client.get_settings(user['id'])
                return jsonify({'settings': settings}), 200
            elif request.method == 'PUT':
                # Check JSON
                settings_json = request.get_json()
                for key in settings_json.keys():
                    if key not in ['font_size','refresh_rate','secure_mode']:
                        return jsonify({"message": 'Invalid JSON provided'}), 400
                self._client.save_settings(user['id'], settings_json)
                return jsonify({'message': 'Changes saved'}), 200

        @client_blueprint.route('/client/stop', methods=['POST'])
        @jwt_required()
        def client_stop_query_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            client_json = request.get_json()

            # Get current connection - query_id & start_time
            conn = self._connections.get(user['id'], client_json['connection'])

            # Kill Query
            self._connections.kill(user['id'], client_json['connection'])

            # Track query (stopped)
            if conn and conn.query_id:
                elapsed = "{0:.3f}".format(time.time() - conn.start_execution)
                self._client.track_query_end(query_id=conn.query_id, status='STOPPED', elapsed=elapsed)
                conn.query_id = None

            # Return confirmation message
            return jsonify({'message': 'Query stopped'}), 200

        @client_blueprint.route('/client/rights', methods=['GET'])
        @jwt_required()
        def client_rights_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)
            except Exception as e:
                return jsonify({"message": str(e)}), 400

            # Get Rights
            if 'host' not in request.args and 'user' not in request.args:
                try:
                    rights = conn.get_all_rights()
                    return jsonify({'rights': self.__json(rights)}), 200
                except Exception as e:
                    return jsonify({"message": "Cannot retrieve the user permissions. Please check if the current user has SELECT privileges on the 'mysql' database.", "error": str(e)}), 400
            else:
                try:
                    server = conn.get_server_rights(request.args['user'], request.args['host'])
                    database = conn.get_db_rights(request.args['user'], request.args['host'])
                    table = conn.get_table_rights(request.args['user'], request.args['host'])
                    column = conn.get_column_rights(request.args['user'], request.args['host'])
                    proc = conn.get_proc_rights(request.args['user'], request.args['host'])
                    syntax = conn.get_rights_syntax(request.args['user'], request.args['host'])
                    return jsonify({'server': self.__json(server), 'database': self.__json(database), 'table': self.__json(table), 'column': self.__json(column), 'proc': self.__json(proc), 'syntax': self.__json(syntax)}), 200
                except Exception as e:
                    return jsonify({"message": "Cannot retrieve the user permissions. Please check if the current user has SELECT privileges on the 'mysql' database.", "error": str(e)}), 400

        @client_blueprint.route('/client/close', methods=['POST'])
        @jwt_required()
        def client_close_connection_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            # Close Connection
            self._connections.close(user['id'], data['connection'])
            return jsonify({'message': 'Connection closed'}), 200

        @client_blueprint.route('/client/pks', methods=['GET'])
        @jwt_required()
        def client_pks_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['client_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Server Credentials
            cred = self._client.get_credentials(user['id'], user['group_id'], request.args['server'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            try:
                # Get Server Connection
                conn = self._connections.connect(user['id'], request.args['connection'], cred)
            except Exception as e:
                return jsonify({"message": str(e)}), 400

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
                    # Check table size
                    if options['include'] in ['Structure + Content','Content']:
                        info = conn.get_table_info(db=request.args['database'], table=table)
                        if len(info) > 0 and info[0]['data_length'] > 10*1024*1024:
                            raise Exception('To export objects larger than 10 MB use the Utils section.')

                    # Export table
                    syntax = conn.get_table_syntax(request.args['database'], table)
                    if options['includeDropTable']:
                        yield 'DROP TABLE IF EXISTS `{}`;\n\n'.format(table)
                    if options['include'] in ['Structure','Structure + Content']:
                        yield '{};\n\n'.format(syntax)
                    if options['include'] in ['Structure + Content','Content']:
                        yield 'LOCK TABLES `{}` WRITE;\n'.format(table)
                        yield 'ALTER TABLE `{}` DISABLE KEYS;\n\n'.format(table)
                        conn.execute(query=f"SELECT SQL_NO_CACHE * FROM `{table}`", database=request.args['database'], fetch=False)
                        first = True
                        while True:
                            rows = conn.fetch_many(int(options['rows']))
                            if rows is None or len(rows) == 0:
                                break
                            data = ''
                            for row in rows:
                                keys = [f'`{k}`' for k in row.keys()]
                                vals = [i.decode('utf8', 'surrogateescape') if type(i) is bytes else i for i in row.values()]
                                if first:
                                    data += 'INSERT INTO `{}` ({})\nVALUES\n'.format(table, ','.join(keys))
                                    data += '({})'.format(conn.mogrify(','.join(repeat('%s', len(vals))), vals))
                                    first = False
                                else:
                                    data += ',\n({})'.format(conn.mogrify(','.join(repeat('%s', len(vals))), vals))
                            data += ';\n\n'
                            yield data
                            first = True
                        yield 'ALTER TABLE `{}` ENABLE KEYS;\n'.format(table)
                        yield 'UNLOCK TABLES;\n\n'
                except Exception as e:
                    yield '# Error: {}\n\n'.format(e)

        # Build Views
        elif options['object'] == 'view':
            for view in options['items']:
                yield '# ------------------------------------------------------------\n'
                yield '# View: {}\n'.format(view)
                yield '# ------------------------------------------------------------\n'
                try:
                    syntax = conn.get_view_syntax(request.args['database'], view).replace(f"`{request.args['database']}`.", '')
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
                    if options['engine'] in ['MySQL','Amazon Aurora (MySQL)']:
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
                        if options['engine'] in ['MySQL','Amazon Aurora (MySQL)'] and options['includeDelimiters']:
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
                        if options['engine'] in ['MySQL','Amazon Aurora (MySQL)'] and options['includeDelimiters']:
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
                    if options['engine'] in ['MySQL','Amazon Aurora (MySQL)'] and options['includeDelimiters']:
                        yield 'DELIMITER ;;\n{};;\nDELIMITER ;\n\n'.format(syntax)
                    else:
                        yield '{};\n\n'.format(syntax)
                except Exception as e:
                    yield '# Error: {}\n\n'.format(e)

    def __clone_object(self, options, conn):
        conn.disable_fks_checks()
        if options['object'] == 'table':
            for table in options['items']:
                # Check table size
                info = conn.get_table_info(db=options['origin'], table=table)
                if len(info) > 0 and info[0]['data_length'] > 10*1024*1024:
                    raise Exception('To export objects larger than 10 MB use the Utils section.')
                # Drop Table if Exists
                conn.execute(query=f"DROP TABLE IF EXISTS `{table}`", database=options['target'])
                # Create Table
                conn.execute(query=f"CREATE TABLE IF NOT EXISTS `{table}` LIKE `{options['origin']}`.`{table}`", database=options['target'])
                # Create FKs
                fks = conn.execute(query=f"SELECT * FROM information_schema.KEY_COLUMN_USAGE WHERE table_schema = '{options['origin']}' AND table_name = '{table}' AND REFERENCED_TABLE_SCHEMA IS NOT NULL ORDER BY ordinal_position", database=options['target'])['data']
                for fk in fks:
                    db = fk['REFERENCED_TABLE_SCHEMA'] if fk['REFERENCED_TABLE_SCHEMA'] != options['origin'] else options['target']
                    conn.execute(query=f"ALTER TABLE `{table}` ADD CONSTRAINT `{fk['CONSTRAINT_NAME']}` FOREIGN KEY (`{fk['COLUMN_NAME']}`) REFERENCES `{db}`.`{fk['REFERENCED_TABLE_NAME']}` (`{fk['REFERENCED_COLUMN_NAME']}`)", database=options['target'])
                # Insert Data
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
