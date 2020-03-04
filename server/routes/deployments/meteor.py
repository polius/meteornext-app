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
import models.deployments.environments
import models.deployments.regions
import models.deployments.servers
import models.deployments.auxiliary
import models.deployments.slack

class Meteor:
    def __init__(self, app, sql):
        self._app = app

        # Init models
        self._settings = models.admin.settings.Settings(sql)
        self._environments = models.deployments.environments.Environments(sql)
        self._regions = models.deployments.regions.Regions(sql)
        self._servers = models.deployments.servers.Servers(sql)
        self._auxiliary = models.deployments.auxiliary.Auxiliary(sql)
        self._slack = models.deployments.slack.Slack(sql)

        # Init Meteor Credentials
        self._query_execution = ''
        self._credentials = {}

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
        self.__compile_credentials(deployment)
        self.__compile_query_execution(deployment)

        # Execute Meteor
        self.__execute(deployment)

    def __compile_credentials(self, deployment):
        # Get Data
        environments = self._environments.get(deployment['group_id'])
        regions = self._regions.get(deployment['group_id'])
        servers = self._servers.get(deployment['group_id'])
        auxiliary = self._auxiliary.get(deployment['group_id'])
        slack = self._slack.get(deployment['group_id'])
    
        # Compile [Environments, Regions, Servers]
        self._credentials['environments'] = {}

        for environment in environments:
            if environment['name'] == deployment['environment']:
                self._credentials['environments'][environment['name']] = []
                for region in regions:
                    if region['environment_id'] == environment['id']:
                        key_path = "{}/{}/keys/r{}".format(self._logs['local']['path'], self._uuid, region['id'])
                        region_data = {
                            "region": region['name'],
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

                        for server in servers:
                            if server['environment_id'] == environment['id'] and server['region_id'] == region['id']:
                                region_data['sql'].append({
                                    "name": server['name'],
                                    "engine": server['engine'],
                                    "hostname": server['hostname'],
                                    "username": server['username'],
                                    "password": server['password'],
                                    "port": int(server['port'])
                                })

                        # Add region data to the credentials
                        self._credentials['environments'][environment['name']].append(region_data)

        # Compile Auxiliary Connections
        self._credentials['auxiliary_connections'] = {}
        for aux in auxiliary:
            key_path = "{}/{}/keys/a{}".format(self._logs['local']['path'], self._uuid, aux['id'])
            self._credentials['auxiliary_connections'][aux['name']] = {
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
        self._credentials['amazon_s3'] = {
            "enabled": False,
            "aws_access_key_id": "",
            "aws_secret_access_key": "",
            "region_name": "",
            "bucket_name": ""
        }

        if 'amazon_s3' in self._logs and self._logs['amazon_s3']['enabled']:
            self._credentials['amazon_s3'] = {
                "enabled": True,
                "aws_access_key_id": self._logs['amazon_s3']['aws_access_key'],
                "aws_secret_access_key": self._logs['amazon_s3']['aws_secret_access_key'],
                "region_name": self._logs['amazon_s3']['region_name'],
                "bucket_name": self._logs['amazon_s3']['bucket_name']
            }

        # Compile Slack
        self._credentials['slack'] = {
            "enabled": False,
            "channel_name": "",
            "webhook_url": ""
        }
        if len(slack) > 0:
            self._credentials['slack'] = {
                "enabled": True if slack[0]['enabled'] else False,
                "channel_name": slack[0]['channel_name'],
                "webhook_url": slack[0]['webhook_url']
            }

        # Enable Meteor Next
        with open("{}/server.conf".format(self._base_path)) as outfile:
            next_credentials = json.load(outfile)['sql']

        self._credentials['meteor_next'] = {
            "enabled": True,
            "hostname": next_credentials['hostname'],
            "port": int(next_credentials['port']),
            "username": next_credentials['username'],
            "password": next_credentials['password'],
            "database": next_credentials['database']
        }

        # Store Credentials
        with open("{}/{}/credentials.json".format(self._logs['local']['path'], self._uuid), 'w') as outfile:
            json.dump(self._credentials, outfile)

    def __compile_query_execution(self, deployment):
        if deployment['mode'] == 'BASIC':
            self.__compile_query_execution_basic(deployment)
        elif deployment['mode'] == 'PRO':
            self._query_execution = deployment['code']
        elif deployment['mode'] == 'INBENTA':
            self.__compile_query_execution_inbenta(deployment)

        # Store Query Execution
        with open("{}/{}/query_execution.py".format(self._logs['local']['path'], self._uuid), 'w') as outfile:
            outfile.write(self._query_execution.encode('utf-8','ignore').decode('utf-8'))

    def __compile_query_execution_basic(self, deployment):
        queries = {}
        for i, q in enumerate(json.loads(deployment['queries'])):
            queries[str(i+1)] = q['query']
        databases = [i.strip().replace('%','*').replace('_','?').replace('\\?','_') for i in  deployment['databases'].split(',')]

        self._query_execution = """import fnmatch
class query_execution:
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

    def __compile_query_execution_inbenta(self, deployment):
        queries = {}
        for i, q in enumerate(json.loads(deployment['queries'])):
            queries[str(i+1)] = q['query']
        databases = [i.strip().replace('%','*').replace('_','?').replace('\\?','_') for i in deployment['databases'].split(',')]
        products = ','.join("'{}'".format(p) for p in deployment['products'])

        self._query_execution = """import fnmatch
class query_execution:
    def __init__(self):
        self.queries = {0}
        self.auxiliary_queries = {{
            '1': {{"auxiliary_connection": "awseu-sql01", "database": "ilf_admin", "query": "SELECT CONCAT('ilf_', name, '_{1}') AS db_name FROM projects WHERE product IN ({2})"}},
            '2': {{"auxiliary_connection": "awseu-rd01", "database": "ilf_admin", "query": "SELECT CONCAT('ilf_', name, '_{1}') AS db_name FROM projects WHERE product IN ({2})"}}
        }}
    def before(self, meteor, environment, region):
        awseu_sql01 = meteor.execute(auxiliary=self.auxiliary_queries['1'])
        awseu_rd01 = meteor.execute(auxiliary=self.auxiliary_queries['2'])
        self._instances = awseu_sql01 + awseu_rd01
    def main(self, meteor, environment, region, server, database):
        for d in {3}:
            if len(self.__searchInListDict(self._instances, 'db_name', database)) > 0:
                if len(d) == 0 or len(fnmatch.filter([database], d)) > 0:
                    for i in self.queries.keys():
                        meteor.execute(query=self.queries[str(i)], database=database)
    def after(self, meteor, environment, region):
        pass
    def __searchInListDict(self, list_dicts, key_name, value_to_find):
        return [i for i in list_dicts if i[key_name] == value_to_find]""".format(json.dumps(queries), deployment['schema'], products, databases)

    def __execute(self, deployment):
        # Build Meteor Parameters
        meteor_base_path = sys._MEIPASS if self._bin else self._app.root_path
        meteor_path = "{}/apps/meteor/init".format(meteor_base_path) if self._bin else "python3 {}/../meteor/meteor.py".format(meteor_base_path)
        environment = deployment['environment']
        execution_method = deployment['method'].lower()
        execution_id = deployment['execution_id']
        execution_mode = deployment['mode'].lower()
        execution_user = deployment['user']
        execution_path = "{}/{}".format(self._logs['local']['path'], self._uuid)
        execution_threads = deployment['execution_threads']
        execution_limit = ' --execution_limit "{}"'.format(deployment['execution_limit']) if deployment['execution_limit'] else ''

        # Build Meteor Command
        command = '{} --environment "{}" --{} --execution_id "{}" --execution_mode "{}" --execution_user "{}" --execution_path "{}" --execution_threads "{}"{}'.format(meteor_path, environment, execution_method, execution_id, execution_mode, execution_user, execution_path, execution_threads, execution_limit)
        # print(command)

        # Execute Meteor
        p = subprocess.Popen(command, stdout=open('/dev/null', 'w'), shell=True)