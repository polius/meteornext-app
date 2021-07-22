from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from werkzeug.utils import secure_filename
import os
import json

import models.admin.users
import models.utils.restore
import models.admin.settings

class Restore:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._restore = models.utils.restore.Restore(sql)
        self._settings = models.admin.settings.Settings(sql)

    def blueprint(self):
        # Init blueprint
        restore_blueprint = Blueprint('restore', __name__, template_folder='restore')

        @restore_blueprint.route('/restore', methods=['GET','POST','PUT'])
        @jwt_required()
        def restores_method():
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
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user, data)
            elif request.method == 'PUT':
                return self.put(user, data)

        @restore_blueprint.route('/restore/servers', methods=['GET'])
        @jwt_required()
        def restores_servers_method():
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
        if request.form and request.form['mode'] == 'file':
            file = request.files['file']
            if 'file' not in request.files or file.filename == '':
                return jsonify({"message": 'No file was uploaded'}), 400
            if not self.__allowed_file(file.filename):
                return jsonify({"message": 'The file extension is not valid.'}), 400

            # Store file
            files_path = json.loads(self._settings.get(setting_name='FILES'))['local']['path'] + '/restore/'
            if not os.path.exists(files_path):
                os.makedirs(files_path)
            file.save(os.path.join(files_path, secure_filename(file.filename)))

            # Insert new restore to DB
            restore_id = self._restore.post(user, request.form)
            return jsonify({'id': restore_id}), 200

        return jsonify({'message': 'OK'}), 200

    def put(self, user, data):
        # Edit Metadata
        if 'name' in data.keys():
            self._restore.put_name(user, data)
            return jsonify({'message': 'Restore edited successfully'}), 200

    def __allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'sql','gz'}
