import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.monitoring.monitoring
import models.monitoring.monitoring_settings
import models.monitoring.monitoring_queries

class Queries:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._monitoring = models.monitoring.monitoring.Monitoring(sql, self._license)
        self._monitoring_settings = models.monitoring.monitoring_settings.Monitoring_Settings(sql)
        self._monitoring_queries = models.monitoring.monitoring_queries.Monitoring_Queries(sql, self._license)

    def blueprint(self):
        # Init blueprint
        monitoring_queries_blueprint = Blueprint('monitoring_queries', __name__, template_folder='monitoring_queries')

        @monitoring_queries_blueprint.route('/monitoring/queries', methods=['GET','PUT'])
        @jwt_required()
        def monitoring_queries_method():
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
            if user['disabled'] or not user['monitoring_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'PUT':
                return self.put(user)

        return monitoring_queries_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
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

        # Get Queries
        mfilter = args['filter'] if 'filter' in args else None
        msort = args['sort'] if 'sort' in args else None
        if mfilter or msort:
            queries = self._monitoring_queries.get(user, mfilter, msort)
            return jsonify({'queries': queries}), 200

        # Do not apply filter & sort
        settings = self._monitoring_settings.get(user)
        servers = self._monitoring.get_queries(user)
        queries = self._monitoring_queries.get(user)
        return jsonify({'servers': servers, 'queries': queries, 'settings': settings}), 200

    def put(self, user):
        self._monitoring.put_queries(user, request.get_json())
        return jsonify({'message': 'Servers saved'}), 200
