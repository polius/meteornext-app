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
        # Delete finished executions from the queue
        self._utils_queued.delete_finished()

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
        if len(execution_ids['export']):
            executions['export'] = self._utils_queued.get_queued_exports(export_ids=execution_ids['export'])
        if len(execution_ids['clone']):
            executions['clone'] = self._utils_queued.get_queued_clones(clone_ids=execution_ids['clone'])

        # Get file path
        file_path = json.loads(self._settings.get(setting_name='FILES'))['path']

        # Get Amazon S3 credentials
        amazon_s3 = json.loads(self._settings.get(setting_name='AMAZON'))

        # Process imports
        self.__process_queued_imports(executions['import'], file_path)
        self.__process_queued_exports(executions['export'], file_path, amazon_s3)
        self.__process_queued_clones(executions['clone'], file_path, amazon_s3)

    def __process_queued_imports(self, executions, file_path):
        for execution in executions:
            # Build user
            user = {"id": execution['user_id']}

            # Get server details
            server = self._servers.get(user_id=execution['user_id'], group_id=execution['group_id'], server_id=execution['server_id'])
            if len(server) == 0:
                self._imports.update_status(user, execution['id'], 'FAILED', 'This server no longer exists in your inventory.')
                continue
            server = server[0]
            if not server['active']:
                self._imports.update_status(user, execution['id'], 'FAILED', 'The selected server is disabled.')
                continue

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

    def __process_queued_exports(self, executions, file_path, amazon_s3):
        for execution in executions:
            # Build user
            user = {"id": execution['user_id']}

            # Get server details
            server = self._servers.get(user_id=execution['user_id'], group_id=execution['group_id'], server_id=execution['server_id'])
            if len(server) == 0:
                self._exports.update_status(user, execution['id'], 'FAILED', 'This server no longer exists in your inventory.')
                continue
            server = server[0]
            if not server['active']:
                self._exports.update_status(user, execution['id'], 'FAILED', 'The selected server is disabled.')
                continue

            # Get region details
            region = self._regions.get(user_id=execution['user_id'], group_id=execution['group_id'], region_id=server['region_id'])
            if len(region) == 0:
                self._exports.update_status(user, execution['id'], 'FAILED', "This server's region no longer exists in your inventory.")
                continue
            region = region[0]

            # Init path
            path = {
                "local": os.path.join(file_path, 'exports'),
                "remote": '.meteor/exports'
            }

            # Get Amazon S3 credentials
            if not amazon_s3['enabled']:
                self._exports.update_status(user, execution['id'], 'FAILED', "To perform exports enable the Amazon S3 flag in the Admin Panel.")
                continue

            # Build Item
            item = {
                "id": execution['id'],
                "mode": execution['mode'],
                "database": execution['database'],
                "tables": execution['tables'],
                "size": execution['size'],
                "export_schema": execution['export_schema'],
                "add_drop_table": execution['add_drop_table'],
                "export_data": execution['export_data'],
                "export_triggers": execution['export_triggers'],
                "export_routines": execution['export_routines'],
                "export_events": execution['export_events'],
                "url": execution['url'],
                "uri": execution['uri'],
                "server_name": server['name'],
                "region_name": region['name'],
                "username": execution['username'],
                "slack_enabled": execution['slack_enabled'],
                "slack_url": execution['slack_url']
            }

            # Start export process
            self._exports.update_status(user, execution['id'], 'STARTING')
            self._export_app.start(user, item, server, region, path, amazon_s3)

    def __process_queued_clones(self, executions, file_path, amazon_s3):
        for execution in executions:
            # Build user
            user = {"id": execution['user_id']}

            # Get server details (source)
            servers = {}
            servers['source'] = self._servers.get(user_id=user['id'], group_id=execution['group_id'], server_id=execution['source_server'])
            if len(servers['source']) == 0:
                self._clones.update_status(user, execution['id'], 'FAILED', 'The source server no longer exists in your inventory.')
                continue
            servers['source'] = servers['source'][0]
            if not servers['source']['active']:
                self._clones.update_status(user, execution['id'], 'FAILED', 'The source server is disabled.')
                continue

            # Get server details (destination)
            servers['destination'] = self._servers.get(user_id=user['id'], group_id=execution['group_id'], server_id=execution['destination_server'])
            if len(servers['destination']) == 0:
                self._clones.update_status(user, execution['id'], 'FAILED', 'The destination server no longer exists in your inventory.')
                continue
            servers['destination'] = servers['destination'][0]
            if not servers['destination']['active']:
                self._clones.update_status(user, execution['id'], 'FAILED', 'The destination server is disabled.')
                continue

            # Get region details (source)
            regions = {}
            regions['source'] = self._regions.get(user_id=user['id'], group_id=execution['group_id'], region_id=servers['source']['region_id'])
            if len(regions['source']) == 0:
                self._clones.update_status(user, execution['id'], 'FAILED', "The source servers' region no longer exists in your inventory.")
                continue
            regions['source'] = regions['source'][0]

            # Get region details (destination)
            regions['destination'] = self._regions.get(user_id=user['id'], group_id=execution['group_id'], region_id=servers['destination']['region_id'])
            if len(regions['destination']) == 0:
                self._clones.update_status(user, execution['id'], 'FAILED', "The destination servers' region no longer exists in your inventory.")
                continue
            regions['destination'] = regions['destination'][0]

            # Init path
            path = {
                "local": os.path.join(file_path, 'clones'),
                "remote": '.meteor/clones'
            }

            # Get Amazon S3 credentials
            if not amazon_s3['enabled']:
                self._clones.update_status(user, execution['id'], 'FAILED', "To perform clones enable the Amazon S3 flag in the Admin Panel.")
                continue

            # Build Item
            item = {
                "id": execution['id'],
                "mode": execution['mode'],
                "create_database": execution['create_database'],
                "drop_database": execution['drop_database'],
                "source_database": execution['source_database'],
                "destination_database": execution['destination_database'],
                "tables": execution['tables'],
                "export_schema": execution['export_schema'],
                "add_drop_table": execution['add_drop_table'],
                "export_data": execution['export_data'],
                "export_triggers": execution['export_triggers'],
                "export_routines": execution['export_routines'],
                "export_events": execution['export_events'],
                "size": execution['size'],
                "url": execution['url'],
                "uri": execution['uri'],
                "source_server_name": servers['source']['name'],
                "source_region_name": regions['source']['name'],
                "destination_server_name": servers['destination']['name'],
                "destination_region_name": regions['destination']['name'],
                "username": execution['username'],
                "slack_enabled": execution['slack_enabled'],
                "slack_url": execution['slack_url']
            }

            # Start clone process
            self._clones.update_status(user, execution['id'], 'STARTING')
            self._clone_app.start(user, item, servers, regions, path, amazon_s3)
