#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import json
import uuid
import subprocess
import unicodedata
from time import time
from datetime import datetime
from multiprocessing import Process

import models.mysql
import models.admin.settings
import models.inventory.environments
import models.inventory.regions
import models.inventory.servers
import models.inventory.auxiliary
import models.admin.groups

class Meteor:
    def __init__(self, app, sql):
        self._app = app

        # Init models
        self._settings = models.admin.settings.Settings(sql)
        self._environments = models.inventory.environments.Environments(sql)
        self._regions = models.inventory.regions.Regions(sql)
        self._servers = models.inventory.servers.Servers(sql)
        self._auxiliary = models.inventory.auxiliary.Auxiliary(sql)
        self._groups = models.admin.groups.Groups(sql)

        # Init Meteor Config
        self._blueprint = ''
        self._config = {}

        # Retrieve Meteor Logs Path
        self._bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self._base_path = os.path.dirname(sys.executable) if self._bin else app.root_path

        # Logs Settings
        self._logs = {}

    def execute(self, deployment):
        # Generate Deployment Unique Identifier
        self._uuid = str(uuid.uuid4())

        # Init Logs Settings
        self._logs = json.loads(self._settings.get(setting_name='LOGS')[0]['value'])

        # Create Deployment Folder to store Meteor files
        if not os.path.isdir('{}/{}/keys'.format(self._logs['local']['path'], self._uuid)):
            os.makedirs('{}/{}/keys'.format(self._logs['local']['path'], self._uuid))

        # Compile Meteor Files
        self.__compile_config(deployment)
        self.__compile_blueprint(deployment)

        # Execute Meteor
        self.__execute(deployment)

    def __compile_config(self, deployment):
        # Get Data
        environment = self._environments.get_by_name(deployment['user_id'], deployment['group_id'], deployment['environment'])
        regions = self._regions.get_by_environment(deployment['user_id'], deployment['group_id'], deployment['environment'])
        servers = self._servers.get_by_environment(deployment['user_id'], deployment['group_id'], deployment['environment'])
        auxiliary = self._auxiliary.get(deployment['user_id'], deployment['group_id'])
        slack = self._groups.get_slack(deployment['group_id'])

        if len(environment) == 0:
            return
    
        # Compile Regions
        self._config['regions'] = []

        for region in regions:
            # Compile SSH
            key_path = "{}/{}/keys/r{}".format(self._logs['local']['path'], self._uuid, region['id'])
            region_data = {
                "name": region['name'],
                "ssh": {
                    "enabled": True if region['ssh_tunnel'] else False,
                    "hostname": "" if region['hostname'] is None else region['hostname'],
                    "username": "" if region['username'] is None else region['username'],
                    "password": "" if region['password'] is None else region['password'],
                    "key": "" if region['key'] is None else key_path,
                    "port": "" if region['port'] is None else region['port']
                },
                "sql": []
            }

            # Generate region key files
            if region['key'] is not None:
                with open(key_path, 'w') as outfile:
                    outfile.write(region['key'])
                os.chmod(key_path, 0o600)

            # Compile SQL
            for server in servers:
                if server['region_id'] == region['id']:
                    region_data['sql'].append({
                        "name": server['name'],
                        "engine": server['engine'],
                        "hostname": server['hostname'],
                        "username": server['username'],
                        "password": server['password'],
                        "port": int(server['port'])
                    })

            # Add region data to the credentials
            self._config['regions'].append(region_data)

        # Compile Auxiliary Connections
        self._config['auxiliary_connections'] = {}
        for aux in auxiliary:
            key_path = "{}/{}/keys/a{}".format(self._logs['local']['path'], self._uuid, aux['id'])
            self._config['auxiliary_connections'][aux['name']] = {
                "ssh": {
                    "enabled": True if aux['ssh_tunnel'] else False,
                    "hostname": "" if aux['ssh_hostname'] is None else aux['ssh_hostname'],
                    "username": "" if aux['ssh_username'] is None else aux['ssh_username'],
                    "password": "" if aux['ssh_password'] is None else aux['ssh_password'],
                    "key": "" if aux['ssh_key'] is None else key_path,
                    "port": "" if aux['ssh_port'] is None else int(aux['ssh_port'])
                },
                "sql": {
                    "engine": aux['sql_engine'],
                    "hostname": aux['sql_hostname'],
                    "username": aux['sql_username'],
                    "password": aux['sql_password'],
                    "port": int(aux['sql_port'])
                }
            }

            # Generate auxiliary connection key files
            if aux['ssh_key'] is not None:
                with open(key_path, 'w') as outfile:
                    outfile.write(aux['ssh_key'])
                os.chmod(key_path, 0o600)
        
        # Compile Logs
        self._config['amazon_s3'] = {
            "enabled": False,
            "aws_access_key_id": "",
            "aws_secret_access_key": "",
            "region_name": "",
            "bucket_name": ""
        }

        if 'amazon_s3' in self._logs and self._logs['amazon_s3']['enabled']:
            self._config['amazon_s3'] = {
                "enabled": True,
                "aws_access_key_id": self._logs['amazon_s3']['aws_access_key'],
                "aws_secret_access_key": self._logs['amazon_s3']['aws_secret_access_key'],
                "region_name": self._logs['amazon_s3']['region_name'],
                "bucket_name": self._logs['amazon_s3']['bucket_name']
            }

        # Compile Slack
        self._config['slack'] = {
            "enabled": False,
            "channel_name": "",
            "webhook_url": ""
        }
        if slack['enabled']:
            self._config['slack'] = {
                "enabled":  True if slack['enabled'] else False,
                "channel_name": slack['channel_name'],
                "webhook_url": slack['webhook_url']
            }

        # Enable Meteor Next
        with open("{}/server.conf".format(self._base_path)) as outfile:
            next_credentials = json.load(outfile)['sql']

        # Compile Meteor Next Credentials
        self._config['meteor_next'] = {
            "enabled": True,
            "hostname": next_credentials['hostname'],
            "port": int(next_credentials['port']),
            "username": next_credentials['username'],
            "password": next_credentials['password'],
            "database": next_credentials['database']
        }

        # Compile Meteor Next Params
        self._config['params'] = {
            "id": deployment['execution_id'],
            "mode": deployment['mode'].lower(),
            "user": deployment['username'],
            "threads": deployment['execution_threads'],
            "limit": deployment['execution_limit'],
            "environment": deployment['environment'],
            "url": deployment['url']
        }

        # Store Config
        with open("{}/{}/config.json".format(self._logs['local']['path'], self._uuid), 'w') as outfile:
            json.dump(self._config, outfile)

    def __compile_blueprint(self, deployment):
        if deployment['mode'] == 'BASIC':
            self.__compile_blueprint_basic(deployment)
        elif deployment['mode'] == 'PRO':
            self._blueprint = deployment['code']

        # Store Query Execution
        with open("{}/{}/blueprint.py".format(self._logs['local']['path'], self._uuid), 'w') as outfile:
            outfile.write(self._blueprint.encode('utf-8','ignore').decode('utf-8'))

    def __compile_blueprint_basic(self, deployment):
        queries = {}
        for i, q in enumerate(json.loads(deployment['queries'])):
            queries[str(i+1)] = q['query']
        databases = [i.strip().replace('%','*').replace('_','?').replace('\\?','_') for i in  deployment['databases'].split(',')]

        self._blueprint = """import fnmatch
class blueprint:
    def __init__(self):
        self.queries = {0}
        self.auxiliary_queries = {{}}
    def before(self, meteor, environment, region):
        pass
    def main(self, meteor, environment, region, server, database):
        for d in {1}:
            if len(fnmatch.filter([database], d)) > 0:
                for i in self.queries.keys():
                    meteor.execute(query=self.queries[str(i)], database=database)
    def after(self, meteor, environment, region):
        pass""".format(json.dumps(queries), databases)

    def __execute(self, deployment):
        # Build Meteor Parameters
        meteor_base_path = sys._MEIPASS if self._bin else self._app.root_path
        meteor_path = "{}/apps/meteor/init".format(meteor_base_path) if self._bin else "python3 {}/../meteor/meteor.py".format(meteor_base_path)
        execution_path = "{}/{}".format(self._logs['local']['path'], self._uuid)
        execution_method = deployment['method'].lower()

        # Build Meteor Command
        command = '{} --path "{}" --{}'.format(meteor_path, execution_path, execution_method)
        # print(command)

        # Execute Meteor
        p = subprocess.Popen(command, stdout=open('/dev/null', 'w'), shell=True)