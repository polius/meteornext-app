from re import split
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from werkzeug.utils import secure_filename
import os
import uuid
import json
import shutil
import boto3

import models.admin.users
import models.utils.restore
import models.utils.scans
import models.admin.settings
import models.inventory.servers
import models.inventory.cloud
import apps.restore.restore
import apps.restore.scan

class Restore:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._restore = models.utils.restore.Restore(sql)
        self._scans = models.utils.scans.Scans(sql)
        self._settings = models.admin.settings.Settings(sql)
        self._servers = models.inventory.servers.Servers(sql)
        self._cloud = models.inventory.cloud.Cloud(sql)
        # Init core
        self._restore_app = apps.restore.restore.Restore(sql)
        self._scan_app = apps.restore.scan.Scan(sql)

    def blueprint(self):
        # Init blueprint
        restore_blueprint = Blueprint('restore', __name__, template_folder='restore')

        @restore_blueprint.route('/utils/restore', methods=['GET','POST','DELETE'])
        @jwt_required()
        def restore_method():
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

        @restore_blueprint.route('/utils/restore/check', methods=['GET'])
        @jwt_required()
        def restore_check_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Return if there's free space left to upload a file
            return jsonify({'check': shutil.disk_usage("/").free >= int(request.args['size'])}), 200

        @restore_blueprint.route('/utils/restore/servers', methods=['GET'])
        @jwt_required()
        def restore_servers_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Servers List
            return jsonify({'servers': self._restore.get_servers(user)}), 200

        @restore_blueprint.route('/utils/restore/stop', methods=['POST'])
        @jwt_required()
        def restore_stop_method():
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

            # Stop restore process
            return self.stop(user, data)

        @restore_blueprint.route('/utils/restore/scan', methods=['POST','GET'])
        @jwt_required()
        def restore_scan_method():
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

            if request.method == 'GET':
                # Return scanned file
                try:
                    scan = self.get_scan(user, request.args['id'])
                    return jsonify(scan), 200
                except Exception as e:
                    return jsonify({'message': str(e)}), 400
            elif request.method == 'POST':
                # Register a new scan
                try:
                    scan = self.post_scan(user, data)
                    return jsonify(scan), 200
                except Exception as e:
                    return jsonify({'message': str(e)}), 400

        @restore_blueprint.route('/utils/restore/scan/stop', methods=['POST'])
        @jwt_required()
        def restore_scan_stop_method():
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

            # Stop Scan
            return self.stop_scan(user, data)

        @restore_blueprint.route('/utils/restore/s3/buckets', methods=['GET'])
        @jwt_required()
        def restore_s3_buckets_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Buckets
            return self.get_s3_buckets(user)

        @restore_blueprint.route('/utils/restore/s3/objects', methods=['GET'])
        @jwt_required()
        def restore_s3_objects_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Objects
            return self.get_s3_objects(user)

        return restore_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        if 'id' not in request.args:
            restore = self._restore.get(user_id=user['id'])
            return jsonify({'restore': restore}), 200

        # Get current restore
        restore = self._restore.get(restore_id=request.args['id'])

        # Check if restore exists
        if len(restore) == 0:
            return jsonify({'message': 'This restore does not exist'}), 400
        restore = restore[0]

        # Check restore authority
        if restore['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Parse selected
        if restore['selected']:
            restore['selected'] = [{'file': i.split('|')[0], 'size': int(i.split('|')[1])} for i in restore['selected'].split('\n')]

        if restore['progress']:
            raw = restore['progress'].split(' ')
            restore['progress'] = {"value": raw[0], "transferred": raw[1], "rate": raw[2], "elapsed": raw[3]}
            restore['progress']['eta'] = raw[4][3:] if len(raw) == 5 else None

        # Return data
        return jsonify({'restore': restore}), 200

    def post(self, user, data):
        # Get server details
        server = self._servers.get(user_id=user['id'], group_id=user['group_id'], server_id=data['server'])
        if len(server) == 0:
            return jsonify({"message": 'This server does not exist.'}), 400
        server = server[0]

        # Generate uuid
        uri = str(uuid.uuid4())

        # Make restore folder
        base_path = json.loads(self._settings.get(setting_name='FILES'))['local']['path'] + '/restore/'
        if not os.path.exists(os.path.join(base_path, uri)):
            os.makedirs(os.path.join(base_path, uri))

        # Method: file
        if data['mode'] == 'file':
            if 'source' not in request.files or request.files['source'].filename == '':
                return jsonify({"message": 'No file was uploaded'}), 400
            file = request.files['source']
            if not self.__allowed_file(file.filename):
                return jsonify({"message": 'The file extension is not valid.'}), 400

            # Store file
            file.save(os.path.join(base_path, uri, secure_filename(file.filename)))

            # Build file metadata
            source = file.filename
            size = os.path.getsize(os.path.join(base_path, uri, secure_filename(file.filename)))
            selected = ''

        elif data['mode'] == 'url':
            source = data['source']
            size = self._scan_app.metadata(data)['size']
            selected = '\n'.join([f"{i['file']}|{i['size']}" for i in data['selected']])

        elif data['mode'] == 'cloud':
            # Retrieve cloud details
            cloud = self._cloud.get(user_id=user['id'], group_id=user['group_id'], cloud_id=data['cloud']['id'])
            if len(cloud) == 0:
                return jsonify({'message': 'The provided cloud does not exist in your inventory.'}), 400
            data['access_key'] = cloud[0]['access_key']
            data['secret_key'] = cloud[0]['secret_key']
            # Init values
            source = data['source']
            size = self._scan_app.metadata(data)['size']
            selected = '\n'.join([f"{i['file']}|{i['size']}" for i in data['selected']])
            details = {"cloud":  data['cloud'], "bucket": data['bucket'],  "object": data['object']}

        # Insert new restore to DB
        item = {
            'mode': data['mode'],
            'details': json.dumps(details) if 'cloud' in data else None,
            'source': source,
            'selected': None if len(selected) == 0 else selected,
            'size': size,
            'server_id': data['server'],
            'database': data['database'],
            'uri': uri
        }
        item['id'] = self._restore.post(user, item)

        # Parse selected for import process
        item['selected'] = ' '.join([i['file'] for i in data['selected']]) if selected else ''

        # Add Cloud credentials to item
        if item['mode'] == 'cloud':
            item['access_key'] = cloud[0]['access_key']
            item['secret_key'] = cloud[0]['secret_key']
            item['bucket'] = data['bucket']

        # Start import process
        self._restore_app.start(user, item, server, base_path)

        # Return tracking identifier
        return jsonify({'id': item['id']}), 200

    def delete(self, user, data):
        for item in data:
            self._restore.delete(user, item)
        return jsonify({'message': 'Selected restores deleted successfully'}), 200

    def stop(self, user, data):
        # Check params
        if 'id' not in data:
            return jsonify({'message': 'id parameter is required'}), 400

        # Get current restore
        restore = self._restore.get(restore_id=data['id'])

        # Check if restore exists
        if len(restore) == 0:
            return jsonify({'message': 'This restore does not exist.'}), 400
        restore = restore[0]

        # Check user authority
        if restore['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Check if the execution is in progress
        if restore['status'] != 'IN PROGRESS':
            return jsonify({'message': 'The execution has already finished.'}), 400

        # Stop the execution
        try:
            self._restore.update_status(user, data['id'], 'STOPPED')
            self._restore_app.stop(restore['pid'])
        except Exception:
            pass
        return jsonify({'message': 'Execution successfully stopped.'}), 200

    def get_scan(self, user, id):
        scan = self._scans.get(user_id=user['id'], scan_id=id)
        if len(scan) == 0:
            return jsonify({'message': 'This scan does not exist.'}), 400

        # Update 'readed' value
        self._scans.put_readed(scan[0]['id'])

        # Parse progress
        progress = scan[0]['progress']
        if progress:
            raw = progress.split(' ')
            progress = {"value": raw[0], "transferred": raw[1], "rate": raw[2], "elapsed": raw[3]}
            progress['eta'] = raw[4][3:] if len(raw) == 5 else None

        # Parse data
        data = scan[0]['data']
        if data:
            data = [{'file': i.split('|')[0][i.split('|')[0].find('/')+1:], 'size': int(i.split('|')[1])} for i in data.split('\n') if len(i.split('|')[0][i.split('|')[0].find('/')+1:]) > 0]

        # Parse error
        error = scan[0]['error']

        return { "id": scan[0]['id'], "status": scan[0]['status'], "progress": progress, "data": data, "error": error}

    def post_scan(self, user, data):
        # Retrieve cloud details
        if 'cloud_id' in data:
            cloud = self._cloud.get(user_id=user['id'], group_id=user['group_id'], cloud_id=data['cloud_id'])
            if len(cloud) == 0:
                return jsonify({'message': 'The provided cloud does not exist in your inventory.'}), 400
            data['access_key'] = cloud[0]['access_key']
            data['secret_key'] = cloud[0]['secret_key']

        # Validate source + Retrieve filesize
        data['metadata'] = self._scan_app.metadata(data)
        
        # Detect if the file is not compressed
        compress_formats = ('.tar','.tar.gz','tar.bz2')
        if not data['source'].endswith(compress_formats) and \
            ('disposition' not in data['metadata'] or \
           ('disposition' in data['metadata'] and not data['metadata']['disposition'].endswith(compress_formats))):
            return {'size': data['metadata']['size']}

        # - START SCAN - #
        # Generate uuid
        data['uri'] = str(uuid.uuid4())

        # Register the new scan
        data['id'] = self._scans.post(user, data)

        # Make scan folder
        base_path = json.loads(self._settings.get(setting_name='FILES'))['local']['path'] + '/scan/'
        if not os.path.exists(os.path.join(base_path, data['uri'])):
            os.makedirs(os.path.join(base_path, data['uri']))

        # Start new scan (threaded)
        self._scan_app.start(data, base_path)

        # Return tracking metadata
        return {'id': data['id'], 'size': data['metadata']['size']}

    def stop_scan(self, user, data):
        # Check params
        if 'id' not in data:
            return jsonify({'message': 'id parameter is required'}), 400

        # Get current scan
        scan = self._scans.get(user_id=user['id'], scan_id=data['id'])

        # Check if restore exists
        if len(scan) == 0:
            return jsonify({'message': 'This scan does not exist.'}), 400
        scan = scan[0]

        # Check user authority
        if scan['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Check if the scan is in progress
        if scan['status'] != 'IN PROGRESS':
            return jsonify({'message': 'The scan has already finished.'}), 400

        # Stop the scan
        try:
            self._scans.put_status(data['id'], 'STOPPED')
            self._scan_app.stop(scan['pid'])
        except Exception:
            pass
        return jsonify({'message': 'Scan successfully stopped.'}), 200

    def get_s3_buckets(self, user):
        # Get Cloud Key
        cloud = self._cloud.get(user_id=user['id'], group_id=user['group_id'], cloud_id=request.args['key'])
        if len(cloud) == 0:
            return jsonify({'message': 'The provided cloud does not exist in your inventory.'}), 400
        cloud = cloud[0]

        # Init S3 Client
        client = boto3.client('s3', aws_access_key_id=cloud['access_key'], aws_secret_access_key=cloud['secret_key'])

        # List all buckets
        try:
            response = client.list_buckets()
            buckets = [{'name': i['Name'], 'date': i['CreationDate']} for i in response['Buckets']]
            # Get buckets region
            for idx, bucket in enumerate(buckets):
                buckets[idx]['region'] = client.head_bucket(Bucket=bucket['name'])['ResponseMetadata']['HTTPHeaders']['x-amz-bucket-region']
            return jsonify({'buckets': buckets}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 400

    def get_s3_objects(self, user):
        # Get Cloud Key
        cloud = self._cloud.get(user_id=user['id'], group_id=user['group_id'], cloud_id=request.args['key'])
        if len(cloud) == 0:
            return jsonify({'message': 'The provided cloud does not exist in your inventory.'}), 400
        cloud = cloud[0]

        # Init S3 Client
        client = boto3.client('s3', aws_access_key_id=cloud['access_key'], aws_secret_access_key=cloud['secret_key'])

        # List objects
        try:
            response = client.list_objects_v2(
                Bucket=request.args['bucket'],
                Delimiter='/',
                Prefix=request.args['prefix'],
                # ContinuationToken=request.args['token'],
            )
            items = []
            # Build folders
            if 'CommonPrefixes' in response:
                items += [{'key': i['Prefix'], 'name': i['Prefix'][len(request.args['prefix']) - len(request.args['search']):]} for i in response['CommonPrefixes']]
            # Build objects
            if 'Contents' in response:
                items += [{'key': i['Key'], 'name': i['Key'][len(request.args['prefix']) - len(request.args['search']):], 'last_modified': i['LastModified'], 'size': i['Size'], 'storage_class': i['StorageClass']} for i in response['Contents'] if len(i['Key'][len(request.args['prefix']) - len(request.args['search']):]) > 0]
            # Sort items
            items = sorted(items, key=lambda k: k['name'])
            return jsonify({'objects': items}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 400

    def __allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'sql','tar','gz'}
