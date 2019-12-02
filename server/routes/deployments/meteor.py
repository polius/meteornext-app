#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('apps/Meteor/app')

import os
import json
import uuid
import subprocess
from time import time
from datetime import datetime

import models.mysql
import models.admin.settings
import models.deployments.environments
import models.deployments.regions
import models.deployments.servers
import models.deployments.auxiliary
import models.deployments.slack

class Meteor:
    def __init__(self, sql):
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
        self._base_path = os.path.dirname(os.path.realpath(__file__)) if sys.argv[0].endswith('.py') else os.path.dirname(sys.executable)

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
                        key_path = "{}{}/keys/{}".format(self._logs['local']['path'], self._uuid, region['id'])
                        region_data = {
                            "region": region['name'],
                            "ssh": {
                                "enabled": "True" if region['cross_region'] == 1 else "False",
                                "hostname": "" if region['hostname'] is None else region['hostname'],
                                "username": "" if region['username'] is None else region['username'],
                                "password": "" if region['password'] is None else region['password'],
                                "key": "" if region['key'] is None else key_path,
                                "deploy_path": "" if region['deploy_path'] is None else region['deploy_path']
                            },
                            "sql": []
                        }

                        # Generate key files
                        if region['key'] is not None:
                            with open(key_path, 'w') as outfile:
                                outfile.write(region['key'])
                            os.chmod(key_path, 0o600)

                        for server in servers:
                            if server['environment_id'] == environment['id'] and server['region_id'] == region['id']:
                                region_data['sql'].append({
                                    "name": server['name'],
                                    "hostname": server['hostname'],
                                    "username": server['username'],
                                    "password": server['password']
                                })

                        # Add region data to the credentials
                        self._credentials['environments'][environment['name']].append(region_data)

        # Compile Auxiliary Connections
        self._credentials['auxiliary_connections'] = {}
        for aux in auxiliary:
            self._credentials['auxiliary_connections'][aux['name']] = {
                "hostname": aux['hostname'],
                "username": aux['username'],
                "password": aux['password']
            }
        
        # Compile Logs
        self._credentials['s3'] = {
            "enabled": "False",
            "aws_access_key_id": "",
            "aws_secret_access_key": "",
            "region_name": "",
            "bucket_name": ""
        }
        self._credentials['web'] = {
            "public_url": ""
        }

        if 'amazon_s3' in self._logs and self._logs['amazon_s3']['enabled']:
            self._credentials['s3'] = {
                "enabled": "True",
                "aws_access_key_id": self._logs['amazon_s3']['aws_access_key'],
                "aws_secret_access_key": self._logs['amazon_s3']['aws_secret_access_key'],
                "region_name": self._logs['amazon_s3']['region_name'],
                "bucket_name": self._logs['amazon_s3']['bucket_name']
            }

        # Compile Slack
        self._credentials['slack'] = {
            "enabled": "False",
            "webhook": ""
        }
        if len(slack) > 0:
            self._credentials['slack'] = {
                "enabled": "True" if slack[0]['enabled'] == 1 else 'False',
                "webhook": slack[0]['webhook']
            }        

        # Compile Execution Mode
        self._credentials['execution_mode'] = {
            "parallel": "True",
            "threads": deployment['execution_threads']
        }

        # Enable Meteor Next
        with open("{}/server.conf".format(self._base_path)) as outfile:
            next_credentials = json.load(outfile)['sql']

        self._credentials['meteor_next'] = {
            "enabled": "True",
            "hostname": next_credentials['hostname'],
            "username": next_credentials['username'],
            "password": next_credentials['password'],
            "port": next_credentials['port'],
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
        # elif deployment['mode'] == 'INBENTA':
        #     self.__compile_query_execution_inbenta(deployment)

        # Store Query Execution
        with open("{}/{}/query_execution.py".format(self._logs['local']['path'], self._uuid), 'w') as outfile:
            outfile.write(self._query_execution)

    def __compile_query_execution_basic(self, deployment):
        queries = {}
        for i, q in enumerate(json.loads(deployment['queries'])):
            queries[str(i+1)] = q['query']

        self._query_execution = """import fnmatch
class query_execution:
    def __init__(self, query_instance=None):
        self._meteor = query_instance
        self._queries = {}
        self._auxiliary_queries = {{}}
    def before(self, environment, region):
        pass
    def main(self, environment, region, server, database):
        if len(fnmatch.filter([database.decode('utf-8')], '{}')) > 0:
            for i in self._queries.keys():
                self._meteor.execute(query=self._queries[str(i)], database=database)
    def after(self, environment, region):
        pass
    @property
    def queries(self):
        return self._queries
    @property
    def auxiliary_queries(self):
        return self._auxiliary_queries
    def set_query(self, query_instance):
        self._meteor = query_instance""".format(json.dumps(queries), deployment['databases'])

    def __execute(self, deployment):
        # Build Meteor Parameters
        meteor_path = "{}/apps/meteor".format(os.path.dirname(os.path.realpath(__file__)))
        environment = deployment['environment']
        execution_method = 'validate all' if deployment['method'].lower() == 'validate' else deployment['method'].lower()
        logs_path = "{}/{}".format(self._logs['local']['path'], self._uuid)
        query_execution_path = "{}/{}/query_execution.py".format(self._logs['local']['path'], self._uuid)
        credentials_path = "{}/{}/credentials.json".format(self._logs['local']['path'], self._uuid)
        execution_plan_factor = '--execution_plan_factor "{}"'.format(deployment['epf']) if deployment['epf'] > 0 else ''

        # Build Meteor Command
        command = '{} --environment "{}" --{} --logs_path "{}" --query_execution_path "{}" --credentials_path "{}" --deployment_mode "{}" --deployment_id "{}" --uuid "{}" {}'.format(meteor_path, environment, execution_method, logs_path, query_execution_path, credentials_path, deployment['mode'].lower(), deployment['execution_id'], self._uuid, execution_plan_factor)
        print(command)

        # Execute Meteor
        p = subprocess.Popen(command, stdout=open('/dev/null', 'w'), shell=True)
        print(p.pid)