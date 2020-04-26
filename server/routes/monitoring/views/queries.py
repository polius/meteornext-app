from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.monitoring.monitoring
import models.monitoring.monitoring_settings
import models.monitoring.monitoring_queries

class Queries:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._monitoring = models.monitoring.monitoring.Monitoring(sql)
        self._monitoring_settings = models.monitoring.monitoring_settings.Monitoring_Settings(sql)
        self._monitoring_queries = models.monitoring.monitoring_queries.Monitoring_Queries(sql)

    def blueprint(self):
        # Init blueprint
        monitoring_queries_blueprint = Blueprint('monitoring_queries', __name__, template_folder='monitoring_queries')

        @monitoring_queries_blueprint.route('/monitoring/queries', methods=['GET'])
        @jwt_required
        def monitoring_queries_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['monitoring_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get queries
            return self.get(user)

        @monitoring_queries_blueprint.route('/monitoring/queries/filter', methods=['GET'])
        @jwt_required
        def monitoring_queries_filter_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if not user['monitoring_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get queries
            return self.filter(user)

        return monitoring_queries_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        servers = self._monitoring.get_queries(user)
        queries = self._monitoring_queries.get(user)
        settings = self._monitoring_settings.get(user)

        return jsonify({'servers': servers, 'queries': queries, 'settings': settings}), 200

    def filter(self, user):
        data = request.args['filter'] if 'filter' in request.args else None
        queries = self._monitoring_queries.filter(user, data)
        return jsonify({'queries': queries}), 200