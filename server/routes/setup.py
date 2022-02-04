import os
import sys
import json
import uuid
import hashlib
import requests
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from datetime import datetime

import routes.install
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
import routes.admin.inventory.cloud
import routes.admin.utils.imports
import routes.admin.utils.exports
import routes.admin.utils.clones
import routes.admin.client
import routes.admin.monitoring
import routes.inventory.inventory
import routes.inventory.environments
import routes.inventory.regions
import routes.inventory.servers
import routes.inventory.auxiliary
import routes.inventory.cloud
import routes.deployments.releases
import routes.deployments.shared
import routes.deployments.deployments
import routes.monitoring.monitoring
import routes.monitoring.views.parameters
import routes.monitoring.views.processlist
import routes.monitoring.views.queries
import routes.client.client
import routes.utils.imports
import routes.utils.exports
import routes.utils.clones
import connectors.pool
import apps.monitoring.monitoring
from cron import Cron

class Setup:
    def __init__(self, app, url_prefix):
        self._app = app
        self._url_prefix = url_prefix
        self._conf = {}
        self._license = License()
        self._setup_file = "{}/server.conf".format(app.root_path) if sys.argv[0].endswith('.py') else "{}/server.conf".format(os.path.dirname(sys.executable))

        # Init Install blueprint
        install = routes.install.Install(self._app, self._license, self.register_blueprints)
        self._app.register_blueprint(install.blueprint(), url_prefix=self._url_prefix)

        try:
            # Check if Meteor is initiated with all required params.
            with open(self._setup_file) as file_open:
                self._conf = json.load(file_open)
            # Set unique hardware id
            # hashlib.md5("host|port|user|pass|db".encode("utf-8")).hexdigest()
            self._conf['license']['uuid'] = str(uuid.getnode())
            # Init sql pool
            sql = connectors.pool.Pool(self._conf['sql'])
            # Init license
            self._license.license = self._conf['license']
            self._license.validate()
            # Register blueprints
            self.register_blueprints(sql)
            # Start monitoring
            monitoring = apps.monitoring.monitoring.Monitoring(self._license, sql)
            monitoring.start()
            # Init cron
            Cron(self._app, self._license, sql)
            print("- Meteor initiated from existing configuration.")
        except Exception:
            print("- Meteor initiated. No configuration detected. Install is required.")

    ####################
    # Internal Methods #
    ####################
    def register_blueprints(self, sql):
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
        admin_inventory_cloud = routes.admin.inventory.cloud.Cloud(self._app, sql, self._license)
        admin_utils_imports = routes.admin.utils.imports.Imports(self._app, sql, self._license)
        admin_utils_exports = routes.admin.utils.exports.Exports(self._app, sql, self._license)
        admin_utils_clones = routes.admin.utils.clones.Clones(self._app, sql, self._license)
        admin_client = routes.admin.client.Client(self._app, sql, self._license)
        admin_monitoring = routes.admin.monitoring.Monitoring(self._app, sql, self._license)
        inventory = routes.inventory.inventory.Inventory(self._app, sql, self._license)
        environments = routes.inventory.environments.Environments(self._app, sql, self._license)
        regions = routes.inventory.regions.Regions(self._app, sql, self._license)
        servers = routes.inventory.servers.Servers(self._app, sql, self._license)
        auxiliary = routes.inventory.auxiliary.Auxiliary(self._app, sql, self._license)
        cloud = routes.inventory.cloud.Cloud(self._app, sql, self._license)
        releases = routes.deployments.releases.Releases(self._app, sql, self._license)
        shared = routes.deployments.shared.Shared(self._app, sql, self._license)
        deployments = routes.deployments.deployments.Deployments(self._app, sql, self._license)
        monitoring = routes.monitoring.monitoring.Monitoring(self._app, sql, self._license)
        monitoring_parameters = routes.monitoring.views.parameters.Parameters(self._app, sql, self._license)
        monitoring_processlist = routes.monitoring.views.processlist.Processlist(self._app, sql, self._license)
        monitoring_queries = routes.monitoring.views.queries.Queries(self._app, sql, self._license)
        client = routes.client.client.Client(self._app, sql, self._license)
        imports = routes.utils.imports.Imports(self._app, sql, self._license)
        exports = routes.utils.exports.Exports(self._app, sql, self._license)
        clones = routes.utils.clones.Clones(self._app, sql, self._license)

        # Register all blueprints
        blueprints = [login, profile, mfa, notifications, settings, groups, users, admin_deployments, admin_inventory, admin_inventory_environments, admin_inventory_regions, admin_inventory_servers, admin_inventory_auxiliary, admin_inventory_cloud, admin_utils_imports, admin_utils_exports, admin_utils_clones, admin_client, admin_monitoring, inventory, environments, regions, servers, auxiliary, cloud, releases, shared, deployments, monitoring, monitoring_parameters, monitoring_processlist, monitoring_queries, client, imports, exports, clones]
        for i in blueprints:
            self._app.register_blueprint(i.blueprint(), url_prefix=self._url_prefix)

class License:
    def __init__(self):
        self._license_params = None
        self._license_status = {}
        self._last_check_date = datetime.utcnow()

    @property
    def status(self):
        return self._license_status

    @property
    def validated(self):
        return self._license_status and self._license_status['code'] == 200

    @property
    def resources(self):
        return self._license_status['resources']

    @property
    def last_check_date(self):
        return self._last_check_date

    @property
    def license(self): pass

    @license.setter
    def license(self, license):
        self._license_params = license

    def validate(self, force=False):
        if force or not self._license_status or self._license_status['code'] != 200:
            # Check license
            self.__check()

            # Store last check date
            self._last_check_date = datetime.utcnow()

            # Check sentry
            if 'sentry' in self._license_status and self._license_status['sentry'] is not None:
                sentry_sdk.init(dsn=self._license_status['sentry'], environment=self._license_params['access_key'], traces_sample_rate=0, integrations=[FlaskIntegration()])

    def __check(self):
        try:
            # Generate challenge
            self._license_params['challenge'] = str(uuid.uuid4())

            # Check license
            response = requests.post("https://license.meteor2.io/", json=self._license_params, headers={"x-meteor2-key": self._license_params['access_key']}, allow_redirects=False)

            # Check "x-meteor2-key" header is valid
            if response.status_code != 200:
                self._license_status = {"code": response.status_code, "response": "The license is not valid.", "resources": None, "sentry": None}
            else:
                # Check license is valid
                response_code = json.loads(response.text)['statusCode']
                response_body = json.loads(response.text)['body']
                response_text = response_body['response']
                resources = response_body['resources'] if response_code == 200 else None
                sentry = response_body['sentry'] if response_code == 200 else None

                # Solve challenge
                if response_code == 200:
                    response_challenge = response_body['challenge']
                    challenge = ','.join([str(ord(i)) for i in self._license_params['challenge']])
                    challenge = hashlib.sha3_256(challenge.encode()).hexdigest()

                    # Validate challenge
                    if response_challenge != challenge:
                        response_text = "The license is not valid."
                        response_code = 401

                self._license_status = {"code": response_code, "response": response_text, "resources": resources, "sentry": sentry}
        except Exception:
            if not self._license_status or self._license_status['code'] != 200 or int((datetime.utcnow()-self._last_check_date).total_seconds()) > 3600:
                self._license_status = {"code": 404, "response": "A connection to the licensing server could not be established"}
