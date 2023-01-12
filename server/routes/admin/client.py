import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.admin.client
import routes.admin.settings

class Client:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._client = models.admin.client.Client(sql, self._license)
        # Init routes
        self._settings = routes.admin.settings.Settings(self._license, sql)

    def blueprint(self):
        # Init blueprint
        admin_client_blueprint = Blueprint('admin_client', __name__, template_folder='admin_client')

        @admin_client_blueprint.route('/admin/client/queries', methods=['GET'])
        @jwt_required()
        def admin_client_queries_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Parse arguments
            try:
                args = self.parse_args()
            except Exception:
                return jsonify({'message': 'Invalid parameters'}), 400

            # Return Client Queries
            dfilter = args['filter'] if 'filter' in args else None
            dsort = args['sort'] if 'sort' in args else None
            queries = self._client.get_queries(dfilter, dsort)
            users_list = self._client.get_users_list()
            servers_list = self._client.get_servers_list()
            return jsonify({'queries': queries, 'users_list': users_list, 'servers_list': servers_list}), 200

        @admin_client_blueprint.route('/admin/client/servers', methods=['GET','POST','DELETE'])
        @jwt_required()
        def admin_client_servers_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": "The license is not valid"}), 401

            # Check Settings - Security (Administration URL)
            if not self._settings.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                # Parse arguments
                try:
                    args = self.parse_args()
                except Exception:
                    return jsonify({'message': 'Invalid parameters'}), 400
                # Return Client Servers
                dfilter = args['filter'] if 'filter' in args else None
                dsort = args['sort'] if 'sort' in args else None
                servers = self._client.get_servers(dfilter, dsort)
                users_list = self._client.get_users_list()
                servers_list = self._client.get_servers_list()
                return jsonify({'servers': servers, 'users_list': users_list, 'servers_list': servers_list}), 200
            elif request.method == 'POST':
                # Attach Servers
                self._client.attach_servers(request.get_json())
                return jsonify({'message': 'Server(s) attached'}), 200
            elif request.method == 'DELETE':
                # Detach Servers
                self._client.detach_servers(json.loads(request.args['servers']))
                return jsonify({'message': 'Server(s) detached'}), 200

        return admin_client_blueprint

    ####################
    # Internal Methods #
    ####################
    def parse_args(self):
        args = {}
        for k,v in request.args.to_dict().items():
            if '[' in k:
                if not k[:k.find('[')] in args:
                    args[k[:k.find('[')]] = {}
                args[k[:k.find('[')]][k[k.find('[')+1:-1]] = v
            else:
                args[k] = v
        return args
