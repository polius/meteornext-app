from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user
import os
import json

import models.admin.users
import models.admin.settings
import models.inventory.servers
import models.inventory.regions
import models.inventory.cloud
import models.utils.utils
import models.utils.imports
import models.utils.exports
import models.utils.clones
import models.utils.utils_queued
import models.admin.inventory.servers
import models.admin.inventory.regions
import apps.imports.imports
import apps.exports.exports
import apps.clones.clones
import connectors.base

class Utils:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._settings = models.admin.settings.Settings(sql, license)
        self._servers = models.inventory.servers.Servers(sql, license)
        self._regions = models.inventory.regions.Regions(sql)
        self._cloud = models.inventory.cloud.Cloud(sql)
        self._utils = models.utils.utils.Utils(sql, license)
        self._imports = models.utils.imports.Imports(sql, license)
        self._exports = models.utils.exports.Exports(sql, license)
        self._clones = models.utils.clones.Clones(sql, license)
        self._utils_queued = models.utils.utils_queued.Utils_Queued(sql, license)
        self._servers_admin = models.admin.inventory.servers.Servers(sql, license)
        self._regions_admin = models.admin.inventory.regions.Regions(sql)
        # Init cores
        self._import_app = apps.imports.imports.Imports(sql)
        self._export_app = apps.exports.exports.Exports(sql)
        self._clone_app = apps.clones.clones.Clones(sql)

    def blueprint(self):
        # Init blueprint
        utils_blueprint = Blueprint('utils', __name__, template_folder='utils')

        @utils_blueprint.route('/utils/servers', methods=['GET'])
        @jwt_required()
        def utils_servers_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or (not user['admin'] and not user['utils_enabled']):
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if 'server_id' in request.args:
                return self.get(user)
            else:
                return jsonify({'servers': self._utils.get_servers(user)}), 200

        @utils_blueprint.route('/utils/servers/test', methods=['POST'])
        @jwt_required()
        def utils_servers_test_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or (not user['admin'] and not user['inventory_enabled']):
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            # Check args
            if 'server' not in data or 'region' not in data:
                return jsonify({'message': 'Invalid Parameters'}), 400

            # Return test result
            return self.test(user, data)

        @utils_blueprint.route('/utils/databases', methods=['GET'])
        @jwt_required()
        def utils_databases_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or (not user['admin'] and not user['utils_enabled']):
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check args
            if 'server_id' not in request.args:
                return jsonify({'message': "Invalid parameters."}), 400

            # Get credentials
            cred = self._utils.get_credentials(user['id'], user['group_id'], request.args['server_id'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            # Connect to the server
            conn = connectors.base.Base(cred)
            try:
                conn.connect()
            except Exception as e:
                return jsonify({"message": str(e)}), 400

            # Get databases
            try:
                return jsonify({'databases': conn.get_databases()}), 200
            finally:
                conn.stop()

        @utils_blueprint.route('/utils/databases/size', methods=['GET'])
        @jwt_required()
        def utils_database_size_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or (not user['admin'] and not user['utils_enabled']):
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check args
            if 'server_id' not in request.args or 'database' not in request.args:
                return jsonify({'message': "Invalid parameters."}), 400

            # Get credentials
            cred = self._utils.get_credentials(user['id'], user['group_id'], request.args['server_id'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            # Connect to the server
            conn = connectors.base.Base(cred)
            try:
                conn.connect()
            except Exception as e:
                return jsonify({"message": str(e)}), 400

            # Get database size
            try:
                return jsonify({'size': conn.get_database_size(request.args['database'])}), 200
            finally:
                conn.stop()

        @utils_blueprint.route('/utils/tables', methods=['GET'])
        @jwt_required()
        def utils_tables_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or (not user['admin'] and not user['utils_enabled']):
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check args
            if 'server_id' not in request.args or 'database' not in request.args:
                return jsonify({'message': "Invalid parameters."}), 400

            # Get credentials
            cred = self._utils.get_credentials(user['id'], user['group_id'], request.args['server_id'])
            if cred is None:
                return jsonify({"message": 'This server does not exist in your inventory'}), 400

            # Connect to the server
            conn = connectors.base.Base(cred)
            try:
                conn.connect()
            except Exception as e:
                return jsonify({"message": str(e)}), 400

            # Get tables
            try:
                return jsonify({'tables': conn.get_tables_detailed(request.args['database'])}), 200
            finally:
                conn.stop()

        return utils_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        # Get servers
        servers = self._servers_admin.get(server_id=request.args['server_id']) if user['admin'] else self._servers.get(user['id'], user['group_id'], request.args['server_id'])

        # Protect SSL Keys
        for server in servers:
            server['ssl_client_key'] = '<ssl_client_key>' if server['ssl_client_key'] is not None else None
            server['ssl_client_certificate'] = '<ssl_client_certificate>' if server['ssl_client_certificate'] is not None else None
            server['ssl_ca_certificate'] = '<ssl_ca_certificate>' if server['ssl_ca_certificate'] is not None else None

        # Check Inventory Secured
        if not user['admin']:
            servers_secured = []
            for s in servers:
                if s['secured']:
                    servers_secured.append({"id": s['id'], "name": s['name'], "region_id": s['region_id'], "region": s['region'], "shared": s['shared'], "secured": s['secured'], "region_shared": s['region_shared'], "region_secured": s['region_secured'], "usage": s['usage'], "ssh": s['ssh'], "ssl": s['ssl']})
                else:
                    servers_secured.append(s)
            return jsonify({'data': servers_secured}), 200
        return jsonify({'data': servers}), 200

    def test(self, user, data):
        # Get Region
        region = self._regions.get(user['id'], user['group_id'], data['region']) if not user['admin'] else self._regions_admin.get(region_id=data['region'])
        if len(region) == 0:
            return jsonify({'message': "Can't test the connection. Invalid region provided."}), 400
        region = region[0]

        # Get Server
        server_origin = self._servers.get(user['id'], user['group_id'], data['server']) if not user['admin'] else self._servers_admin.get(server_id=data['server'])
        if len(server_origin) == 0:
            return jsonify({'message': "Can't test the connection. Invalid server provided."}), 400
        server = server_origin[0]

        # Check SQL Connection
        try:
            conf = {}
            conf['ssh'] = {'enabled': region['ssh_tunnel'], 'hostname': region['hostname'], 'port': region['port'], 'username': region['username'], 'password': region['password'], 'key': region['key']}
            conf['sql'] = {'engine': server['engine'], 'hostname': server['hostname'], 'port': server['port'], 'username': server['username'], 'password': server['password'], 'ssl': server['ssl'], 'ssl_client_key': server['ssl_client_key'], 'ssl_client_certificate': server['ssl_client_certificate'], 'ssl_ca_certificate': server['ssl_ca_certificate'], 'ssl_verify_ca': server['ssl_verify_ca']}
            sql = connectors.base.Base(conf)
            sql.test_sql()
            return jsonify({'message': 'Connection Successful'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 400

    def check_queued(self):
        # Delete finished executions from the queue
        self._utils_queued.delete_finished()

        # Populate new queued executions
        self._utils_queued.build()

        # Build dictionary of executions
        executions_raw = self._utils_queued.get_next()
        groups = {}
        execution_ids = {"import":[],"export":[],"clone":[]}
        for i in executions_raw:
            concurrent = groups.get(i['group'], 0)
            if concurrent < i['concurrent']:
                groups[i['group']] = concurrent + 1
                if i['status'] == 'QUEUED':
                    execution_ids[i['source_type']].append(i['source_id'])
        executions = {"import":[],"export":[],"clone":[]}
        if len(execution_ids['import']):
            executions['import'] = self._utils_queued.get_queued_imports(import_ids=execution_ids['import'])
        if len(execution_ids['export']):
            executions['export'] = self._utils_queued.get_queued_exports(export_ids=execution_ids['export'])
        if len(execution_ids['clone']):
            executions['clone'] = self._utils_queued.get_queued_clones(clone_ids=execution_ids['clone'])

        # Get file path
        file_path = json.loads(self._settings.get(setting_name='FILES'))['path']

        # Get Amazon S3 credentials
        amazon_s3 = json.loads(self._settings.get(setting_name='AMAZON'))

        # Process imports
        self.__process_queued_imports(executions['import'], file_path)
        self.__process_queued_exports(executions['export'], file_path, amazon_s3)
        self.__process_queued_clones(executions['clone'], file_path, amazon_s3)

    def __process_queued_imports(self, executions, file_path):
        for execution in executions:
            # Build user
            user = {"id": execution['user_id']}

            # Get server details
            server = self._servers.get(user_id=execution['user_id'], group_id=execution['group_id'], server_id=execution['server_id'])
            if len(server) == 0:
                self._imports.update_status(user, execution['id'], 'FAILED', 'This server no longer exists in your inventory.')
                continue
            server = server[0]
            if not server['active']:
                self._imports.update_status(user, execution['id'], 'FAILED', 'The selected server is disabled.')
                continue

            # Get region details
            region = self._regions.get(user_id=execution['user_id'], group_id=execution['group_id'], region_id=server['region_id'])
            if len(region) == 0:
                self._imports.update_status(user, execution['id'], 'FAILED', "This server's region no longer exists in your inventory.")
                continue
            region = region[0]

            # Init path
            path = {
                "local": os.path.join(file_path, 'imports'),
                "remote": '.meteor/imports'
            }

            # Init amazon s3
            amazon_s3 = None
            if execution['mode'] == 'cloud':
                details = json.loads(execution['details'])
                cloud = self._cloud.get(user_id=execution['user_id'], group_id=execution['group_id'], cloud_id=details['cloud']['id'])
                if len(cloud) == 0:
                    self._imports.update_status(user, execution['id'], 'FAILED', 'This cloud key no longer exists in your inventory.')
                    continue
                cloud = cloud[0]
                amazon_s3 = {
                    "aws_access_key": cloud['access_key'],
                    "aws_secret_access_key": cloud['secret_key'],
                    "bucket": details['bucket']
                }

            # Build item
            item = {
                "id": execution['id'],
                "mode": execution['mode'],
                "source": execution['source'],
                "format": execution['format'],
                "selected": None if execution['selected'] is None else [i.split('|')[0] for i in execution['selected'].split('\n')],
                "size": execution['size'],
                "database": execution['database'],
                "recreate_database": execution['recreate_database'],
                "url": execution['url'],
                "uri": execution['uri'],
                "user_id": execution['user_id'],
                "slack_enabled": execution['slack_enabled'],
                "username": execution['username'],
                "server_name": server['name'],
                "region_name": region['name'],
                "slack_url": execution['slack_url']
            }

            # Start import process
            self._imports.update_status(user, execution['id'], 'STARTING')
            self._import_app.start(user, item, server, region, path, amazon_s3)

    def __process_queued_exports(self, executions, file_path, amazon_s3):
        for execution in executions:
            # Build user
            user = {"id": execution['user_id']}

            # Get server details
            server = self._servers.get(user_id=execution['user_id'], group_id=execution['group_id'], server_id=execution['server_id'])
            if len(server) == 0:
                self._exports.update_status(user, execution['id'], 'FAILED', 'This server no longer exists in your inventory.')
                continue
            server = server[0]
            if not server['active']:
                self._exports.update_status(user, execution['id'], 'FAILED', 'The selected server is disabled.')
                continue

            # Get region details
            region = self._regions.get(user_id=execution['user_id'], group_id=execution['group_id'], region_id=server['region_id'])
            if len(region) == 0:
                self._exports.update_status(user, execution['id'], 'FAILED', "This server's region no longer exists in your inventory.")
                continue
            region = region[0]

            # Init path
            path = {
                "local": os.path.join(file_path, 'exports'),
                "remote": '.meteor/exports'
            }

            # Get Amazon S3 credentials
            if not amazon_s3['enabled']:
                self._exports.update_status(user, execution['id'], 'FAILED', "To perform exports enable the Amazon S3 flag in the Admin Panel.")
                continue

            # Build Item
            item = {
                "id": execution['id'],
                "mode": execution['mode'],
                "database": execution['database'],
                "tables": execution['tables'],
                "size": execution['size'],
                "export_schema": execution['export_schema'],
                "add_drop_table": execution['add_drop_table'],
                "export_data": execution['export_data'],
                "export_triggers": execution['export_triggers'],
                "export_routines": execution['export_routines'],
                "export_events": execution['export_events'],
                "url": execution['url'],
                "uri": execution['uri'],
                "server_name": server['name'],
                "region_name": region['name'],
                "username": execution['username'],
                "slack_enabled": execution['slack_enabled'],
                "slack_url": execution['slack_url']
            }

            # Start export process
            self._exports.update_status(user, execution['id'], 'STARTING')
            self._export_app.start(user, item, server, region, path, amazon_s3)

    def __process_queued_clones(self, executions, file_path, amazon_s3):
        for execution in executions:
            # Build user
            user = {"id": execution['user_id']}

            # Get server details (source)
            servers = {}
            servers['source'] = self._servers.get(user_id=user['id'], group_id=execution['group_id'], server_id=execution['source_server'])
            if len(servers['source']) == 0:
                self._clones.update_status(user, execution['id'], 'FAILED', 'The source server no longer exists in your inventory.')
                continue
            servers['source'] = servers['source'][0]
            if not servers['source']['active']:
                self._clones.update_status(user, execution['id'], 'FAILED', 'The source server is disabled.')
                continue

            # Get server details (destination)
            servers['destination'] = self._servers.get(user_id=user['id'], group_id=execution['group_id'], server_id=execution['destination_server'])
            if len(servers['destination']) == 0:
                self._clones.update_status(user, execution['id'], 'FAILED', 'The destination server no longer exists in your inventory.')
                continue
            servers['destination'] = servers['destination'][0]
            if not servers['destination']['active']:
                self._clones.update_status(user, execution['id'], 'FAILED', 'The destination server is disabled.')
                continue

            # Get region details (source)
            regions = {}
            regions['source'] = self._regions.get(user_id=user['id'], group_id=execution['group_id'], region_id=servers['source']['region_id'])
            if len(regions['source']) == 0:
                self._clones.update_status(user, execution['id'], 'FAILED', "The source servers' region no longer exists in your inventory.")
                continue
            regions['source'] = regions['source'][0]

            # Get region details (destination)
            regions['destination'] = self._regions.get(user_id=user['id'], group_id=execution['group_id'], region_id=servers['destination']['region_id'])
            if len(regions['destination']) == 0:
                self._clones.update_status(user, execution['id'], 'FAILED', "The destination servers' region no longer exists in your inventory.")
                continue
            regions['destination'] = regions['destination'][0]

            # Init path
            path = {
                "local": os.path.join(file_path, 'clones'),
                "remote": '.meteor/clones'
            }

            # Get Amazon S3 credentials
            if not amazon_s3['enabled']:
                self._clones.update_status(user, execution['id'], 'FAILED', "To perform clones enable the Amazon S3 flag in the Admin Panel.")
                continue

            # Build Item
            item = {
                "id": execution['id'],
                "mode": execution['mode'],
                "recreate_database": execution['recreate_database'],
                "source_database": execution['source_database'],
                "destination_database": execution['destination_database'],
                "tables": execution['tables'],
                "export_schema": execution['export_schema'],
                "add_drop_table": execution['add_drop_table'],
                "export_data": execution['export_data'],
                "export_triggers": execution['export_triggers'],
                "export_routines": execution['export_routines'],
                "export_events": execution['export_events'],
                "size": execution['size'],
                "url": execution['url'],
                "uri": execution['uri'],
                "source_server_name": servers['source']['name'],
                "source_region_name": regions['source']['name'],
                "destination_server_name": servers['destination']['name'],
                "destination_region_name": regions['destination']['name'],
                "username": execution['username'],
                "slack_enabled": execution['slack_enabled'],
                "slack_url": execution['slack_url']
            }

            # Start clone process
            self._clones.update_status(user, execution['id'], 'STARTING')
            self._clone_app.start(user, item, servers, regions, path, amazon_s3)
