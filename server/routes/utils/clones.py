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
import models.utils.clones
import connectors.base
import apps.clones.clones

class Clones:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._settings = models.admin.settings.Settings(sql, license)
        self._servers = models.inventory.servers.Servers(sql, license)
        self._regions = models.inventory.regions.Regions(sql)
        self._clone = models.utils.clones.Clones(sql, license)
        # Init core
        self._clone_app = apps.clones.clones.Clones(sql)

    def blueprint(self):
        # Init blueprint
        clones_blueprint = Blueprint('clones', __name__, template_folder='clones')

        @clones_blueprint.route('/utils/clones', methods=['GET','POST','DELETE'])
        @jwt_required()
        def clones_method():
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

        @clones_blueprint.route('/utils/clones/servers', methods=['GET'])
        @jwt_required()
        def clones_servers_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Servers List
            return jsonify({'servers': self._clone.get_servers(user)}), 200

        @clones_blueprint.route('/utils/clones/databases', methods=['GET'])
        @jwt_required()
        def clones_databases_method():
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
            cred = self._clone.get_credentials(user['id'], user['group_id'], request.args['server_id'])
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

        @clones_blueprint.route('/utils/clones/databases/size', methods=['GET'])
        @jwt_required()
        def clones_database_size_method():
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
            cred = self._clone.get_credentials(user['id'], user['group_id'], request.args['server_id'])
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

        @clones_blueprint.route('/utils/clones/tables', methods=['GET'])
        @jwt_required()
        def clones_tables_method():
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
            cred = self._clone.get_credentials(user['id'], user['group_id'], request.args['server_id'])
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

        @clones_blueprint.route('/utils/clones/stop', methods=['POST'])
        @jwt_required()
        def clones_stop_method():
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

            # Stop clone process
            return self.stop(user, data)

        return clones_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        if 'uri' not in request.args:
            clones = self._clone.get(user_id=user['id'])
            return jsonify({'clones': clones}), 200

        # Get current clone
        clone = self._clone.get(clone_uri=request.args['uri'])
        # Check if clone exists
        if len(clone) == 0:
            return jsonify({'message': 'This clone does not exist'}), 400
        clone = clone[0]

        # Check import authority
        if clone['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Parse progress
        clone['progress_export'] = self.parse_progress(clone['progress_export']) if clone['progress_export'] else None
        clone['progress_import'] = self.parse_progress(clone['progress_import']) if clone['progress_import'] else None

        # Return data
        return jsonify({'clone': clone}), 200

    def post(self, user, data):
        # Get group details
        group = self._groups.get(group_id=user['group_id'])[0]

        # Get server details (source)
        servers = {}
        servers['source'] = self._servers.get(user_id=user['id'], group_id=user['group_id'], server_id=data['source_server'])
        if len(servers['source']) == 0:
            return jsonify({"message": 'The source server does not exist.'}), 400
        servers['source'] = servers['source'][0]
        if not servers['source']['active']:
            return jsonify({"message": 'The source server is disabled.'}), 400

        # Get server details (destination)
        servers['destination'] = self._servers.get(user_id=user['id'], group_id=user['group_id'], server_id=data['destination_server'])
        if len(servers['destination']) == 0:
            return jsonify({"message": 'The destination server does not exist.'}), 400
        servers['destination'] = servers['destination'][0]
        if not servers['destination']['active']:
            return jsonify({"message": 'The destination server is disabled.'}), 400

        # Get region details (source)
        regions = {}
        regions['source'] = self._regions.get(user_id=user['id'], group_id=user['group_id'], region_id=servers['source']['region_id'])
        if len(regions['source']) == 0:
            return jsonify({"message": 'The source server does not have a region.'}), 400
        regions['source'] = regions['source'][0]

        # Get region details (destination)
        regions['destination'] = self._regions.get(user_id=user['id'], group_id=user['group_id'], region_id=servers['destination']['region_id'])
        if len(regions['destination']) == 0:
            return jsonify({"message": 'The destination server does not have a region.'}), 400
        regions['destination'] = regions['destination'][0]

        # Generate uuid
        uri = str(uuid.uuid4())

        # Init path
        path = {
            "local": os.path.join(json.loads(self._settings.get(setting_name='FILES'))['path'], 'clones'),
            "remote": '.meteor/clones'
        }

        # Get Amazon S3 credentials
        amazon_s3 = json.loads(self._settings.get(setting_name='AMAZON'))
        if not amazon_s3['enabled']:
            return jsonify({"message": 'To perform clones enable the Amazon S3 flag in the Admin Panel.'}), 400

        # Make clones folder
        if not os.path.exists(os.path.join(path['local'], uri)):
            os.makedirs(os.path.join(path['local'], uri))

        # Build Item
        item = {
            'username': user['username'],
            'source_server': data['source_server'],
            'source_database': data['source_database'].strip(),
            'source_server_name': servers['source']['name'],
            'source_region_name': regions['source']['name'],
            'destination_server': data['destination_server'],
            'destination_database': data['destination_database'].strip(),
            'destination_server_name': servers['destination']['name'],
            'destination_region_name': regions['destination']['name'],
            'create_database': data['create_database'],
            'drop_database': data['drop_database'],
            'mode': data['mode'],
            'tables': f"{{\"t\":{json.dumps(data['tables'], separators=(',', ':'))}}}" if data['tables'] else None,
            'export_schema': data['export_schema'],
            'export_data': data['export_data'],
            'add_drop_table': data['add_drop_table'],
            'export_triggers': data['export_triggers'],
            'export_routines': data['export_routines'],
            'export_events': data['export_events'],
            'size': data['size'],
            'status': 'STARTING' if not group['utils_concurrent'] else 'QUEUED',
            'created': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            'uri': uri,
            'slack_enabled': group['utils_slack_enabled'],
            'slack_url': group['utils_slack_url'],
            'url': data['url']
        }
        item['id'] = self._clone.post(user, item)

        # Start import process
        if not group['utils_concurrent']:
            self._clone_app.start(user, item, servers, regions, path, amazon_s3)

        # Return tracking identifier
        return jsonify({'uri': item['uri']}), 200

    def delete(self, user, data):
        for item in data:
            self._clone.delete(user, item)
        return jsonify({'message': 'Selected clones deleted'}), 200

    def stop(self, user, data):
        # Check params
        if 'uri' not in data:
            return jsonify({'message': 'uri parameter is required'}), 400

        # Get current clone
        clone = self._clone.get(clone_uri=data['uri'])

        # Check if clone exists
        if len(clone) == 0:
            return jsonify({'message': 'This clone does not exist'}), 400
        clone = clone[0]

        # Check user authority
        if clone['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Check if the execution is in progress
        if clone['status'] != 'IN PROGRESS':
            return jsonify({'message': 'The execution has already finished'}), 400

        # Stop the execution
        self._clone.stop(user, data['uri'])
        return jsonify({'message': 'Stopping execution...'}), 200

    def parse_progress(self, data):
        raw = data.split(' ')
        progress = {"value": '0%', "transferred": '0B', "rate": '0B/s', "elapsed": '0:00:00', "eta": None}
        if len(raw) == 3:
            progress = {"value": '0%', "transferred": raw[0], "rate": raw[1], "elapsed": raw[2], "eta": None}
        elif len(raw) == 4:
            progress = {"value": raw[0], "transferred": raw[1], "rate": raw[2], "elapsed": raw[3], "eta": None}
        elif len(raw) == 5:
            progress = {"value": raw[0], "transferred": raw[1], "rate": raw[2], "elapsed": raw[3], "eta": raw[4][3:]}
        return progress
