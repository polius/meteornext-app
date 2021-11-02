import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.admin.client
import routes.admin.settings

class Client:
    def __init__(self, app, sql, license):
        self._app = app
        self._sql = sql
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._client = models.admin.client.Client(sql, license)
        # Init routes
        self._settings = routes.admin.settings.Settings(app, sql, license)

    def blueprint(self):
        # Init blueprint
        admin_client_blueprint = Blueprint('admin_client', __name__, template_folder='admin_client')

        @admin_client_blueprint.route('/admin/client/queries', methods=['GET'])
        @jwt_required()
        def admin_client_queries_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Return Client Queries
            dfilter = json.loads(request.args['filter']) if 'filter' in request.args else None
            dsort = json.loads(request.args['sort']) if 'sort' in request.args else None
            queries = self._client.get_queries(dfilter, dsort)
            users_list = self._client.get_users_list()
            servers_list = self._client.get_servers_list()
            return jsonify({'queries': queries, 'users_list': users_list, 'servers_list': servers_list}), 200

        @admin_client_blueprint.route('/admin/client/servers', methods=['GET','POST','DELETE'])
        @jwt_required()
        def admin_client_servers_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                # Return Client Servers
                dfilter = json.loads(request.args['filter']) if 'filter' in request.args else None
                dsort = json.loads(request.args['sort']) if 'sort' in request.args else None
                servers = self._client.get_servers(dfilter, dsort)
                users_list = self._client.get_users_list()
                servers_list = self._client.get_servers_list()
                return jsonify({'servers': servers, 'users_list': users_list, 'servers_list': servers_list}), 200
            elif request.method == 'POST':
                # Attach Servers
                self._client.attach_servers(request.get_json())
                return jsonify({'message': 'Server(s) Successfully Attached'}), 200
            elif request.method == 'DELETE':
                # Detach Servers
                self._client.detach_servers(json.loads(request.args['servers']))
                return jsonify({'message': 'Server(s) Successfully Detached'}), 200

        return admin_client_blueprint
