from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from werkzeug.utils import secure_filename
import os
import uuid
import json
import shutil
import signal
import subprocess

import models.admin.users
import models.utils.restore
import models.admin.settings
import models.inventory.servers
import apps.restore.restore

class Restore:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._restore = models.utils.restore.Restore(sql)
        self._settings = models.admin.settings.Settings(sql)
        self._servers = models.inventory.servers.Servers(sql)
        # Init core
        self._core = apps.restore.restore.Restore(sql)

    def blueprint(self):
        # Init blueprint
        restore_blueprint = Blueprint('restore', __name__, template_folder='restore')

        @restore_blueprint.route('/restore', methods=['GET','POST','DELETE'])
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

        @restore_blueprint.route('/restore/check', methods=['GET'])
        @jwt_required()
        def restore_space_method():
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

        @restore_blueprint.route('/restore/servers', methods=['GET'])
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

        @restore_blueprint.route('/restore/stop', methods=['POST'])
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

        @restore_blueprint.route('/restore/inspect', methods=['GET'])
        @jwt_required()
        def restore_inspect_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['utils_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Return inspected file
            try:
                inspect = self.inspect(request.args['url'])
                return jsonify({'inspect': inspect}), 200
            except Exception as e:
                return jsonify({'message': str(e)}), 400

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
        else:
            restore = restore[0]

        # Check restore authority
        if restore['user_id'] != user['id'] and not user['admin']:
            return jsonify({'message': 'Insufficient Privileges'}), 400

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
            file = request.files['file']
            if 'file' not in request.files or file.filename == '':
                return jsonify({"message": 'No file was uploaded'}), 400
            if not self.__allowed_file(file.filename):
                return jsonify({"message": 'The file extension is not valid.'}), 400

            # Store file            
            file.save(os.path.join(base_path, uri, secure_filename(file.filename)))
            file = file.filename

            # Get file size
            size = os.path.getsize(os.path.join(base_path, uri, secure_filename(file)))
            selected = None
        
        elif data['mode'] == 'url':
            try:
                inspect = self.inspect(data['url'])
            except Exception as e:
                return jsonify({'message': str(e)}), 400
            file = data['url']
            selected = [i for i in inspect['items'] if i['file'] in data['selected']] if 'selected' in data and len(data['selected']) > 0 else None
            size = inspect['size']
            if len(selected) != len(data['selected']):
                return jsonify({'message': 'The selected file(s) do not match with the provided url.'}), 400
            selected = json.dumps(selected)

        # Insert new restore to DB
        item = {
            'mode': data['mode'],
            'file': file,
            'selected': selected,
            'size': size,
            'server_id': data['server'],
            'database': data['database'],
            'uri': uri
        }
        item['id'] = self._restore.post(user, item)

        # Start import process
        self._core.start(user, item, server, base_path)

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
            os.kill(restore['pid'], signal.SIGINT)
            self._restore.update_status(user, data['id'], 'STOPPED')
            return jsonify({'message': 'The execution has successfully stopped.'}), 200
        except Exception:
            return jsonify({'message': 'The execution has already finished.'}), 400

    def inspect(self, url):
        inspect = { "file": url, "size": None, "items": [] }
        # File Size
        p = subprocess.run(f"curl -sSI '{url}' | grep -i Content-Length | awk '{{print $2}}'", shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if len(p.stdout) == 0:
            raise Exception("This URL is not valid")
        inspect['size'] = int(p.stdout.strip())

        # If file is a .tar or .tar.gz, get the files
        # https://meteor2.io/restore.tar
        # https://meteor2.io/restore.tar.gz
        # http://file.fyicenter.com/a/sample.tar
        # https://dev-files.blender.org/file/download/bwdp5reejwpkuh5i2oak/PHID-FILE-nui3bpuan4wdvd7yzjrs/sample.tar.gz
        p = None
        if url.endswith('.tar.gz'):
            p = subprocess.run(f"curl -sS '{url}' | gunzip -c | tar -tv | awk '{{print $6\"|\"$3}}'", shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif url.endswith('.tar'):
            p = subprocess.run(f"curl -sS '{url}' | tar -tv | awk '{{print $6\"|\"$3}}'", shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p:
            if len(p.stderr) > 0:
                raise Exception(p.stderr.strip())
            inspect['items'] = [{'file': i.split('|')[0][i.split('|')[0].find('/')+1:], 'size': int(i.split('|')[1])} for i in p.stdout.strip().split('\n')]
        return inspect

    def __allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'sql','tar','gz'}
