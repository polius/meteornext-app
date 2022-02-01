import os
import json
from flask import Blueprint

import models.admin.users
import models.admin.groups
import models.admin.settings
import models.inventory.servers
import models.inventory.regions
import models.inventory.cloud
import models.notifications
import models.utils.imports
import models.utils.exports
import models.utils.clones
import models.utils.utils_queued
import apps.imports.imports
import apps.exports.exports
import apps.clones.clones

class Utils:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._groups = models.admin.groups.Groups(sql)
        self._settings = models.admin.settings.Settings(sql, license)
        self._servers = models.inventory.servers.Servers(sql, license)
        self._regions = models.inventory.regions.Regions(sql)
        self._cloud = models.inventory.cloud.Cloud(sql)
        self._notifications = models.notifications.Notifications(sql)
        self._imports = models.utils.imports.Imports(sql, license)
        self._exports = models.utils.exports.Exports(sql, license)
        self._clones = models.utils.clones.Clones(sql, license)
        self._utils_queued = models.utils.utils_queued.Utils_Queued(sql, license)
        # Init cores
        self._import_app = apps.imports.imports.Imports(sql)
        self._export_app = apps.exports.exports.Exports(sql)
        self._clone_app = apps.clones.clones.Clones(sql)

    def blueprint(self):
        # Init blueprint
        utils_blueprint = Blueprint('utils', __name__, template_folder='utils')
        return utils_blueprint

    ####################
    # Internal Methods #
    ####################
    def check_queued(self):
        # Notify finished queue executions and remove it from queue
        items = self._utils_queued.get_finished()
        self._utils_queued.delete(items)

        # Populate new queued executions
        self._utils_queued.build()

        # Build dictionary of executions
        executions_raw = self._utils_queued.get_next()
        groups = {}
        execution_ids = {"import":[],"export":[],"clone":[]}
        for i in executions_raw:
            concurrent = groups.get(i['group'], 0)
            if concurrent < i['concurrent']:
                groups[i['group']] = concurrent + 1
                if i['status'] == 'QUEUED':
                    execution_ids[i['source_type']].append(i['source_id'])
        executions = {"import":[],"export":[],"clone":[]}
        if len(execution_ids['import']):
            executions['import'] = self._utils_queued.get_queued_imports(import_ids=execution_ids['import'])

        # Process imports
        self.__process_queued_imports(executions['import'])

    def __process_queued_imports(self, executions):
        # Init file path
        file_path = json.loads(self._settings.get(setting_name='FILES'))['path']

        for execution in executions:
            # Build user
            user = {"id": execution['user_id']}

            # Get server details
            server = self._servers.get(user_id=execution['user_id'], group_id=execution['group_id'], server_id=execution['server_id'])
            if len(server) == 0:
                self._imports.update_status(user, execution['id'], 'FAILED', 'This server no longer exists in your inventory.')
                continue
            server = server[0]

            # Get region details
            region = self._regions.get(user_id=execution['user_id'], group_id=execution['group_id'], region_id=server['region_id'])
            if len(region) == 0:
                self._imports.update_status(user, execution['id'], 'FAILED', "This server's region no longer exists in your inventory.")
                continue
            region = region[0]

            # Init path
            path = {
                "local": os.path.join(file_path, 'imports'),
                "remote": '.meteor/imports'
            }

            # Init amazon s3
            amazon_s3 = None
            if execution['mode'] == 'cloud':
                details = json.loads(execution['details'])
                cloud = self._cloud.get(user_id=execution['user_id'], group_id=execution['group_id'], cloud_id=details['cloud']['id'])
                if len(cloud) == 0:
                    self._imports.update_status(user, execution['id'], 'FAILED', 'This cloud key no longer exists in your inventory.')
                    continue
                cloud = cloud[0]
                amazon_s3 = {
                    "aws_access_key": cloud['access_key'],
                    "aws_secret_access_key": cloud['secret_key'],
                    "bucket": details['cloud']['bucket']
                }

            # Build item
            item = {
                "id": execution['id'],
                "mode": execution['mode'],
                "source": execution['source'],
                "format": execution['format'],
                "selected": execution['selected'],
                "size": execution['size'],
                "database": execution['database'],
                "create_database": execution['create_database'],
                "drop_database": execution['drop_database'],
                "url": execution['url'],
                "uri": execution['uri'],
                "user_id": execution['user_id'],
                "slack_enabled": execution['slack_enabled'],
                "username": execution['username'],
                "server_name": server['name'],
                "region_name": region['name'],
                "slack_url": execution['slack_url']
            }
            # Start import process
            self._imports.update_status(user, execution['id'], 'STARTING')
            self._import_app.start(user, item, server, region, path, amazon_s3)
