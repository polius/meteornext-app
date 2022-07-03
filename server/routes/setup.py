import os
import sys
import json
import uuid
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

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
import routes.utils.utils
import routes.utils.imports
import routes.utils.exports
import routes.utils.clones
import connectors.pool

class Setup:
    def __init__(self, app, license, url_prefix):
        self._app = app
        self._url_prefix = url_prefix
        self._conf = {}
        self._license = license
        root_path = os.path.realpath(os.path.dirname(sys.argv[0]))
        setup_file = "{}/server.conf".format(root_path) if sys.argv[0].endswith('.py') else "{}/server.conf".format(os.path.dirname(sys.executable))

        # Init Install blueprint
        install = routes.install.Install(self._license, self._conf, self.register_blueprints)
        self._app.register_blueprint(install.blueprint(), url_prefix=self._url_prefix)

        try:
            # Check if Meteor is initiated with all required params.
            with open(setup_file) as file_open:
                self._conf = json.load(file_open)
            # Set unique hardware id
            self._conf['license']['uuid'] = str(uuid.getnode())
            # Init sql pool
            sql = connectors.pool.Pool(self._conf['sql'])
            # Init license
            self._license.set_license(self._conf['license'])
            self._license.validate()
            # Init sentry
            if 'sentry' in self._license.get_status() and self._license.get_status()['sentry'] is not None:
                sentry_sdk.init(dsn=self._license.get_status()['sentry'], environment=self._conf['license']['access_key'], traces_sample_rate=0, integrations=[FlaskIntegration()])
            # Register blueprints
            self.register_blueprints(sql)
            print("- Meteor initiated from existing configuration.")
        except Exception as e:
            print(f"Error: {str(e)}")
            print("- Meteor initiated. No configuration detected. Install is required.")

    ####################
    # Internal Methods #
    ####################
    def register_blueprints(self, sql):
        # Init all blueprints
        login = routes.login.Login(sql, self._license)
        profile = routes.profile.Profile(sql, self._license)
        mfa = routes.mfa.MFA(sql, self._license)
        notifications = routes.notifications.Notifications(sql, self._license)
        settings = routes.admin.settings.Settings(sql, self._license, self._conf)
        groups = routes.admin.groups.Groups(sql, self._license)
        users = routes.admin.users.Users(sql, self._license)
        admin_deployments = routes.admin.deployments.Deployments(sql, self._license)
        admin_inventory = routes.admin.inventory.inventory.Inventory(sql, self._license)
        admin_inventory_environments = routes.admin.inventory.environments.Environments(sql, self._license)
        admin_inventory_regions = routes.admin.inventory.regions.Regions(sql, self._license)
        admin_inventory_servers = routes.admin.inventory.servers.Servers(sql, self._license)
        admin_inventory_auxiliary = routes.admin.inventory.auxiliary.Auxiliary(sql, self._license)
        admin_inventory_cloud = routes.admin.inventory.cloud.Cloud(sql, self._license)
        admin_utils_imports = routes.admin.utils.imports.Imports(sql, self._license)
        admin_utils_exports = routes.admin.utils.exports.Exports(sql, self._license)
        admin_utils_clones = routes.admin.utils.clones.Clones(sql, self._license)
        admin_client = routes.admin.client.Client(sql, self._license)
        admin_monitoring = routes.admin.monitoring.Monitoring(sql, self._license)
        inventory = routes.inventory.inventory.Inventory(sql, self._license)
        environments = routes.inventory.environments.Environments(sql, self._license)
        regions = routes.inventory.regions.Regions(sql, self._license)
        servers = routes.inventory.servers.Servers(sql, self._license)
        auxiliary = routes.inventory.auxiliary.Auxiliary(sql, self._license)
        cloud = routes.inventory.cloud.Cloud(sql, self._license)
        releases = routes.deployments.releases.Releases(sql, self._license)
        shared = routes.deployments.shared.Shared(sql, self._license)
        deployments = routes.deployments.deployments.Deployments(sql, self._license)
        monitoring = routes.monitoring.monitoring.Monitoring(sql, self._license)
        monitoring_parameters = routes.monitoring.views.parameters.Parameters(sql, self._license)
        monitoring_processlist = routes.monitoring.views.processlist.Processlist(sql, self._license)
        monitoring_queries = routes.monitoring.views.queries.Queries(sql, self._license)
        client = routes.client.client.Client(self._app, sql, self._license)
        utils = routes.utils.utils.Utils(sql, self._license)
        imports = routes.utils.imports.Imports(sql, self._license)
        exports = routes.utils.exports.Exports(sql, self._license)
        clones = routes.utils.clones.Clones(sql, self._license)

        # Register all blueprints
        blueprints = [login, profile, mfa, notifications, settings, groups, users, admin_deployments, admin_inventory, admin_inventory_environments, admin_inventory_regions, admin_inventory_servers, admin_inventory_auxiliary, admin_inventory_cloud, admin_utils_imports, admin_utils_exports, admin_utils_clones, admin_client, admin_monitoring, inventory, environments, regions, servers, auxiliary, cloud, releases, shared, deployments, monitoring, monitoring_parameters, monitoring_processlist, monitoring_queries, utils, client, imports, exports, clones]
        for i in blueprints:
            self._app.register_blueprint(i.blueprint(), url_prefix=self._url_prefix)
