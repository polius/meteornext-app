import os
import sys
import json
import bcrypt
import requests
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
    def __init__(self, app, url_prefix):
        self._app = app
        self._url_prefix = url_prefix
        self._setup_file = "{}/server.conf".format(app.root_path) if sys.argv[0].endswith('.py') else "{}/server.conf".format(os.path.dirname(sys.executable))
        self._schema_file = "{}/models/schema.sql".format(app.root_path) if sys.argv[0].endswith('.py') else "{}/models/schema.sql".format(sys._MEIPASS)
        self._logs_folder = "{}/logs".format(app.root_path) if sys.argv[0].endswith('.py') else "{}/logs".format(os.path.dirname(sys.executable))
        self._blueprints = []
        self._license = {}
        
        # Start Setup
        try:
            with open(self._setup_file) as file_open:
                self._conf = json.load(file_open)
            sql = models.mysql.mysql()
            sql.connect(self._conf['sql']['hostname'], self._conf['sql']['username'], self._conf['sql']['password'], self._conf['sql']['port'], self._conf['sql']['database'])
            # Check license
            self._license = self.__check_license(self._conf['license'])
            # Register blueprints
            self.__register_blueprints(sql)
            # Init cron
            cron = Cron(self._license, self._conf['license'], self._blueprints, sql)
            self.__cron_start(cron)

        except Exception:
            self._conf = {}

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
                return jsonify({}), 401

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400

            # Get Params
            setup_json = request.get_json()

            # Part 1: Check License
            self._license = self.__check_license(setup_json)
            return jsonify({"message": self._license['response']}), self._license['code']
            
        @setup_blueprint.route('/setup/2', methods=['POST'])
        def setup2():
            # Protect api call once is already configured
            if not self.__setup_available():
                return jsonify({}), 401

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400

            # Get Params
            setup_json = request.get_json()

            # Part 2: Check SQL Credentials
            try:
                sql = models.mysql.mysql()
                sql.connect(setup_json['hostname'], setup_json['username'], setup_json['password'], setup_json['port'])
                exists = sql.check_db_exists(setup_json['database'])
                return jsonify({'message': 'Connection Successful', 'exists': exists}), 200
            except Exception as e:
                return jsonify({'message': str(e)}), 500

        @setup_blueprint.route('/setup/3', methods=['POST'])
        def setup3():
            # Protect api call once is already configured
            if not self.__setup_available():
                return jsonify({}), 401

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400

            # Get Params
            setup_json = request.get_json()

            # Part 3: Build Meteor & Create User Admin Account
            sql = models.mysql.mysql()
            sql.connect(setup_json['sql']['hostname'], setup_json['sql']['username'], setup_json['sql']['password'], setup_json['sql']['port'])

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
                "license":
                {
                    "email": setup_json['license']['email'],
                    "key": setup_json['license']['key']
                },
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

            # Init cron
            cron = Cron(self._license, self._conf['license'], self._blueprints, sql)
            self.__cron_start(cron)

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

    def __check_license(self, license):
        try:
            response = requests.post("http://www.poliuscorp.com:12350/license", json=license)
            response_text = json.loads(response.text)['response']
            print(response_text)
            return {"status": response.status_code == 200, "code": response.status_code, "response": response_text}
        except requests.exceptions.RequestException:
            return {"status": False, "code": 404, "response": "A connection to the licensing server could not be established"}

    def __register_blueprints(self, sql):
        # Init all blueprints
        login = routes.login.Login(self._app, sql)
        profile = routes.profile.Profile(self._app, sql)
        settings = routes.admin.settings.Settings(self._app, self._conf, sql)
        groups = routes.admin.groups.Groups(self._app, sql)
        users = routes.admin.users.Users(self._app, sql)
        admin_deployments = routes.admin.deployments.Deployments(self._app, sql)
        environments = routes.deployments.settings.environments.Environments(self._app, sql)
        regions = routes.deployments.settings.regions.Regions(self._app, sql)
        servers = routes.deployments.settings.servers.Servers(self._app, sql)
        auxiliary = routes.deployments.settings.auxiliary.Auxiliary(self._app, sql)
        slack = routes.deployments.settings.slack.Slack(self._app, sql)
        deployments = routes.deployments.deployments.Deployments(self._app, sql)
        deployments_basic = routes.deployments.views.basic.Basic(self._app, sql)
        deployments_pro = routes.deployments.views.pro.Pro(self._app, sql)

        self._blueprints = [login, profile, settings, groups, users, admin_deployments, environments, regions, servers, auxiliary, slack, deployments, deployments_basic, deployments_pro]

        # Register all blueprints
        for i in self._blueprints:
            i.license(self._license)
            self._app.register_blueprint(i.blueprint(), url_prefix=self._url_prefix)

    def __cron_start(self, cron):
        # Check integrity
        try:
            response = cron.KMMLeSdKHFP9hBQCm7Pg9J3VtvjsNeEnuc4nyDV9ZD7QDxQUwaRgyddSZqxhsFP3()
            if response != 'FBfLXedVRQ4Kj4tAZ2EUcYruu8KX8WPYLaxjaCYzxuM3yF89aPXwLxE2AMwWz5Jr':
                sys.exit()
        except BaseException:
            sys.exit()

        # Start Cron
        cron.start()
