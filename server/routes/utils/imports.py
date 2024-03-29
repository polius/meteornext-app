from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user
from werkzeug.utils import secure_filename
import os
import sys
import uuid
import json
import shutil
import boto3
from datetime import datetime

import models.admin.users
import models.admin.groups
import models.utils.imports
import models.utils.scans
import models.admin.settings
import models.inventory.servers
import models.inventory.regions
import models.inventory.cloud
import apps.imports.imports
import apps.imports.scan

class Imports:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._imports = models.utils.imports.Imports(sql, self._license)
        self._scans = models.utils.scans.Scans(sql)
        self._settings = models.admin.settings.Settings(sql, self._license)
        self._servers = models.inventory.servers.Servers(sql, self._license)
        self._regions = models.inventory.regions.Regions(sql)
        self._cloud = models.inventory.cloud.Cloud(sql)
        # Init core
        self._import_app = apps.imports.imports.Imports(sql)
        self._scan_app = apps.imports.scan.Scan(sql)
        # Retrieve base path
        self._bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self._base_path = os.path.realpath(os.path.dirname(sys.executable)) if self._bin else os.path.realpath(os.path.dirname(sys.argv[0]))

    def blueprint(self):
        # Init blueprint
        imports_blueprint = Blueprint('imports', __name__, template_folder='imports')

        @imports_blueprint.route('/utils/imports', methods=['GET','POST','DELETE'])
        @jwt_required()
        def imports_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

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

        @imports_blueprint.route('/utils/imports/check', methods=['GET'])
        @jwt_required()
        def imports_check_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check file size limit
            group = self._groups.get(group_id=user['group_id'])[0]
            if group['utils_limit'] is not None and int(request.args['size']) >= group['utils_limit'] * 1024**2:
                return jsonify({'message': f"The file size exceeds the maximum allowed size ({group['utils_limit']} MB)"}), 400

            # Return if there's free space left to upload a file
            return jsonify({'check': shutil.disk_usage("/").free >= int(request.args['size'])}), 200

        @imports_blueprint.route('/utils/imports/stop', methods=['POST'])
        @jwt_required()
        def imports_stop_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Stop import process
            return self.stop(user)

        @imports_blueprint.route('/utils/imports/scan', methods=['POST','GET'])
        @jwt_required()
        def imports_scan_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

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
                # Return scanned file
                try:
                    scan = self.get_scan(user, request.args['id'])
                    return jsonify(scan), 200
                except Exception as e:
                    return jsonify({'message': str(e)}), 400
            elif request.method == 'POST':
                # Register a new scan
                try:
                    scan = self.post_scan(user)
                    return jsonify(scan), 200
                except Exception as e:
                    return jsonify({'message': str(e)}), 400

        @imports_blueprint.route('/utils/imports/scan/stop', methods=['POST'])
        @jwt_required()
        def imports_scan_stop_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Stop Scan
            return self.stop_scan(user)

        @imports_blueprint.route('/utils/imports/s3/buckets', methods=['GET'])
        @jwt_required()
        def imports_s3_buckets_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Buckets
            return self.get_s3_buckets(user)

        @imports_blueprint.route('/utils/imports/s3/objects', methods=['GET'])
        @jwt_required()
        def imports_s3_objects_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Objects
            return self.get_s3_objects(user)

        return imports_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        if 'uri' not in request.args:
            imports = self._imports.get(user_id=user['id'])
            return jsonify({'imports': imports}), 200

        # Get current import
        imp = self._imports.get(import_uri=request.args['uri'])

        # Check if import exists
        if len(imp) == 0:
            return jsonify({'message': 'This import does not exist'}), 400
        imp = imp[0]

        # Check import authority
        if imp['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Parse selected
        if imp['selected']:
            imp['selected'] = [{'file': i.split('|')[0], 'size': int(i.split('|')[1])} for i in imp['selected'].split('\n')]

        # Parse upload
        imp['upload'] = json.loads(imp['upload']) if imp['upload'] else None

        # Parse progress
        if imp['progress']:
            raw = imp['progress'].split(' ')
            imp['progress'] = {"value": '0%', "transferred": '0B', "rate": '0B/s', "elapsed": '0:00:00', "eta": None}
            if len(raw) == 3:
                imp['progress'] = {"value": '0%', "transferred": raw[0], "rate": raw[1], "elapsed": raw[2], "eta": None}
            elif len(raw) == 4:
                imp['progress'] = {"value": raw[0], "transferred": raw[1], "rate": raw[2], "elapsed": raw[3], "eta": None}
            elif len(raw) == 5:
                imp['progress'] = {"value": raw[0], "transferred": raw[1], "rate": raw[2], "elapsed": raw[3], "eta": raw[4][3:]}
        # Return data
        return jsonify({'import': imp}), 200

    def post(self, user):
        # Get data
        data = request.get_json() if request.is_json else request.form

        # Get group details
        group = self._groups.get(group_id=user['group_id'])[0]

        # Check Coins
        if (user['coins'] - group['utils_coins']) < 0:
            return jsonify({'message': 'Insufficient Coins'}), 400

        # Get server details
        server = self._servers.get(user_id=user['id'], group_id=user['group_id'], server_id=data['server'])
        if len(server) == 0:
            return jsonify({"message": 'This server does not exist in your inventory.'}), 400
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

        # Make import folder
        if not os.path.exists(f"{self._base_path}/files/imports/{uri}"):
            os.makedirs(f"{self._base_path}/files/imports/{uri}")

        # Method: file
        if data['mode'] == 'file':
            # Check file size limit
            if group['utils_limit'] is not None and int(data['size']) >= group['utils_limit'] * 1024**2:
                return jsonify({'message': f"The upload file exceeds the maximum allowed size ({group['utils_limit']} MB)"}), 400

            # Check file constraints
            if 'source' not in request.files or request.files['source'].filename == '':
                return jsonify({"message": 'No file was uploaded'}), 400
            file = request.files['source']
            if not self.__allowed_file(file.filename):
                return jsonify({"message": 'The file extension is not valid.'}), 400

            # Store file
            file.save(f"{self._base_path}/files/imports/{uri}/{secure_filename(file.filename)}")

            # Build file metadata
            source = secure_filename(file.filename)
            format = '.tar' if source.endswith('.tar') else '.tar.gz' if source.endswith('.tar.gz') else '.gz' if source.endswith('.gz') else '.sql'
            size = os.path.getsize(f"{self._base_path}/files/imports/{uri}/{secure_filename(file.filename)}")
            selected = ''
            url = data['url']
            create_database = json.loads(data['createDatabase'])
            recreate_database = json.loads(data['recreateDatabase'])

        elif data['mode'] == 'url':
            source = data['source']
            format = data['format']
            size = self._scan_app.metadata(data)['size']
            selected = '\n'.join([f"{i['file']}|{i['size']}" for i in data['selected']])
            url = data['url']
            create_database = data['createDatabase']
            recreate_database = data['recreateDatabase']

        elif data['mode'] == 'cloud':
            # Retrieve cloud details
            cloud = self._cloud.get(user_id=user['id'], group_id=user['group_id'], cloud_id=data['cloud']['id'])
            if len(cloud) == 0:
                return jsonify({'message': 'The provided cloud does not exist in your inventory.'}), 400
            cloud = cloud[0]
            # Init values
            data['access_key'] = cloud['access_key']
            data['secret_key'] = cloud['secret_key']
            source = data['source']
            format = '.tar' if source.endswith('.tar') else '.tar.gz' if source.endswith('.tar.gz') else '.gz' if source.endswith('.gz') else '.sql'
            size = self._scan_app.metadata(data)['size']
            selected = '\n'.join([f"{i['file']}|{i['size']}" for i in data['selected']])
            details = {"cloud": data['cloud'], "bucket": data['bucket'], "region": data['region'], "object": data['object']}
            url = data['url']
            create_database = data['createDatabase']
            recreate_database = data['recreateDatabase']

        # Consume Coins
        self._users.consume_coins(user, group['utils_coins'])
        coins = user['coins'] - group['utils_coins']

        # Create new import
        item = {
            'username': user['username'],
            'mode': data['mode'],
            'details': json.dumps(details) if 'cloud' in data else None,
            'source': source,
            'format': format,
            'selected': None if len(selected) == 0 else selected,
            'size': size,
            'server_id': data['server'],
            'server_name': server['name'],
            'region_name': region['name'],
            'database': data['database'].strip(),
            'create_database': create_database,
            'recreate_database': recreate_database,
            'status': 'QUEUED',
            'created': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            'uri': uri,
            'upload': json.dumps("{'value': 0, 'transferred': 0}") if region['ssh_tunnel'] and data['mode'] == 'file' else None,
            'slack_enabled': group['utils_slack_enabled'],
            'slack_url': group['utils_slack_url'],
            'url': url
        }
        self._imports.post(user, item)

        # Return tracking identifier
        return jsonify({'uri': item['uri'], 'coins': coins}), 200

    def delete(self, user):
        data = request.get_json()
        for item in data:
            self._imports.delete(user, item)
        return jsonify({'message': 'Selected imports deleted'}), 200

    def stop(self, user):
        # Get data
        data = request.get_json()

        # Check params
        if 'uri' not in data:
            return jsonify({'message': 'uri parameter is required'}), 400

        # Get current import
        imp = self._imports.get(import_uri=data['uri'])

        # Check if import exists
        if len(imp) == 0:
            return jsonify({'message': 'This import does not exist'}), 400
        imp = imp[0]

        # Check user authority
        if imp['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Check if the execution is in progress
        if imp['status'] in ['SUCCESS','FAILED','STOPPED']:
            return jsonify({'message': 'The execution has already finished'}), 400

        # Stop the execution
        self._imports.stop(user, data['uri'])
        return jsonify({'message': 'Stopping execution...'}), 200

    def get_scan(self, user, id):
        scan = self._scans.get(user_id=user['id'], scan_id=id)
        if len(scan) == 0:
            return jsonify({'message': 'This scan does not exist'}), 400

        # Update 'readed' value
        self._scans.put_readed(scan[0]['id'])

        # Parse progress
        progress = scan[0]['progress']
        if progress and not scan[0]['error']:
            raw = progress.split(' ')
            progress = {"value": raw[0], "transferred": raw[1], "rate": raw[2], "elapsed": raw[3]}
            progress['eta'] = raw[4][3:] if len(raw) == 5 else None

        # Parse data
        data = scan[0]['data']
        if data:
            data = [{'file': i.split('|')[0], 'size': int(i.split('|')[1])} for i in data.split('\n') if int(i.split('|')[1]) > 0]

        # Parse error
        error = scan[0]['error']

        return { "id": scan[0]['id'], "status": scan[0]['status'], "progress": progress, "data": data, "error": error}

    def post_scan(self, user):
        # Get data
        data = request.get_json()

        # Retrieve cloud details
        if 'cloud_id' in data:
            cloud = self._cloud.get(user_id=user['id'], group_id=user['group_id'], cloud_id=data['cloud_id'])
            if len(cloud) == 0:
                return jsonify({'message': 'The provided cloud does not exist in your inventory'}), 400
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
        if not os.path.exists(f"{self._base_path}/files/scans/{data['uri']}"):
            os.makedirs(f"{self._base_path}/files/scans/{data['uri']}")

        # Start new scan (threaded)
        self._scan_app.start(data, f"{self._base_path}/files/scans/{data['uri']}")

        # Return tracking metadata
        return {'id': data['id'], 'size': data['metadata']['size']}

    def stop_scan(self, user):
        # Get data
        data = request.get_json()

        # Check params
        if 'id' not in data:
            return jsonify({'message': 'id parameter is required'}), 400

        # Get current scan
        scan = self._scans.get(user_id=user['id'], scan_id=data['id'])

        # Check if import exists
        if len(scan) == 0:
            return jsonify({'message': 'This scan does not exist'}), 400
        scan = scan[0]

        # Check user authority
        if scan['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

        # Check if the scan is in progress
        if scan['status'] != 'IN PROGRESS':
            return jsonify({'message': 'The scan has already finished'}), 400

        # Stop the scan
        self._scans.put_status(data['id'], 'STOPPED')
        self._scan_app.stop(scan['pid'])
        return jsonify({'message': 'Scan stopped'}), 200

    def get_s3_buckets(self, user):
        # Get Cloud Key
        cloud = self._cloud.get(user_id=user['id'], group_id=user['group_id'], cloud_id=request.args['key'])
        if len(cloud) == 0:
            return jsonify({'message': 'The provided cloud does not exist in your inventory'}), 400
        cloud = cloud[0]

        # Init S3 Client
        client = boto3.client('s3', aws_access_key_id=cloud['access_key'], aws_secret_access_key=cloud['secret_key'])

        # List all buckets
        try:
            buckets = []
            exception = None
            if cloud['buckets']:
                for bucket in cloud['buckets'].split(','):
                    try:
                        location = client.get_bucket_location(Bucket=bucket)
                        buckets.append({'name': bucket, 'region': location['LocationConstraint']})
                    except Exception as e:
                        exception = e
                if len(buckets) == 0 and exception:
                    raise exception
            return jsonify({'buckets': buckets}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 400

    def get_s3_objects(self, user):
        # Get Cloud Key
        cloud = self._cloud.get(user_id=user['id'], group_id=user['group_id'], cloud_id=request.args['key'])
        if len(cloud) == 0:
            return jsonify({'message': 'The provided cloud does not exist in your inventory'}), 400
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
                items += [{'key': i['Prefix'], 'name': i['Prefix'][len(request.args['path']):]} for i in response['CommonPrefixes']]
            # Build objects
            if 'Contents' in response:
                items += [{'key': i['Key'], 'name': i['Key'][len(request.args['path']):], 'last_modified': i['LastModified'], 'size': i['Size'], 'storage_class': i['StorageClass']} for i in response['Contents'] if len(i['Key'][len(request.args['path']):]) > 0]
            # Sort items
            items = sorted(items, key=lambda k: k['name'])
            return jsonify({'objects': items}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 400

    def __allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'sql','tar','gz'}
