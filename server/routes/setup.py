import os
import sys
import json
import uuid
import bcrypt
import hashlib
import requests
import traceback
from datetime import datetime, timedelta
from flask import request, jsonify, Blueprint

import routes.login
import routes.profile
import routes.mfa
import routes.notifications
import routes.admin.settings
import routes.admin.groups
import routes.admin.users
import routes.admin.deployments
import routes.admin.inventory.inventory
import routes.admin.inventory.environments
import routes.admin.inventory.regions
import routes.admin.inventory.servers
import routes.admin.inventory.auxiliary
import routes.admin.client
import routes.inventory.environments
import routes.inventory.regions
import routes.inventory.servers
import routes.inventory.auxiliary
import routes.deployments.releases
import routes.deployments.deployments
import routes.deployments.views.basic
import routes.deployments.views.pro
import routes.monitoring.monitoring
import routes.monitoring.views.parameters
import routes.monitoring.views.processlist
import routes.monitoring.views.queries
import routes.client.client
import connectors.base
import connectors.pool
import models.admin.settings
import models.admin.groups
import models.admin.users
import apps.monitoring.monitoring
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
        
        # Start Setup
        try:
            with open(self._setup_file) as file_open:
                self._conf = json.load(file_open)
            # Set unique hardware id
            self._conf['license']['uuid'] = str(uuid.getnode())
            # Test sql connection
            sql = connectors.base.Base({'ssh': {'enabled': False}, 'sql': self._conf['sql']})
            sql.test_sql()
            # Init sql pool
            sql = connectors.pool.Pool(self._conf)
            # Init license
            self._license = License(self._conf['license'])
            self._license.validate()
            # Register blueprints
            self.__register_blueprints(sql)
            # Start monitoring
            monitoring = apps.monitoring.monitoring.Monitoring(sql)
            monitoring.start()
            # Init cron
            Cron(self._app, self._license, self._blueprints, sql)
        except Exception as e:
            traceback.print_exc()
            self._conf = {}

    def blueprint(self):
        # Init blueprint
        setup_blueprint = Blueprint('setup', __name__, template_folder='setup')

        @setup_blueprint.route('/setup', methods=['GET'])
        def setup():
            available =  self.__setup_available()
            if available:
                return jsonify({}), 200
            else:
                return jsonify({}), 401

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
            self._license.validate()
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
                sql = connectors.base.Base({'ssh': {'enabled': False}, 'sql': {'engine': setup_json['engine'], 'hostname': setup_json['hostname'], 'username': setup_json['username'], 'password': setup_json['password'], 'port': setup_json['port']}})
                sql.test_sql()
            except Exception as e:
                return jsonify({'message': "Connection Failed"}), 400

            # Check Database Access
            try:
                exists = sql.check_db_exists(setup_json['database'])
                sql = connectors.base.Base({'ssh': {'enabled': False}, 'sql': {'engine': setup_json['engine'], 'hostname': setup_json['hostname'], 'username': setup_json['username'], 'password': setup_json['password'], 'port': setup_json['port']}})
                sql.test_sql()
                return jsonify({'message': 'Connection Successful', 'exists': exists}), 200
            except Exception as e:
                if "Unknown database " in str(e): 
                    return jsonify({'message': 'Connection Successful', 'exists': exists}), 200
                return jsonify({'message': "Access denied for user '{}' to database '{}'".format(setup_json['username'], setup_json['database'])}), 400 

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
                    # Init sql pool
                    sql = connectors.pool.Pool(setup_json)
                    # Import SQL Schema
                    sql.execute('DROP DATABASE IF EXISTS {}'.format(setup_json['sql']['database']))
                    sql.execute('CREATE DATABASE {}'.format(setup_json['sql']['database']))

                    with open(self._schema_file) as file_open:
                        queries = file_open.read().split(';')
                        for q in queries:
                            if q != '':
                                sql.execute(q)

                    # Create group
                    groups = models.admin.groups.Groups(sql)
                    group = {"name": 'Administrator', "description": 'The Admin', "coins_day": 25, "coins_max": 100, "coins_execution": 10, "inventory_enabled": 1, "deployments_enabled": 1, "deployments_basic": 1, "deployments_pro": 1, "deployments_execution_threads": 10, "deployments_execution_limit": None, "deployments_execution_concurrent": None, "monitoring_enabled": 1, "utils_enabled": 1, "client_enabled": 1}
                    groups.post(1, group)

                    # Create user
                    users = models.admin.users.Users(sql)
                    user = {"username": setup_json['account']['username'], "password": setup_json['account']['password'], "email": "admin@admin.com", "coins": 100, "group": 'Administrator', "admin": 1}
                    user['password'] = bcrypt.hashpw(user['password'].encode('utf8'), bcrypt.gensalt())
                    users.post(1, user)

                    # Init Logs Local Path
                    settings = models.admin.settings.Settings(sql)
                    setting = {"name": "LOGS", "value": '{{"amazon_s3":{{"enabled":false}},"local":{{"path":"{}"}}}}'.format(self._logs_folder)}
                    settings.post(1, setting)
                else:
                    # Init sql pool
                    sql = connectors.pool.Pool(setup_json)

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
                    "engine": setup_json['sql']['engine'],
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
            Cron(self._app, self._license, self._blueprints, sql)

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
                if f['sql']['hostname'] != '' and f['sql']['username'] != '' and f['sql']['password'] != '' and f['sql']['port'] != '' and f['sql']['database'] != '':
                    return False
        return True

    def __register_blueprints(self, sql):
        # Init all blueprints
        login = routes.login.Login(self._app, sql, self._license)
        profile = routes.profile.Profile(self._app, sql, self._license)
        mfa = routes.mfa.MFA(self._app, sql, self._license)
        notifications = routes.notifications.Notifications(self._app, sql, self._license)
        settings = routes.admin.settings.Settings(self._app, sql, self._license, self._conf)
        groups = routes.admin.groups.Groups(self._app, sql, self._license)
        users = routes.admin.users.Users(self._app, sql, self._license)
        admin_deployments = routes.admin.deployments.Deployments(self._app, sql, self._license)
        admin_inventory = routes.admin.inventory.inventory.Inventory(self._app, sql, self._license)
        admin_inventory_environments = routes.admin.inventory.environments.Environments(self._app, sql, self._license)
        admin_inventory_regions = routes.admin.inventory.regions.Regions(self._app, sql, self._license)
        admin_inventory_servers = routes.admin.inventory.servers.Servers(self._app, sql, self._license)
        admin_inventory_auxiliary = routes.admin.inventory.auxiliary.Auxiliary(self._app, sql, self._license)
        admin_client = routes.admin.client.Client(self._app, sql, self._license)
        environments = routes.inventory.environments.Environments(self._app, sql, self._license)
        regions = routes.inventory.regions.Regions(self._app, sql, self._license)
        servers = routes.inventory.servers.Servers(self._app, sql, self._license)
        auxiliary = routes.inventory.auxiliary.Auxiliary(self._app, sql, self._license)
        releases = routes.deployments.releases.Releases(self._app, sql, self._license)
        deployments = routes.deployments.deployments.Deployments(self._app, sql, self._license)
        deployments_basic = routes.deployments.views.basic.Basic(self._app, sql, self._license)
        deployments_pro = routes.deployments.views.pro.Pro(self._app, sql, self._license)
        monitoring = routes.monitoring.monitoring.Monitoring(self._app, sql, self._license)
        monitoring_parameters = routes.monitoring.views.parameters.Parameters(self._app, sql, self._license)
        monitoring_processlist = routes.monitoring.views.processlist.Processlist(self._app, sql, self._license)
        monitoring_queries = routes.monitoring.views.queries.Queries(self._app, sql, self._license)
        client = routes.client.client.Client(self._app, sql, self._license)

        self._blueprints = [login, profile, mfa, notifications, settings, groups, users, admin_deployments, admin_inventory, admin_inventory_environments, admin_inventory_regions, admin_inventory_servers, admin_inventory_auxiliary, admin_client, environments, regions, servers, auxiliary, releases, deployments, deployments_basic, deployments_pro, monitoring, monitoring_parameters, monitoring_processlist, monitoring_queries, client]

        # Register all blueprints
        for i in self._blueprints:
            self._app.register_blueprint(i.blueprint(), url_prefix=self._url_prefix)

