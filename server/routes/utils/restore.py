from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from werkzeug.utils import secure_filename
import os

import models.admin.users
import models.utils.restore

class Restore:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._restore = models.utils.restore.Restore(sql)

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
        restore = self._restore.get(user_id=user['id'])
        return jsonify({'restore': restore}), 200

    def post(self, user, data):
        # Get uploaded file
        file = request.files['file']
        if 'file' not in request.files or file.filename == '':
            return jsonify({"message": 'No file was uploaded'}), 400

        if not self.__allowed_file(file.filename):
            return jsonify({"message": 'The file extension is not valid'}), 400

        filename = secure_filename(file.filename)
        file.save(os.path.join('???', filename))

    def put(self, user, data):
        # Edit Metadata
        if 'name' in data.keys():
            self._restore.put_name(user, data)
            return jsonify({'message': 'Restore edited successfully'}), 200

    def __allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'sql'}