import os
import sys
import json
import bcrypt
import models.admin.users
import models.mysql
from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity)

import routes.login
import routes.profile
import routes.admin.settings
import routes.admin.groups
import routes.admin.users
import routes.admin.deployments
import routes.deployments.settings.environments
import routes.deployments.settings.regions
import routes.deployments.settings.servers
import routes.deployments.settings.auxiliary
import routes.deployments.settings.slack
import routes.deployments.deployments
import routes.deployments.views.basic
import routes.deployments.views.pro
import models.mysql
import models.admin.settings
from cron import Cron

class Setup:
    def __init__(self, app):
        self._app = app
        self._setup_file = "{}/server.conf".format(app.root_path) if sys.argv[0].endswith('.py') else "{}/server.conf".format(os.path.dirname(sys.executable))
        self._schema_file = "{}/models/schema.sql".format(app.root_path) if sys.argv[0].endswith('.py') else "{}/models/schema.sql".format(sys._MEIPASS)
        self._logs_folder = "{}/logs".format(app.root_path) if sys.argv[0].endswith('.py') else "{}/logs".format(os.path.dirname(sys.executable))

        try:
            with open(self._setup_file) as file_open:
                self._conf = json.load(file_open)
            sql = models.mysql.mysql()
            sql.connect(self._conf['sql']['hostname'], self._conf['sql']['username'], self._conf['sql']['password'], self._conf['sql']['database'])
            self.__register_blueprints(sql)

            # Start cron
            Cron(sql)

        except Exception:
            self._conf = {}

    def getBind(self):
        if 'bind' in self._conf:
            return self._conf['bind']
        else:
            return '0.0.0.0:5000'

    def blueprint(self):
        # Init blueprint
        setup_blueprint = Blueprint('setup', __name__, template_folder='setup')

        @setup_blueprint.route('/setup', methods=['GET'])
        def setup():
            if self.__setup_available():
                return jsonify({}), 200
            else:
                return jsonify({}), 401

        @setup_blueprint.route('/setup/1', methods=['POST'])
        def setup1():
            # Protect api call once is already configured
            if not self.__setup_available():
                return jsonify({}), 400

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400
            
            setup_json = request.get_json()

            # Part 1: Check SQL Credentials
            try:
                sql = models.mysql.mysql()
                sql.connect(setup_json['hostname'], setup_json['username'], setup_json['password'])
                exists = sql.check_db_exists(setup_json['database'])
                return jsonify({'message': 'Connection Successful', 'exists': exists}), 200
            except Exception as e:
                return jsonify({'message': str(e)}), 500

        @setup_blueprint.route('/setup/2', methods=['POST'])
        def setup2():
            # Protect api call once is already configured
            if not self.__setup_available():
                return jsonify({}), 400

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400
            
            setup_json = request.get_json()

            # Part 2: Build Meteor & Create User Admin Account
            sql = models.mysql.mysql()
            sql.connect(setup_json['sql']['hostname'], setup_json['sql']['username'], setup_json['sql']['password'])

            try:
                sql.execute('DROP DATABASE IF EXISTS {}'.format(setup_json['sql']['database']))
                sql.execute('CREATE DATABASE {}'.format(setup_json['sql']['database']))
                sql.select_database(setup_json['sql']['database'])
                with open(self._schema_file) as file_open:
                    queries = file_open.read().split(';')
                    for q in queries:
                        if q != '':
                            sql.execute(q)

                # Create user
                users = models.admin.users.Users(sql)
                user = {"username": setup_json['account']['username'], "password": setup_json['account']['password'], "email": "admin@admin.com", "coins": 100, "group": 'Administrator', "admin": 1}
                user['password'] = bcrypt.hashpw(user['password'].encode('utf8'), bcrypt.gensalt())
                users.post(user)

                # Init Logs Local Path
                settings = models.admin.settings.Settings(sql)
                setting = {"name": "LOGS", "value": '{{"amazon_s3":{{"enabled":false}},"local":{{"path":"{}"}}}}'.format(self._logs_folder)}
                settings.post(setting)

            except Exception as e:
                return jsonify({'message': str(e)}), 500

            # Write setup to the setup file
            self._conf = {
                "bind": "0.0.0.0:5000",
                "sql":
                {
                    "hostname": setup_json['sql']['hostname'],
                    "username": setup_json['sql']['username'],
                    "password": setup_json['sql']['password'],
                    "port": setup_json['sql']['port'],
                    "database": setup_json['sql']['database']
                }
            }
            with open(self._setup_file, 'w') as outfile:
                json.dump(self._conf, outfile)

            # Init blueprints
            self.__register_blueprints(sql)

            # Build return message
            return jsonify({'message': 'Setup Finished Successfully'}), 200

        return setup_blueprint

    ####################
    # Internal Methods #
    ####################
    def __setup_available(self):
        if os.path.exists(self._setup_file):
            with open(self._setup_file) as file_open:
                f = json.load(file_open)
                if f['sql']['hostname'] != '' or f['sql']['username'] != '' or f['sql']['password'] != '' or f['sql']['port'] != '' or f['sql']['database'] != '':
                    return False
        return True

    def __register_blueprints(self, sql):
        # Init all blueprints
        login = routes.login.Login(self._app, sql).blueprint()
        profile = routes.profile.Profile(self._app, sql).blueprint()
        settings = routes.admin.settings.Settings(self._app, self._conf, sql).blueprint()
        groups = routes.admin.groups.Groups(self._app, sql).blueprint()
        users = routes.admin.users.Users(self._app, sql).blueprint()
        admin_deployments = routes.admin.deployments.Deployments(self._app, sql).blueprint()
        environments = routes.deployments.settings.environments.Environments(self._app, sql).blueprint()
        regions = routes.deployments.settings.regions.Regions(self._app, sql).blueprint()
        servers = routes.deployments.settings.servers.Servers(self._app, sql).blueprint()
        auxiliary = routes.deployments.settings.auxiliary.Auxiliary(self._app, sql).blueprint()
        slack = routes.deployments.settings.slack.Slack(self._app, sql).blueprint()
        deployments = routes.deployments.deployments.Deployments(self._app, sql).blueprint()
        deployments_basic = routes.deployments.views.basic.Basic(self._app, sql).blueprint()
        deployments_pro = routes.deployments.views.pro.Pro(self._app, sql).blueprint()

        # Instantiate all routes
        self._app.register_blueprint(login)
        self._app.register_blueprint(profile)
        self._app.register_blueprint(settings)
        self._app.register_blueprint(groups)
        self._app.register_blueprint(users)
        self._app.register_blueprint(admin_deployments)
        self._app.register_blueprint(environments)
        self._app.register_blueprint(regions)
        self._app.register_blueprint(servers)
        self._app.register_blueprint(auxiliary)
        self._app.register_blueprint(slack)
        self._app.register_blueprint(deployments)
        self._app.register_blueprint(deployments_basic)
        self._app.register_blueprint(deployments_pro)