class License:
    def __init__(self, license):
        self._license_params = license
        self._license_status = {} 
        self._license_timeout = 24 # Hours
        self._last_login_date = str(datetime.utcnow())
        self._next_check = None
        self._next_check2 = None

    @property
    def status(self):
        return self._license_status

    @property
    def validated(self):
        return self._license_status and self._license_status['code'] == 200

    def validate(self):
        current_utc = str(datetime.utcnow())
        # Check if first time
        if not self._license_status:
            self.__check()
        # Check again if license server is unreachable
        elif self._license_status['code'] == 404:
            self.__check()
        # Check license if time was changed
        elif current_utc <= self._last_login_date or current_utc <= self._license_status['date']:
            self.__check()
        # Check next validation
        elif current_utc > self._next_check or current_utc > self._next_check2:
            self.__check()

        # Store last login date
        self._last_login_date = current_utc

    def __check(self):
        try:
            # Generate challenge
            self._license_params['challenge'] = str(uuid.uuid4())

            # Check license
            response = requests.post("https://license.meteor2.io/", json=self._license_params, allow_redirects=False)
            response_code = response.status_code
            response_text = json.loads(response.text)['response']
            date = json.loads(response.text)['date']
            expiration = None if 'expiration' not in json.loads(response.text) else json.loads(response.text)['expiration']

            # Solve challenge
            if response_code == 200:
                response_challenge = json.loads(response.text)['challenge']
                challenge = ','.join([str(ord(i)) for i in self._license_params['challenge']])
                challenge = hashlib.sha3_256(challenge.encode()).hexdigest()

                # Validate challenge
                if response_challenge != challenge:
                    response_text = "The license is not valid"
                    response_code = 401

            self._license_status = {"code": response_code, "response": response_text, "date": date, "expiration": expiration}
        except Exception:
            self._license_status = {"code": 404, "response": "A connection to the licensing server could not be established"}
        else:
            if self._license_status['code'] == 200:
                self._next_check = str(datetime.utcnow() + timedelta(hours=self._license_timeout))
                self._next_check2 = str(datetime.strptime(self._license_status['date'], '%Y-%m-%d %H:%M:%S.%f') + timedelta(hours=self._license_timeout))
