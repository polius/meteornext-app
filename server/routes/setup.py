import os
import sys
import json
# import uuid
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
    def __init__(self, app, license, url_prefix, sentry_dsn):
        self._app = app
        self._url_prefix = url_prefix
        self._conf = {}
        self._license = license
        root_path = os.path.realpath(os.path.dirname(sys.argv[0]))
        setup_file = "{}/server.conf".format(root_path) if sys.argv[0].endswith('.py') else "{}/server.conf".format(os.path.dirname(sys.executable))

        # Register blueprints
        blueprints = self.register_blueprints()

        # Init Install blueprint
        install = routes.install.Install(app, self._license, self._conf, blueprints)
        app.register_blueprint(install.blueprint(), url_prefix=self._url_prefix)

        # Check if Meteor is initiated with all required params.
        try:
            with open(setup_file) as file_open:
                self._conf = json.load(file_open)
        except FileNotFoundError:
            print("- Meteor initiated. No configuration detected. Install is required.")
        else:
            # Set unique hardware id
            self._conf['license']['uuid'] = app.config['JWT_SECRET_KEY'] # str(uuid.getnode())
            # Init sql pool
            sql = connectors.pool.Pool(self._conf['sql'])
            # Init license
            self._license.set_license(self._conf['license'])
            self._license.validate()
            # Init sentry
            if self._license.get_status()['sentry']:
                sentry_sdk.init(dsn=sentry_dsn, environment=self._conf['license']['access_key'], traces_sample_rate=0, integrations=[FlaskIntegration()])
            # Init blueprints
            for k,v in blueprints.items():
                if k == 'settings':
                    v.init(sql, self._conf)
                else:
                    v.init(sql)
            print("- Meteor initiated from existing configuration.")

    ####################
    # Internal Methods #
    ####################
    def register_blueprints(self):
        # Init all blueprints
        login = routes.login.Login(self._license)
        profile = routes.profile.Profile(self._license)
        mfa = routes.mfa.MFA(self._license)
        notifications = routes.notifications.Notifications(self._license)
        settings = routes.admin.settings.Settings(self._license)
        groups = routes.admin.groups.Groups(self._license)
        users = routes.admin.users.Users(self._license)
        admin_deployments = routes.admin.deployments.Deployments(self._license)
        admin_inventory = routes.admin.inventory.inventory.Inventory(self._license)
        admin_inventory_environments = routes.admin.inventory.environments.Environments(self._license)
        admin_inventory_regions = routes.admin.inventory.regions.Regions(self._license)
        admin_inventory_servers = routes.admin.inventory.servers.Servers(self._license)
        admin_inventory_auxiliary = routes.admin.inventory.auxiliary.Auxiliary(self._license)
        admin_inventory_cloud = routes.admin.inventory.cloud.Cloud(self._license)
        admin_utils_imports = routes.admin.utils.imports.Imports(self._license)
        admin_utils_exports = routes.admin.utils.exports.Exports(self._license)
        admin_utils_clones = routes.admin.utils.clones.Clones(self._license)
        admin_client = routes.admin.client.Client(self._license)
        admin_monitoring = routes.admin.monitoring.Monitoring(self._license)
        inventory = routes.inventory.inventory.Inventory(self._license)
        environments = routes.inventory.environments.Environments(self._license)
        regions = routes.inventory.regions.Regions(self._license)
        servers = routes.inventory.servers.Servers(self._license)
        auxiliary = routes.inventory.auxiliary.Auxiliary(self._license)
        cloud = routes.inventory.cloud.Cloud(self._license)
        releases = routes.deployments.releases.Releases(self._license)
        shared = routes.deployments.shared.Shared(self._license)
        deployments = routes.deployments.deployments.Deployments(self._license)
        monitoring = routes.monitoring.monitoring.Monitoring(self._license)
        monitoring_parameters = routes.monitoring.views.parameters.Parameters(self._license)
        monitoring_processlist = routes.monitoring.views.processlist.Processlist(self._license)
        monitoring_queries = routes.monitoring.views.queries.Queries(self._license)
        client = routes.client.client.Client(self._license)
        utils = routes.utils.utils.Utils(self._license)
        imports = routes.utils.imports.Imports(self._license)
        exports = routes.utils.exports.Exports(self._license)
        clones = routes.utils.clones.Clones(self._license)

        # Register all blueprints
        blueprints = {"login": login, "profile": profile, "mfa": mfa, "notifications": notifications, "settings": settings, "groups": groups, "users": users, "admin_deployments": admin_deployments, "admin_inventory": admin_inventory, "admin_inventory_environments": admin_inventory_environments, "admin_inventory_regions": admin_inventory_regions, "admin_inventory_servers": admin_inventory_servers, "admin_inventory_auxiliary": admin_inventory_auxiliary, "admin_inventory_cloud": admin_inventory_cloud, "admin_utils_imports": admin_utils_imports, "admin_utils_exports": admin_utils_exports, "admin_utils_clones": admin_utils_clones, "admin_client": admin_client, "admin_monitoring": admin_monitoring, "inventory": inventory, "environments": environments, "regions": regions, "servers": servers, "auxiliary": auxiliary, "cloud": cloud, "releases": releases, "shared": shared, "deployments": deployments, "monitoring": monitoring, "monitoring_parameters": monitoring_parameters, "monitoring_processlist": monitoring_processlist, "monitoring_queries": monitoring_queries, "utils": utils, "client": client, "imports": imports, "exports": exports, "clones": clones}
        for i in blueprints.values():
            self._app.register_blueprint(i.blueprint(), url_prefix=self._url_prefix)

        # Return all blueprints
        return blueprints
