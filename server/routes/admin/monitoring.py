import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.admin.monitoring
import routes.admin.settings

class Monitoring:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._monitoring = models.admin.monitoring.Monitoring(sql, self._license)
        # Init routes
        self._settings = routes.admin.settings.Settings(self._license, sql)

    def blueprint(self):
        # Init blueprint
        admin_monitoring_blueprint = Blueprint('admin_monitoring', __name__, template_folder='admin_monitoring')

        @admin_monitoring_blueprint.route('/admin/monitoring/servers', methods=['GET','POST','DELETE'])
        @jwt_required()
        def admin_monitoring_servers_method():
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
                return self.get()
            elif request.method == 'POST':
                return self.post()
            elif request.method == 'DELETE':
                return self.delete()

        return admin_monitoring_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        # Parse arguments
        args = {}
        try:
            for k,v in request.args.to_dict().items():
                if '[' in k:
                    if not k[:k.find('[')] in args:
                        args[k[:k.find('[')]] = {}
                    args[k[:k.find('[')]][k[k.find('[')+1:-1]] = v
                else:
                    args[k] = v
        except Exception:
            return jsonify({'message': 'Invalid parameters'}), 400

        # Return Monitoring Servers
        mfilter = args['filter'] if 'filter' in args else None
        msort = args['sort'] if 'sort' in args else None
        servers = self._monitoring.get_servers(mfilter, msort)
        users_list = self._monitoring.get_users_list()
        servers_list = self._monitoring.get_servers_list()
        return jsonify({'servers': servers, 'users_list': users_list, 'servers_list': servers_list }), 200

    def post(self):
        # Attach Servers
        self._monitoring.attach_servers(request.get_json())
        return jsonify({'message': 'Server(s) attached'}), 200

    def delete(self):
        # Detach Servers
        self._monitoring.detach_servers(json.loads(request.args['servers']))
        return jsonify({'message': 'Server(s) detached'}), 200
