from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from datetime import datetime
import os
import uuid
import json

import models.admin.users
import models.admin.groups
import models.admin.settings
import models.inventory.servers
import models.inventory.regions
import models.utils.export
import connectors.base
import apps.export.export

class Export:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._settings = models.admin.settings.Settings(sql, license)
        self._servers = models.inventory.servers.Servers(sql, license)
        self._regions = models.inventory.regions.Regions(sql)
        self._export = models.utils.export.Export(sql, license)
        # Init core
        self._export_app = apps.export.export.Export(sql)

    def blueprint(self):
        # Init blueprint
        export_blueprint = Blueprint('export', __name__, template_folder='export')

        @export_blueprint.route('/utils/export', methods=['GET','POST','DELETE'])
        @jwt_required()
        def export_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json() if request.get_json() else request.form

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user, data)
            elif request.method == 'DELETE':
                return self.delete(user, data)

        @export_blueprint.route('/utils/export/servers', methods=['GET'])
        @jwt_required()
        def export_servers_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Servers List
            return jsonify({'servers': self._export.get_servers(user)}), 200

        @export_blueprint.route('/utils/export/databases', methods=['GET'])
        @jwt_required()
        def export_databases_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check args
            if 'server_id' not in request.args:
                return jsonify({'message': "Invalid parameters."}), 400

            # Get credentials
            cred = self._export.get_credentials(user['id'], user['group_id'], request.args['server_id'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400

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

        @export_blueprint.route('/utils/export/databases/size', methods=['GET'])
        @jwt_required()
        def export_database_size_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check args
            if 'server_id' not in request.args or 'database' not in request.args:
                return jsonify({'message': "Invalid parameters."}), 400

            # Get credentials
            cred = self._export.get_credentials(user['id'], user['group_id'], request.args['server_id'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400

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

        @export_blueprint.route('/utils/export/tables', methods=['GET'])
        @jwt_required()
        def export_tables_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check args
            if 'server_id' not in request.args or 'database' not in request.args:
                return jsonify({'message': "Invalid parameters."}), 400

            # Get credentials
            cred = self._export.get_credentials(user['id'], user['group_id'], request.args['server_id'])
            if cred is None:
                return jsonify({"message": 'This server does not exist'}), 400

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

        @export_blueprint.route('/utils/export/stop', methods=['POST'])
        @jwt_required()
        def export_stop_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            data = request.get_json()

            # Stop export process
            return self.stop(user, data)

        return export_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        if 'uri' not in request.args:
            exports = self._export.get(user_id=user['id'])
            return jsonify({'exports': exports}), 200

        # Get current export
        export = self._export.get(export_uri=request.args['uri'])

        # Check if export exists
        if len(export) == 0:
            return jsonify({'message': 'This export does not exist'}), 400
        export = export[0]

        # Check restore authority
        if export['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Parse progress
        if export['progress']:
            raw = export['progress'].split(' ')
            export['progress'] = {"value": '0%', "transferred": '0B', "rate": '0B/s', "elapsed": '0:00:00', "eta": None}
            if len(raw) == 3:
                export['progress'] = {"value": '0%', "transferred": raw[0], "rate": raw[1], "elapsed": raw[2], "eta": None}
            elif len(raw) == 4:
                export['progress'] = {"value": raw[0], "transferred": raw[1], "rate": raw[2], "elapsed": raw[3], "eta": None}
            elif len(raw) == 5:
                export['progress'] = {"value": raw[0], "transferred": raw[1], "rate": raw[2], "elapsed": raw[3], "eta": raw[4][3:]}
        # Return data
        return jsonify({'export': export}), 200

    def post(self, user, data):
        # Get group details
        group = self._groups.get(group_id=user['group_id'])[0]

        # Get server details
        server = self._servers.get(user_id=user['id'], group_id=user['group_id'], server_id=data['server_id'])
        if len(server) == 0:
            return jsonify({"message": 'This server does not exist.'}), 400
        elif not server[0]['active']:
            return jsonify({"message": 'The selected server is disabled.'}), 400
        server = server[0]

        # Get region details
        region = self._regions.get(user_id=user['id'], group_id=user['group_id'], region_id=server['region_id'])
        if len(region) == 0:
            return jsonify({"message": 'This server does not have a region.'}), 400
        region = region[0]

        # Generate uuid
        uri = str(uuid.uuid4())

        # Init path
        path = {
            "local": os.path.join(json.loads(self._settings.get(setting_name='FILES'))['local']['path'], 'exports'),
            "remote": '.meteor/exports'
        }

        amazon_s3 = json.loads(self._settings.get(setting_name='FILES'))['amazon_s3']

        # Make exports folder
        if not os.path.exists(os.path.join(path['local'], uri)):
            os.makedirs(os.path.join(path['local'], uri))

        # Build Item
        item = {
            'user_id': user['id'],
            'server_id': data['server_id'],
            'database': data['database'].strip(),
            'mode': data['mode'],
            'format': data['format'],
            'tables': data['tables'],
            'export_schema': data['export_schema'],
            'export_data': data['export_data'],
            'add_drop_table': data['add_drop_table'],
            'export_triggers': data['export_triggers'],
            'export_routines': data['export_routines'],
            'export_events': data['export_events'],
            'size': data['size'],
            'status': 'IN PROGRESS',
            'started': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            'uri': uri,
            'slack_enabled': group['utils_slack_enabled'],
            'slack_url': group['utils_slack_url'],
            'url': data['url']
        }
        item['id'] = self._export.post(user, item)

        # Start import process
        self._export_app.start(user, item, server, region, path, amazon_s3)

        # Return tracking identifier
        return jsonify({'uri': item['uri']}), 200

    def delete(self, user, data):
        for item in data:
            self._export.delete(user, item)
        return jsonify({'message': 'Selected exports deleted'}), 200

    def stop(self, user, data):
        # Check params
        if 'uri' not in data:
            return jsonify({'message': 'uri parameter is required'}), 400

        # Get current export
        export = self._export.get(export_uri=data['uri'])

        # Check if export exists
        if len(export) == 0:
            return jsonify({'message': 'This export does not exist'}), 400
        export = export[0]

        # Check user authority
        if export['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Check if the execution is in progress
        if export['status'] != 'IN PROGRESS':
            return jsonify({'message': 'The execution has already finished'}), 400

        # Stop the execution
        self._export.stop(user, data['uri'])
        return jsonify({'message': 'Stopping execution...'}), 200