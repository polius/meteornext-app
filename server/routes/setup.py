import os
import sys
import json
import uuid
import bcrypt
import hashlib
import requests
import threading
import models.admin.groups
import models.admin.users
import models.mysql
from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity)

import utils
import routes.login
import routes.profile
import routes.notifications
import routes.admin.settings
import routes.admin.groups
import routes.admin.users
import routes.admin.deployments
import routes.deployments.settings.environments
import routes.deployments.settings.regions
import routes.deployments.settings.servers
import routes.deployments.settings.auxiliary
import routes.deployments.settings.slack
import routes.deployments.releases
import routes.deployments.deployments
import routes.deployments.views.basic
import routes.deployments.views.pro
import routes.deployments.views.inbenta
import models.mysql
import models.admin.settings
import models.deployments.regions
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
        self._cron = None
        
        # Start Setup
        try:
            with open(self._setup_file) as file_open:
                self._conf = json.load(file_open)
            # Set unique hardware id
            self._conf['license']['uuid'] = str(uuid.getnode())
            # Test sql connection
            sql = models.mysql.mysql(self._conf['sql']['hostname'], self._conf['sql']['username'], self._conf['sql']['password'], self._conf['sql']['port'], self._conf['sql']['database'])
            sql.test()
            # Check license
            self._license = self.__check_license(self._conf['license'])
            # Register blueprints
            self.__register_blueprints(sql)
            # Init cron
            self._cron = Cron(self._app, self._license, self._conf['license'], self._blueprints, sql)
            self.__cron_start()

        except Exception as e:
            self._conf = {}

    def blueprint(self):
        # Init blueprint
        setup_blueprint = Blueprint('setup', __name__, template_folder='setup')

        @setup_blueprint.route('/setup', methods=['GET'])
        def setup():
            if self.__setup_available():
                return jsonify({'setup': True}), 200
            else:
                lic = self._cron.license
                if lic['status'] == 200:
                    return jsonify({'setup': False}), 200
                return jsonify({"message": lic['response']}), lic['code']

        @setup_blueprint.route('/setup/license', methods=['POST'])
        def setup_license():
            # Protect api call once is already configured
            if not self.__setup_available():
                return jsonify({}), 401

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400

            # Get Params
            setup_json = request.get_json()

            # Set unique hardware id
            setup_json['uuid'] = str(uuid.getnode())

            # Part 1: Check License
            self._license = self.__check_license(setup_json)
            return jsonify({"message": self._license['response']}), self._license['code']
            
        @setup_blueprint.route('/setup/sql', methods=['POST'])
        def setup_sql():
            # Protect api call once is already configured
            if not self.__setup_available():
                return jsonify({}), 401

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400

            # Get Params
            setup_json = request.get_json()

            # Part 2: Check SQL Credentials
            try:
                sql = models.mysql.mysql(setup_json['hostname'], setup_json['username'], setup_json['password'], setup_json['port'])
                sql.test()
            except Exception as e:
                return jsonify({'message': "Can't connect to MySQL server"}), 400

            # Check Database Access
            try:
                exists = sql.check_db_exists(setup_json['database'])
                sql = models.mysql.mysql(setup_json['hostname'], setup_json['username'], setup_json['password'], setup_json['port'], setup_json['database'])
                sql.test()
                return jsonify({'message': 'Connection Successful', 'exists': exists}), 200
            except Exception as e:
                if "Unknown database " in str(e): 
                    return jsonify({'message': 'Connection Successful', 'exists': exists}), 200
                return jsonify({'message': "Access denied for user 'meteor' to database '{}'".format(setup_json['database'])}), 400 

        @setup_blueprint.route('/setup', methods=['POST'])
        def setup_account():
            # Protect api call once is already configured
            if not self.__setup_available():
                return jsonify({}), 401

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400

            # Get Params
            setup_json = request.get_json()

            try:
                # Part 3: Build Meteor & Create User Admin Account
                if setup_json['sql']['recreate']:
                    sql = models.mysql.mysql(setup_json['sql']['hostname'], setup_json['sql']['username'], setup_json['sql']['password'], setup_json['sql']['port'])
                    # Import SQL Schema
                    sql.execute('DROP DATABASE IF EXISTS {}'.format(setup_json['sql']['database']))
                    sql.execute('CREATE DATABASE {}'.format(setup_json['sql']['database']))
                    sql = models.mysql.mysql(setup_json['sql']['hostname'], setup_json['sql']['username'], setup_json['sql']['password'], setup_json['sql']['port'], setup_json['sql']['database'])

                    with open(self._schema_file) as file_open:
                        queries = file_open.read().split(';')
                        for q in queries:
                            if q != '':
                                sql.execute(q)

                    # Create group
                    groups = models.admin.groups.Groups(sql)
                    group = {"name": 'Administrator', "description": 'The Admin', "coins_day": 25, "coins_max": 100, "coins_execution": 10, "deployments_enable": 1, "deployments_basic": 1, "deployments_pro": 1, "deployments_inbenta": 1, "deployments_edit": 1, "deployments_execution_threads": 10, "deployments_execution_limit": 0}
                    groups.post(0, group)

                    # Create user
                    users = models.admin.users.Users(sql)
                    user = {"username": setup_json['account']['username'], "password": setup_json['account']['password'], "email": "admin@admin.com", "coins": 100, "group": 'Administrator', "admin": 1}
                    user['password'] = bcrypt.hashpw(user['password'].encode('utf8'), bcrypt.gensalt())
                    users.post(0, user)

                    # Init Logs Local Path
                    settings = models.admin.settings.Settings(sql)
                    setting = {"name": "LOGS", "value": '{{"amazon_s3":{{"enabled":false}},"local":{{"path":"{}"}}}}'.format(self._logs_folder)}
                    settings.post(0, setting)
                else:
                    sql = models.mysql.mysql(setup_json['sql']['hostname'], setup_json['sql']['username'], setup_json['sql']['password'], setup_json['sql']['port'], setup_json['sql']['database'])

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
                    "port": int(setup_json['sql']['port']),
                    "username": setup_json['sql']['username'],
                    "password": setup_json['sql']['password'],
                    "database": setup_json['sql']['database']
                }
            }
            with open(self._setup_file, 'w') as outfile:
                json.dump(self._conf, outfile)

            # Init blueprints
            self.__register_blueprints(sql)

            # Set unique hardware id
            self._conf['license']['uuid'] = str(uuid.getnode())

            # Init cron
            self._cron = Cron(self._app, self._license, self._conf['license'], self._blueprints, sql)
            self.__cron_start()

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
            # Generate trial
            license['trial'] = str(uuid.uuid4())
            # Check license
            response = requests.post("http://34.252.139.218:12350/license", json=license, allow_redirects=False)
            response_code = response.status_code
            response_status = response.status_code == 200
            response_text = json.loads(response.text)['response']
            
            # Solve trial
            if response_status == 200:
                response_trial = json.loads(response.text)['trial']
                trial = ','.join([str(ord(i)) for i in license['trial']])
                trial = hashlib.sha3_256(trial.encode()).hexdigest()

                # Validate trials
                if response_trial != trial:
                    response_text = "The license is not valid"
                    response_code = 401
                    response_status = False

            return {"status": response_status, "code": response_code, "response": response_text}

        except requests.exceptions.RequestException:
            return {"status": False, "code": 404, "response": "A connection to the licensing server could not be established"}

    def __register_blueprints(self, sql):
        # Init all blueprints
        login = routes.login.Login(self._app, sql)
        profile = routes.profile.Profile(self._app, sql)
        notifications = routes.notifications.Notifications(self._app, sql)
        settings = routes.admin.settings.Settings(self._app, sql, self._conf)
        groups = routes.admin.groups.Groups(self._app, sql)
        users = routes.admin.users.Users(self._app, sql)
        admin_deployments = routes.admin.deployments.Deployments(self._app, sql)
        environments = routes.deployments.settings.environments.Environments(self._app, sql)
        regions = routes.deployments.settings.regions.Regions(self._app, sql)
        servers = routes.deployments.settings.servers.Servers(self._app, sql)
        auxiliary = routes.deployments.settings.auxiliary.Auxiliary(self._app, sql)
        slack = routes.deployments.settings.slack.Slack(self._app, sql)
        releases = routes.deployments.releases.Releases(self._app, sql)
        deployments = routes.deployments.deployments.Deployments(self._app, sql)
        deployments_basic = routes.deployments.views.basic.Basic(self._app, sql)
        deployments_pro = routes.deployments.views.pro.Pro(self._app, sql)
        deployments_inbenta = routes.deployments.views.inbenta.Inbenta(self._app, sql)

        self._blueprints = [login, profile, notifications, settings, groups, users, admin_deployments, environments, regions, servers, auxiliary, slack, releases, deployments, deployments_basic, deployments_pro, deployments_inbenta]

        # Register all blueprints
        for i in self._blueprints:
            i.license(self._license)
            self._app.register_blueprint(i.blueprint(), url_prefix=self._url_prefix)

    def __cron_start(self):
        # Check integrity
        try:
            response = self._cron.KMMLeSdKHFP9hBQCm7Pg9J3VtvjsNeEnuc4nyDV9ZD7QDxQUwaRgyddSZqxhsFP3()
            if response != 'FBfLXedVRQ4Kj4tAZ2EUcYruu8KX8WPYLaxjaCYzxuM3yF89aPXwLxE2AMwWz5Jr':
                sys.exit()
        except BaseException:
            sys.exit()

        # Start Cron
        self._cron.start()

    def __searchInListDict(self, list_dicts, key_name, value_to_find):
        # Search a key value in a list of dictionaries
        return len(filter(lambda obj: obj[key_name] == value_to_find, list_dicts)) > 0