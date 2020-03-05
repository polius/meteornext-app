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
from datetime import datetime, timedelta
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
        self._license = None
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
            # Init license
            self._license = License(self._conf['license'])
            self._license.validated()
            # Register blueprints
            self.__register_blueprints(sql)
            # Init cron
            self._cron = Cron(self._app, self._license, self._blueprints, sql)
            self._cron.start()

        except Exception:
            self._conf = {}

    def blueprint(self):
        # Init blueprint
        setup_blueprint = Blueprint('setup', __name__, template_folder='setup')

        @setup_blueprint.route('/setup', methods=['GET'])
        def setup():
            return jsonify({'setup': self.__setup_available()}), 200

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
            self._license = License(setup_json)
            self._license.validated()
            return jsonify({"message": self._license.status['response']}), self._license.status['code']
            
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
            self._cron = Cron(self._app, self._license, self._blueprints, sql)
            self._cron.start()

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
        login = routes.login.Login(self._app, sql, self._license)
        profile = routes.profile.Profile(self._app, sql, self._license)
        notifications = routes.notifications.Notifications(self._app, sql, self._license)
        settings = routes.admin.settings.Settings(self._app, sql, self._license, self._conf)
        groups = routes.admin.groups.Groups(self._app, sql, self._license)
        users = routes.admin.users.Users(self._app, sql, self._license)
        admin_deployments = routes.admin.deployments.Deployments(self._app, sql, self._license)
        environments = routes.deployments.settings.environments.Environments(self._app, sql, self._license)
        regions = routes.deployments.settings.regions.Regions(self._app, sql, self._license)
        servers = routes.deployments.settings.servers.Servers(self._app, sql, self._license)
        auxiliary = routes.deployments.settings.auxiliary.Auxiliary(self._app, sql, self._license)
        slack = routes.deployments.settings.slack.Slack(self._app, sql, self._license)
        releases = routes.deployments.releases.Releases(self._app, sql, self._license)
        deployments = routes.deployments.deployments.Deployments(self._app, sql, self._license)
        deployments_basic = routes.deployments.views.basic.Basic(self._app, sql, self._license)
        deployments_pro = routes.deployments.views.pro.Pro(self._app, sql, self._license)
        deployments_inbenta = routes.deployments.views.inbenta.Inbenta(self._app, sql, self._license)

        self._blueprints = [login, profile, notifications, settings, groups, users, admin_deployments, environments, regions, servers, auxiliary, slack, releases, deployments, deployments_basic, deployments_pro, deployments_inbenta]

        # Register all blueprints
        for i in self._blueprints:
            self._app.register_blueprint(i.blueprint(), url_prefix=self._url_prefix)

class License:
    def __init__(self, license):
        self._license_params = license
        self._license_status = {} 
        self._license_timeout = 1  # Minutes
        self._last_login_date = str(datetime.utcnow())
        self._next_check = None
        self._next_check2 = None

    @property
    def status(self):
        return self._license_status

    @property
    def validated(self):
        return self._license_status and self._license_status['code'] == 200

    def validated(self):
        current_utc = str(datetime.utcnow())
        # Check if first time
        if not self._license_status:
            self.__check()
        # Check license if time was changed
        elif current_utc <= self._last_login_date or current_utc <= self._license_status['date']:
            self.__check()
        # Check next validation
        elif current_utc > self._next_check or current_utc > self._next_check2:
            self.__check()

        # Store last login date
        self._last_login_date = current_utc
        return self._license_status['code'] == 200

    def __check(self):
        try:
            # Generate challenge
            self._license_params['challenge'] = str(uuid.uuid4())

            # Check license
            response = requests.post("https://license.meteor2.io/", json=self._license_params, allow_redirects=False)
            response_code = response.status_code
            response_text = json.loads(response.text)['response']
            date = json.loads(response.text)['date']

            # Solve challenge
            if response_code == 200:
                response_challenge = json.loads(response.text)['challenge']
                challenge = ','.join([str(ord(i)) for i in self._license_params['challenge']])
                challenge = hashlib.sha3_256(challenge.encode()).hexdigest()

                # Validate challenge
                if response_challenge != challenge:
                    response_text = "The license is not valid"
                    response_code = 401

            self._license_status = {"code": response_code, "response": response_text, "date": date}
        except Exception:
            self._license_status = {"code": 404, "response": "A connection to the licensing server could not be established", "date": date}
        finally:
            minutes = self._license_timeout if self._license_status['code'] == 200 else 1
            self._next_check = str(datetime.utcnow() + timedelta(minutes=minutes))
            self._next_check2 = str(datetime.strptime(self._license_status['date'], '%Y-%m-%d %H:%M:%S.%f') + timedelta(minutes=minutes))
