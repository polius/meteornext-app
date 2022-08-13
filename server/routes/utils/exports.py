from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user
from datetime import datetime
import os
import sys
import uuid
import json

import models.admin.users
import models.admin.groups
import models.admin.settings
import models.inventory.servers
import models.inventory.regions
import models.utils.exports
import apps.exports.exports

class Exports:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._settings = models.admin.settings.Settings(sql, self._license)
        self._servers = models.inventory.servers.Servers(sql, self._license)
        self._regions = models.inventory.regions.Regions(sql)
        self._export = models.utils.exports.Exports(sql, self._license)
        # Init core
        self._export_app = apps.exports.exports.Exports(sql)
        # Retrieve base path
        self._bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self._base_path = os.path.realpath(os.path.dirname(sys.executable)) if self._bin else os.path.realpath(os.path.dirname(sys.argv[0]))

    def blueprint(self):
        # Init blueprint
        exports_blueprint = Blueprint('exports', __name__, template_folder='exports')

        @exports_blueprint.route('/utils/exports', methods=['GET','POST','DELETE'])
        @jwt_required()
        def exports_method():
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
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user)
            elif request.method == 'DELETE':
                return self.delete(user)

        @exports_blueprint.route('/utils/exports/stop', methods=['POST'])
        @jwt_required()
        def exports_stop_method():
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
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Stop export process
            return self.stop(user)

        return exports_blueprint

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

        # Check import authority
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

    def post(self, user):
        # Get data
        data = request.get_json()

        # Get group details
        group = self._groups.get(group_id=user['group_id'])[0]

        # Check Coins
        if (user['coins'] - group['utils_coins']) < 0:
            return jsonify({'message': 'Insufficient Coins'}), 400

        # Get server details
        server = self._servers.get(user_id=user['id'], group_id=user['group_id'], server_id=data['server_id'])
        if len(server) == 0:
            return jsonify({"message": 'This server does not exist.'}), 400
        server = server[0]
        if not server['active']:
            return jsonify({"message": 'The selected server is disabled.'}), 400

        # Get region details
        region = self._regions.get(user_id=user['id'], group_id=user['group_id'], region_id=server['region_id'])
        if len(region) == 0:
            return jsonify({"message": 'This server does not have a region.'}), 400
        region = region[0]

        # Generate uuid
        uri = str(uuid.uuid4())

        # Get Amazon S3 credentials
        amazon_s3 = json.loads(self._settings.get(setting_name='AMAZON'))
        if not amazon_s3['enabled']:
            return jsonify({"message": 'To perform exports enable the Amazon S3 flag in the Admin Panel.'}), 400

        # Make exports folder
        if not os.path.exists(f"{self._base_path}/files/exports/{uri}"):
            os.makedirs(f"{self._base_path}/files/exports/{uri}")

        # Consume Coins
        self._users.consume_coins(user, group['utils_coins'])
        coins = user['coins'] - group['utils_coins']

        # Create new export
        item = {
            'username': user['username'],
            'server_id': data['server_id'],
            'server_name': server['name'],
            'region_name': region['name'],
            'mode': data['mode'],
            'database': data['database'].strip(),
            'tables': f"{{\"t\":{json.dumps(data['tables'], separators=(',', ':'))}}}" if data['tables'] else None,
            'export_schema': data['export_schema'],
            'export_data': data['export_data'],
            'add_drop_table': data['add_drop_table'],
            'export_triggers': data['export_triggers'],
            'export_routines': data['export_routines'],
            'export_events': data['export_events'],
            'size': data['size'],
            'status': 'QUEUED',
            'created': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            'uri': uri,
            'slack_enabled': group['utils_slack_enabled'],
            'slack_url': group['utils_slack_url'],
            'url': data['url']
        }
        self._export.post(user, item)

        # Return tracking identifier
        return jsonify({'uri': item['uri'], 'coins': coins}), 200

    def delete(self, user):
        data = request.get_json()
        for item in data:
            self._export.delete(user, item)
        return jsonify({'message': 'Selected exports deleted'}), 200

    def stop(self, user):
        # Get data
        data = request.get_json()

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
        if export['status'] in ['SUCCESS','FAILED','STOPPED']:
            return jsonify({'message': 'The execution has already finished'}), 400

        # Stop the execution
        self._export.stop(user, data['uri'])
        return jsonify({'message': 'Stopping execution...'}), 200